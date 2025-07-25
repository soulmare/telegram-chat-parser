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
    parser.add_argument("csv_filename", help="Path to the CSV file generated from Telegram JSON")
    parser.add_argument("--show-edge-labels", action="store_true", help="Display edge labels with reply counts")
    parser.add_argument("--min-messages", type=int, default=0, help="Minimum number of messages for a user to be included in the plot")
    parser.add_argument("--from-date", type=str, help="Start date (inclusive) in YYYY-MM-DD format")
    parser.add_argument("--to-date", type=str, help="End date (inclusive) in YYYY-MM-DD format")
    parser.add_argument("--min-replies", type=int, default=0, help="Minimum number of replies between users to be included in the graph")
    parser.add_argument("--seed", type=int, help="Seed for graph layout. If omitted, a random seed is used")
    parser.add_argument(
        "--nickname-file",
        help="Path to file with nickname overrides. Each line should be: user_id nickname (nickname can contain spaces)"
    )
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

    from_date = datetime.strptime(args.from_date, "%Y-%m-%d") if args.from_date else None
    to_date = datetime.strptime(args.to_date, "%Y-%m-%d") if args.to_date else None

    nickname_overrides = {}
    if args.nickname_file:
        try:
            with open(args.nickname_file, encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    stripped = line.strip()
                    if not stripped:
                        continue
                    parts = stripped.split()
                    if len(parts) < 2:
                        print(f"Warning: Line {line_num} in nickname file is invalid: {stripped}")
                        continue
                    user_id = parts[0]
                    nickname = " ".join(parts[1:]).replace("\\n", "\n")
                    nickname_overrides[user_id] = nickname
        except Exception as e:
            print(f"Error reading nickname file: {e}")
            return

    reply_counts = {}
    user_names = {}
    user_message_counts = {}

    raw_names = {}

    with open(args.csv_filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            msg_date_str = row.get("date")
            if not msg_date_str:
                continue
            try:
                msg_date = datetime.fromisoformat(msg_date_str)
            except ValueError:
                continue
            if from_date and msg_date < from_date:
                continue
            if to_date and msg_date > to_date:
                continue

            from_id = row.get("from_id")
            from_name = row.get("from")
            reply_user_id = row.get("reply_user_id")

            if not from_id:
                continue
            user_message_counts[from_id] = user_message_counts.get(from_id, 0) + 1

            if from_id not in user_names and from_id not in nickname_overrides:
                raw_name = from_name or from_id
                clean_name = sanitize_text(raw_name, from_id)
                user_names[from_id] = wrap_nickname(clean_name, MAX_LINE_LENGTH)

            if reply_user_id and reply_user_id != from_id:
                if reply_user_id not in user_names and reply_user_id not in nickname_overrides:
                    reply_user_name = row.get("reply_user_name")
                    if reply_user_name:
                        clean_reply = sanitize_text(reply_user_name, reply_user_id)
                        user_names[reply_user_id] = wrap_nickname(clean_reply, MAX_LINE_LENGTH)

                key = tuple(sorted((from_id, reply_user_id)))
                reply_counts[key] = reply_counts.get(key, 0) + 1

    user_names.update(nickname_overrides)

    filtered_users = {user: count for user, count in user_message_counts.items() if count >= args.min_messages}
    max_messages = max(user_message_counts.values(), default=1)
    max_replies = max(reply_counts.values(), default=1)

    G = nx.Graph()
    for (u1, u2), count in reply_counts.items():
        if count < args.min_replies or u1 not in filtered_users or u2 not in filtered_users:
            continue
        name1 = user_names.get(u1, u1)
        name2 = user_names.get(u2, u2)
        G.add_edge(name1, name2, weight=count)

    node_sizes = []
    for user in G.nodes():
        user_id = next((uid for uid, name in user_names.items() if name == user), None)
        node_size = user_message_counts.get(user_id, 0) / max_messages * 3000 if user_id in filtered_users else 0
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
    pos = nx.spring_layout(G, seed=seed, k=5)

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
