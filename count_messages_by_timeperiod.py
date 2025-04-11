import json
import sys
import csv
from collections import defaultdict
from datetime import datetime, timedelta

def count_messages_by_time(time_unit, json_filename, filter_from_id=None):
    with open(json_filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    time_counts = defaultdict(int)
    
    for message in data.get("messages", []):
        if filter_from_id and message.get("from_id") != filter_from_id:
            continue
        
        timestamp = message.get("date")
        if not timestamp:
            continue
        
        dt = datetime.fromisoformat(timestamp)
        
        if time_unit == "year":
            time_key = dt.strftime("%Y")
        elif time_unit == "month":
            time_key = dt.strftime("%Y/%m")
        elif time_unit == "week":
            week_start = dt - timedelta(days=dt.weekday())  # Start of the week (Monday)
            time_key = f"{week_start.strftime('%Y/%m')}/W{week_start.strftime('%U')}"
        elif time_unit == "day":
            time_key = dt.strftime("%Y/%m/%d")
        else:
            print("Invalid time unit. Use: year, month, week, or day.", file=sys.stderr)
            sys.exit(1)
        
        time_counts[time_key] += 1
    
    writer = csv.writer(sys.stdout)
    writer.writerow(["time", "count"])
    
    for time_key, count in sorted(time_counts.items()):
        writer.writerow([time_key, count])

if __name__ == "__main__":
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python3 count_messages_by_timeperiod.py (year|month|week|day) <json_filename> [from_id]", file=sys.stderr)
        sys.exit(1)
    
    time_unit = sys.argv[1].lower()
    json_filename = sys.argv[2]
    filter_from_id = sys.argv[3] if len(sys.argv) > 3 else None
    
    count_messages_by_time(time_unit, json_filename, filter_from_id)
