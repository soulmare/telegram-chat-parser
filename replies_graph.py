import csv
import argparse
import networkx as nx
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib.colors as mcolors
import matplotlib.cm as cmx
import random
import os

NODE_COLOR = "lightgreen"
TEXT_COLOR = "#444444"
MAX_LINE_LENGTH = 10

def parse_args():
    parser = argparse.ArgumentParser(description="Build and plot a user reply graph from Telegram CSV data.")
    parser.add_argument("csv_filename", help="Path to the CSV file (grouped edges, flexible columns)")
    parser.add_argument("--from-id-field", required=True, help="CSV column for first user id")
    parser.add_argument("--from-name-field", required=True, help="CSV column for first user name")
    parser.add_argument("--reply-id-field", required=True, help="CSV column for second user id")
    parser.add_argument("--reply-name-field", required=True, help="CSV column for second user name")
    parser.add_argument("--weight-field", required=True, help="CSV column for edge weight (messages count)")
    parser.add_argument("--show-edge-labels", action="store_true", help="Display edge labels with reply counts")
    parser.add_argument("--seed", type=int, help="Seed for graph layout. If omitted, a random seed is used")
    return parser.parse_args()

def sanitize_text(nickname: str, user_id: str) -> str:
    def is_safe(c):
        code = ord(c)
        return (
            c == '\n' or
            0x0020 <= code <= 0x007E or
            0x00A0 <= code <= 0x024F or
            0x0400 <= code <= 0x04FF
        )

    sanitized = ''.join(c for c in nickname if is_safe(c))

    if len(sanitized.strip()) < 3:
        print(f"⚠️  Warning: Nickname for user {user_id} sanitized to fewer than 3 characters: '{sanitized}'")
        print(f"   ➤ Consider using --nickname-file with a line like:")
        print(f"     {user_id} {nickname.strip()}\n")

    return sanitized

def wrap_nickname(nickname: str, max_len: int) -> str:
    words = nickname.split()
    if not words:
        return nickname

    lines = []
    current_line = words[0]
    for word in words[1:]:
        if len(current_line) + 1 + len(word) > max_len:
            lines.append(current_line)
            current_line = word
        else:
            current_line += ' ' + word
    lines.append(current_line)
    return "\n".join(lines)

def main():
    args = parse_args()


    # Mapping fields from arguments
    from_id_field = args.from_id_field
    from_name_field = args.from_name_field
    reply_id_field = args.reply_id_field
    reply_name_field = args.reply_name_field
    weight_field = args.weight_field

    edge_map = {}  # key: tuple(sorted([id1, id2])) -> weight
    user_names = {}
    user_message_counts = {}

    with open(args.csv_filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            id1 = row.get(from_id_field)
            name1 = row.get(from_name_field) or id1
            id2 = row.get(reply_id_field)
            name2 = row.get(reply_name_field) or id2
            try:
                weight = int(row.get(weight_field, 1))
            except Exception:
                weight = 1

            if not id1 or not id2 or id1 == id2:
                continue

            # Sanitize and store names
            if id1 not in user_names:
                clean_name1 = sanitize_text(name1, id1)
                user_names[id1] = wrap_nickname(clean_name1, MAX_LINE_LENGTH)
            if id2 not in user_names:
                clean_name2 = sanitize_text(name2, id2)
                user_names[id2] = wrap_nickname(clean_name2, MAX_LINE_LENGTH)

            # Count messages for node sizing
            user_message_counts[id1] = user_message_counts.get(id1, 0) + weight
            user_message_counts[id2] = user_message_counts.get(id2, 0) + weight

            # Bidirectional edge: use sorted tuple as key
            key = tuple(sorted([id1, id2]))
            edge_map[key] = edge_map.get(key, 0) + weight

    # Build graph
    G = nx.Graph()
    for (id1, id2), weight in edge_map.items():
        name1 = user_names.get(id1, id1)
        name2 = user_names.get(id2, id2)
        G.add_edge(name1, name2, weight=weight)

    # Node sizes by total messages
    max_messages = max(user_message_counts.values(), default=1)
    node_sizes = []
    for user in G.nodes():
        user_id = next((uid for uid, name in user_names.items() if name == user), None)
        node_size = user_message_counts.get(user_id, 0) / max_messages * 2000 if user_id else 0
        node_sizes.append(node_size)

    edge_weights = [G[u][v]['weight'] for u, v in G.edges()]
    max_weight = max(edge_weights, default=1)
    widths = [weight / max_weight * 5 for weight in edge_weights]

    cmap = plt.get_cmap('Blues')
    norm = mcolors.Normalize(vmin=0, vmax=max_weight)
    sm = cmx.ScalarMappable(norm=norm, cmap=cmap)
    edge_colors = [sm.to_rgba(weight) for weight in edge_weights]

    seed = args.seed if args.seed is not None else random.randint(0, 99999)
    print(f"Using layout seed: {seed}")
    pos = nx.spring_layout(G, seed=seed, k=7)

    csv_dir = os.path.dirname(args.csv_filename)
    base_name = os.path.splitext(os.path.basename(args.csv_filename))[0]
    output_filename = os.path.join(csv_dir, f"{base_name}_seed{seed}.png")

    plt.figure(figsize=(10, 8))
    nx.draw(G, pos, with_labels=True, node_size=node_sizes, node_color=NODE_COLOR,
            edge_color=edge_colors, width=widths,
            font_size=9, font_weight='bold', font_color=TEXT_COLOR, alpha=0.8)

    if args.show_edge_labels:
        nx.draw_networkx_edge_labels(G, pos,
            edge_labels={(u, v): G[u][v]['weight'] for u, v in G.edges()},
            font_size=8, font_color=TEXT_COLOR)

    plt.title("Telegram User Reply Graph")
    plt.margins(0.2)
    plt.savefig(output_filename)
    print(f"Graph saved to {output_filename}")

if __name__ == "__main__":
    main()
