import json
import sys
import csv
from collections import defaultdict
from datetime import datetime, timedelta

HELP_TEXT = """
Count messages and active users by time period from a Telegram export JSON file.

Usage:
  python3 count_by_timeperiod.py <period> <json_filename> [from_id]

Arguments:
  period         Aggregation period:
                   year   - group by year
                   month  - group by month
                   week   - group by week (starting Monday)
                   day    - group by day

  json_filename  Telegram export JSON file.

  from_id        Optional sender ID filter. If specified, only messages
                 from this sender are counted.

Output:
  CSV written to stdout with columns:

    time,messages_count,active_users

  where:
    time            Aggregation key.
    messages_count  Number of messages in the period.
    active_users    Number of unique senders in the period.

Examples:
  Count messages per month:
    python3 count_by_timeperiod.py month result.json

  Count messages per week for a specific user:
    python3 count_by_timeperiod.py week result.json user123456

Example output:
  time,messages_count,active_users
  2025/01,1532,24
  2025/02,1418,21
  2025/03,1764,27

The CSV can be redirected to a file:
  python3 count_by_timeperiod.py month result.json > stats.csv
"""

def get_time_key(dt, time_unit):
    if time_unit == "year":
        return dt.strftime("%Y")
    elif time_unit == "month":
        return dt.strftime("%Y/%m")
    elif time_unit == "week":
        week_start = dt - timedelta(days=dt.weekday())  # Start of week (Monday)
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

    messages = []

    for message in data.get("messages", []):
        if filter_from_id and message.get("from_id") != filter_from_id:
            continue

        timestamp = message.get("date")
        if not timestamp:
            continue

        dt = datetime.fromisoformat(timestamp)
        messages.append((dt, message))

        time_key = get_time_key(dt, time_unit)
        time_counts[time_key] += 1

        from_id = message.get("from_id")
        if from_id:
            time_users[time_key].add(from_id)

    messages.sort(key=lambda x: x[0])

    total_users_by_period = {}
    seen_users = set()

    for dt, message in messages:
        from_id = message.get("from_id")
        if from_id:
            seen_users.add(from_id)

        time_key = get_time_key(dt, time_unit)
        total_users_by_period[time_key] = len(seen_users)

    writer = csv.writer(sys.stdout)
    writer.writerow([
        "time",
        "messages_count",
        "active_users",
        "total_users"
    ])

    for time_key in sorted(time_counts.keys()):
        writer.writerow([
            time_key,
            time_counts[time_key],
            len(time_users[time_key]),
            total_users_by_period.get(time_key, 0)
        ])

if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help"):
        print(HELP_TEXT.strip())
        sys.exit(0)

    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Use --help for usage information.", file=sys.stderr)
        sys.exit(1)

    time_unit = sys.argv[1].lower()
    json_filename = sys.argv[2]
    filter_from_id = sys.argv[3] if len(sys.argv) > 3 else None

    count_stats(time_unit, json_filename, filter_from_id)
