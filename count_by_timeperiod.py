import json
import sys
import csv
from collections import defaultdict
from datetime import datetime, timedelta

def get_time_key(dt, time_unit):
    if time_unit == "year":
        return dt.strftime("%Y")
    elif time_unit == "month":
        return dt.strftime("%Y/%m")
    elif time_unit == "week":
        week_start = dt - timedelta(days=dt.weekday())  # Start of the week (Monday)
        return f"{week_start.strftime('%Y/%m')}/W{week_start.strftime('%U')}"
    elif time_unit == "day":
        return dt.strftime("%Y/%m/%d")
    else:
        print("Invalid time unit. Use: year, month, week, or day.", file=sys.stderr)
        sys.exit(1)

def count_stats(time_unit, json_filename, filter_from_id=None, count_what="messages"):
    with open(json_filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    if count_what == "messages":
        time_counts = defaultdict(int)
        for message in data.get("messages", []):
            if filter_from_id and message.get("from_id") != filter_from_id:
                continue
            timestamp = message.get("date")
            if not timestamp:
                continue
            dt = datetime.fromisoformat(timestamp)
            time_key = get_time_key(dt, time_unit)
            time_counts[time_key] += 1
        writer = csv.writer(sys.stdout)
        writer.writerow(["time", "count"])
        for time_key, count in sorted(time_counts.items()):
            writer.writerow([time_key, count])
    elif count_what == "users":
        time_users = defaultdict(set)
        for message in data.get("messages", []):
            if filter_from_id and message.get("from_id") != filter_from_id:
                continue
            timestamp = message.get("date")
            if not timestamp:
                continue
            dt = datetime.fromisoformat(timestamp)
            time_key = get_time_key(dt, time_unit)
            from_id = message.get("from_id")
            if from_id:
                time_users[time_key].add(from_id)
        writer = csv.writer(sys.stdout)
        writer.writerow(["time", "active_users"])
        for time_key, users in sorted(time_users.items()):
            writer.writerow([time_key, len(users)])
    else:
        print("Invalid count type. Use: messages or users.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 4 or len(sys.argv) > 5:
        print("Usage: python3 count_by_timeperiod.py (messages|users) (year|month|week|day) <json_filename> [from_id]", file=sys.stderr)
        sys.exit(1)

    count_what = sys.argv[1].lower()
    time_unit = sys.argv[2].lower()
    json_filename = sys.argv[3]
    filter_from_id = sys.argv[4] if len(sys.argv) > 4 else None

    count_stats(time_unit, json_filename, filter_from_id, count_what)
