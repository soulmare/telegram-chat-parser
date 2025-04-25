import csv
import argparse
import networkx as nx
import matplotlib.pyplot as plt
from datetime import datetime

# Define colors here for easy editing
EDGE_COLOR = "lightblue"
NODE_COLOR = "lightgreen"
TEXT_COLOR = "brown"

def parse_args():
    parser = argparse.ArgumentParser(description="Build and plot a user reply graph from Telegram CSV data.")
    parser.add_argument("csv_filename", help="Path to the CSV file generated from Telegram JSON")
    parser.add_argument("--output", required=True, help="Path to output image file")
    parser.add_argument("--show-edge-labels", action="store_true", help="Display edge labels with reply counts")
    parser.add_argument("--min-messages", type=int, default=0, help="Minimum number of messages for a user to be included in the plot")
    parser.add_argument("--from-date", type=str, help="Start date (inclusive) in YYYY-MM-DD format")
    parser.add_argument("--to-date", type=str, help="End date (inclusive) in YYYY-MM-DD format")
    return parser.parse_args()

def main():
    args = parse_args()

    from_date = datetime.strptime(args.from_date, "%Y-%m-%d") if args.from_date else None
    to_date = datetime.strptime(args.to_date, "%Y-%m-%d") if args.to_date else None

    reply_counts = {}  # (user_a, user_b) => count
    user_names = {}    # from_id => name
    user_message_counts = {}  # from_id => message count

    with open(args.csv_filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            msg_date_str = row.get("date")
            if not msg_date_str:
                continue

            try:
                msg_date = datetime.fromisoformat(msg_date_str)
            except ValueError:
                continue  # Skip rows with invalid date format

            if from_date and msg_date < from_date:
                continue
            if to_date and msg_date > to_date:
                continue

            from_id = row.get("from_id")
            from_name = row.get("from")
            reply_user_id = row.get("reply_user_id")

            if not from_id:
                continue

            # Count the messages for each user
            user_message_counts[from_id] = user_message_counts.get(from_id, 0) + 1

            if not reply_user_id or from_id == reply_user_id:
                continue  # Skip self-replies

            # Ensure that both the user and the replied user names are stored
            user_names[from_id] = from_name or from_id
            if reply_user_id not in user_names:
                reply_user_name = row.get("reply_user_name")
                if reply_user_name:
                    user_names[reply_user_id] = reply_user_name

            # Create the key for the reply
            key = tuple(sorted((from_id, reply_user_id)))
            reply_counts[key] = reply_counts.get(key, 0) + 1

    # Filter users based on the minimum message count
    filtered_users = {user: count for user, count in user_message_counts.items() if count >= args.min_messages}

    max_messages = max(user_message_counts.values(), default=1)

    G = nx.Graph()
    for (u1, u2), count in reply_counts.items():
        if u1 not in filtered_users or u2 not in filtered_users:
            continue

        distance = 1 / count
        name1 = user_names.get(u1, u1)
        name2 = user_names.get(u2, u2)
        G.add_edge(name1, name2, weight=count, distance=distance)

    node_sizes = []
    for user in G.nodes():
        user_id = next((uid for uid, name in user_names.items() if name == user), None)
        if user_id in filtered_users:
            node_size = user_message_counts.get(user_id, 0) / max_messages * 3000
        else:
            node_size = 0
        node_sizes.append(node_size)

    pos = nx.spring_layout(G, weight='distance', seed=42)

    plt.figure(figsize=(10, 8))
    nx.draw(G, pos, with_labels=True, node_size=node_sizes, node_color=NODE_COLOR, edge_color=EDGE_COLOR,
            width=2, font_size=9, font_weight='bold', font_color=TEXT_COLOR)

    if args.show_edge_labels:
        nx.draw_networkx_edge_labels(G, pos,
            edge_labels={(u, v): G[u][v]['weight'] for u, v in G.edges()},
            font_size=8, font_color=TEXT_COLOR)

    plt.title("Telegram User Reply Graph")
    plt.margins(0.2)
    plt.savefig(args.output)
    print(f"Graph saved to {args.output}")

if __name__ == "__main__":
    main()
