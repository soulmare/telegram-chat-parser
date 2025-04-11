import json
import csv
import argparse
import sys
from collections import defaultdict, Counter
from datetime import datetime, timedelta

def parse_args():
    parser = argparse.ArgumentParser(description="Group user messages by time periods.")
    parser.add_argument("json_filename", help="Path to the JSON file")
    parser.add_argument("--period", choices=["year", "month", "week", "day"], required=True, help="Time grouping unit")
    parser.add_argument("--begin", help="Start date in YYYY-MM-DD")
    parser.add_argument("--end", help="End date in YYYY-MM-DD")
    parser.add_argument("--min", type=int, default=0, help="Minimum total messages per user to include")
    parser.add_argument("--include-others", action="store_true", help="Include messages from users below the threshold under 'OtherUsers'")
    return parser.parse_args()

def get_time_key(dt, period):
    if period == "year":
        return dt.strftime("%Y")
    elif period == "month":
        return dt.strftime("%Y %B")
    elif period == "week":
        monday = dt - timedelta(days=dt.weekday())
        return monday.strftime("%Y W%U")
    elif period == "day":
        return dt.strftime("%Y-%m-%d")

def main():
    args = parse_args()

    with open(args.json_filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    begin_date = datetime.min
    end_date = datetime.max

    if args.begin:
        begin_date = datetime.strptime(args.begin, "%Y-%m-%d")
    if args.end:
        end_date = datetime.strptime(args.end, "%Y-%m-%d")

    user_time_counts = defaultdict(lambda: defaultdict(int))
    total_user_counts = Counter()

    for msg in data.get("messages", []):
        if msg.get("type") != "message":
            continue

        date_str = msg.get("date")
        if not date_str or not msg.get("from"):
            continue

        try:
            dt = datetime.fromisoformat(date_str)
        except ValueError:
            continue

        if dt < begin_date or dt > end_date:
            continue

        user = msg["from"]
        time_key = get_time_key(dt, args.period)

        user_time_counts[time_key][user] += 1
        total_user_counts[user] += 1

    # Filter and sort users
    included_users = [user for user, count in total_user_counts.items() if count >= args.min]
    included_users.sort(key=lambda u: total_user_counts[u], reverse=True)

    time_keys = sorted(user_time_counts.keys())

    writer = csv.writer(sys.stdout)
    header = ["Period"] + included_users
    if args.include_others:
        header.append("OtherUsers")
    writer.writerow(header)

    for time_key in time_keys:
        row = [time_key]
        counts = user_time_counts[time_key]
        other_count = 0
        for user in included_users:
            row.append(counts.get(user, 0))
        if args.include_others:
            for user, count in counts.items():
                if user not in included_users:
                    other_count += count
            row.append(other_count)
        writer.writerow(row)

if __name__ == "__main__":
    main()
