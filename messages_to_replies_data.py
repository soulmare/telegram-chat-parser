import json
import csv
import argparse
import sys
from datetime import datetime
from collections import defaultdict, Counter


def parse_args():
    parser = argparse.ArgumentParser(description="Aggregate Telegram replies between users into CSV statistics.")
    parser.add_argument("json_filename", help="Path to the Telegram JSON export file")
    parser.add_argument("--from-date", type=str, help="Start date (inclusive) in YYYY-MM-DD format")
    parser.add_argument("--to-date", type=str, help="End date (inclusive) in YYYY-MM-DD format")
    parser.add_argument("--max-nodes", type=int, default=0, help="Maximum number of top users (by message count) to include in the result")
    parser.add_argument("--min-replies", type=int, default=1, help="Minimum number of replies required to include a line in the result")
    parser.add_argument("--nickname-file", help="Path to file with nickname overrides. Each line should be: user_id nickname (nickname can contain spaces)")
    parser.add_argument("--mirror", action="store_true", help="Output each line twice, exchanging users order")
    parser.add_argument("--min-count-perc", type=float, default=0, help="Minimum percentage (0-100) of messages_count to user1 or user2 total messages to include row. If 0, disables this filter.")
    return parser.parse_args()


def load_nicknames(file_path):
    nicknames = {}
    if not file_path:
        return nicknames
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(maxsplit=1)
            if len(parts) == 2:
                uid, name = parts
                nicknames[uid] = name
    return nicknames


def main():
    args = parse_args()

    from_date = datetime.fromisoformat(args.from_date) if args.from_date else None
    to_date = datetime.fromisoformat(args.to_date) if args.to_date else None
    nicknames = load_nicknames(args.nickname_file)

    with open(args.json_filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    messages = data.get("messages", [])

    # Per-user stats (messages inside date range only)
    user_stats = defaultdict(lambda: {"count": 0, "length": 0, "name": None, "replies_count": 0})

    # Reply stats between pairs
    pairs = defaultdict(lambda: {
        "messages_count": 0,
        "messages_total_length": 0,
        "first_message_datetime": None,
        "last_message_datetime": None,
    })

    # Map message_id -> from_id
    id_to_user = {}
    id_to_name = {}
    user_order = []

    # ---- FIRST PASS (USER STATS WITH DATE FILTER) ----
    for msg in messages:
        if msg.get("type") != "message" or "from_id" not in msg:
            continue

        msg_time = datetime.fromisoformat(msg["date"].replace("Z", "+00:00"))
        if from_date and msg_time < from_date:
            continue
        if to_date and msg_time > to_date:
            continue

        uid = str(msg["from_id"])
        if uid not in user_order:
            user_order.append(uid)

        name = msg.get("from")
        if uid in nicknames:
            name = nicknames[uid]

        id_to_user[msg["id"]] = uid
        id_to_name[msg["id"]] = name

        # Parse text
        text = msg.get("text", "")
        if isinstance(text, list):
            text = "".join(part if isinstance(part, str) else part.get("text", "") for part in text)
        text_len = len(text)

        # Count per user inside date range
        user_stats[uid]["count"] += 1
        user_stats[uid]["length"] += text_len
        user_stats[uid]["name"] = name

    # Filter top users by message count
    if args.max_nodes > 0:
        top_users = set(uid for uid, _ in Counter({k: v["count"] for k, v in user_stats.items()}).most_common(args.max_nodes))
    else:
        top_users = set(user_stats.keys())

    # ---- SECOND PASS (PAIR REPLY STATS WITH DATE FILTER) ----
    for msg in messages:
        if msg.get("type") != "message" or "from_id" not in msg:
            continue

        msg_time = datetime.fromisoformat(msg["date"].replace("Z", "+00:00"))
        if from_date and msg_time < from_date:
            continue
        if to_date and msg_time > to_date:
            continue

        reply_to_id = msg.get("reply_to_message_id")
        if not reply_to_id or reply_to_id not in id_to_user:
            continue

        uid_a = str(msg["from_id"])
        uid_b = str(id_to_user[reply_to_id])
        if uid_a == uid_b:
            continue
        if uid_a not in top_users or uid_b not in top_users:
            continue

        # Order by appearance
        if user_order.index(uid_a) < user_order.index(uid_b):
            user1, user2 = uid_a, uid_b
        else:
            user1, user2 = uid_b, uid_a


        pair = pairs[(user1, user2)]
        pair["messages_count"] += 1

        # Count replies only for the user who sent the reply
        user_stats[uid_a]["replies_count"] += 1

        text = msg.get("text", "")
        if isinstance(text, list):
            text = "".join(part if isinstance(part, str) else part.get("text", "") for part in text)

        pair["messages_total_length"] += len(text)
        if pair["first_message_datetime"] is None or msg_time < pair["first_message_datetime"]:
            pair["first_message_datetime"] = msg_time
        if pair["last_message_datetime"] is None or msg_time > pair["last_message_datetime"]:
            pair["last_message_datetime"] = msg_time

    # ---- OUTPUT ----

    # Prepare to collect filtered nodes
    filtered_nodes = set()

    writer = csv.DictWriter(sys.stdout, fieldnames=[
        "user1_id", "user1_name", "user1_messages_count", "user1_replies_count", "user1_messages_total_length", "user1_messages_count_perc",
        "user2_id", "user2_name", "user2_messages_count", "user2_replies_count", "user2_messages_total_length", "user2_messages_count_perc",
        "messages_count", "messages_total_length",
        "messages_count_perc",
        "first_message_datetime", "last_message_datetime",
    ])
    writer.writeheader()

    filtered_edges = 0
    for (user1, user2), stats in pairs.items():
        if stats["messages_count"] < args.min_replies:
            continue

        user1_total = user_stats[user1]["count"]
        user2_total = user_stats[user2]["count"]
        user1_replies = user_stats[user1]["replies_count"]
        user2_replies = user_stats[user2]["replies_count"]
        # Avoid division by zero for replies
        user1_perc = (stats["messages_count"] / user1_replies * 100) if user1_replies > 0 else 0
        user2_perc = (stats["messages_count"] / user2_replies * 100) if user2_replies > 0 else 0
        messages_count_perc = max(user1_perc, user2_perc)

        # Filtering by min-count-perc (now using messages_count_perc)
        if args.min_count_perc > 0:
            if messages_count_perc <= args.min_count_perc:
                continue

        row = {
            "user1_id": user1,
            "user1_name": user_stats[user1]["name"],
            "user1_messages_count": user1_total,
            "user1_replies_count": user1_replies,
            "user1_messages_total_length": user_stats[user1]["length"],
            "user1_messages_count_perc": f"{user1_perc:.2f}",
            "user2_id": user2,
            "user2_name": user_stats[user2]["name"],
            "user2_messages_count": user2_total,
            "user2_replies_count": user2_replies,
            "user2_messages_total_length": user_stats[user2]["length"],
            "user2_messages_count_perc": f"{user2_perc:.2f}",
            "messages_count": stats["messages_count"],
            "messages_total_length": stats["messages_total_length"],
            "messages_count_perc": f"{messages_count_perc:.2f}",
            "first_message_datetime": stats["first_message_datetime"].strftime("%Y-%m-%d %H:%M:%S") if stats["first_message_datetime"] else "",
            "last_message_datetime": stats["last_message_datetime"].strftime("%Y-%m-%d %H:%M:%S") if stats["last_message_datetime"] else "",
        }

        writer.writerow(row)
        filtered_edges += 1
        filtered_nodes.add(user1)
        filtered_nodes.add(user2)

        if args.mirror:
            swapped = row.copy()
            swapped.update({
                "user1_id": row["user2_id"],
                "user1_name": row["user2_name"],
                "user1_messages_count": row["user2_messages_count"],
                "user1_replies_count": row["user2_replies_count"],
                "user1_messages_total_length": row["user2_messages_total_length"],
                "user1_messages_count_perc": row["user2_messages_count_perc"],
                "user2_id": row["user1_id"],
                "user2_name": row["user1_name"],
                "user2_messages_count": row["user1_messages_count"],
                "user2_replies_count": row["user1_replies_count"],
                "user2_messages_total_length": row["user1_messages_total_length"],
                "user2_messages_count_perc": row["user1_messages_count_perc"],
                # messages_count_perc is still the max of the two, so remains the same
            })
            writer.writerow(swapped)
            filtered_edges += 1
            filtered_nodes.add(row["user2_id"])
            filtered_nodes.add(row["user1_id"])

    print(f"Nodes count: {len(filtered_nodes)}", file=sys.stderr)
    print(f"Edges count: {filtered_edges}", file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.stderr.close()
        sys.exit(0)
