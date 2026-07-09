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

def count_stats(time_unit, json_filename, filter_from_id=None):
    with open(json_filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    time_counts = defaultdict(int)
    time_users = defaultdict(set)
    for message in data.get("messages", []):
        if filter_from_id and message.get("from_id") != filter_from_id:
            continue
        timestamp = message.get("date")
        if not timestamp:
            continue
        dt = datetime.fromisoformat(timestamp)
        time_key = get_time_key(dt, time_unit)
        time_counts[time_key] += 1
        from_id = message.get("from_id")
        if from_id:
            time_users[time_key].add(from_id)

    writer = csv.writer(sys.stdout)
    writer.writerow(["time", "messages_count", "active_users"])
    for time_key in sorted(time_counts.keys()):
        writer.writerow([time_key, time_counts[time_key], len(time_users[time_key])])

if __name__ == "__main__":
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python3 count_by_timeperiod.py (year|month|week|day) <json_filename> [from_id]", file=sys.stderr)
        sys.exit(1)

    time_unit = sys.argv[1].lower()
    json_filename = sys.argv[2]
    filter_from_id = sys.argv[3] if len(sys.argv) > 3 else None

    count_stats(time_unit, json_filename, filter_from_id)
