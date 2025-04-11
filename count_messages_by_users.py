import json
import sys
import csv
from collections import defaultdict
from datetime import datetime
import argparse

def count_messages(json_filename, begin=None, end=None):
    with open(json_filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    message_counts = defaultdict(lambda: {"from": "", "count": 0, "first_message_time": None})
    
    for message in data.get("messages", []):
        from_id = message.get("from_id")
        from_name = message.get("from")
        timestamp = message.get("date")
        
        if from_id and from_name and timestamp:
            dt = datetime.fromisoformat(timestamp)

            # Filter by date range
            if (begin and dt < begin) or (end and dt > end):
                continue
            
            message_counts[from_id]["from"] = from_name
            message_counts[from_id]["count"] += 1
            
            if message_counts[from_id]["first_message_time"] is None or dt < message_counts[from_id]["first_message_time"]:
                message_counts[from_id]["first_message_time"] = dt
    
    writer = csv.writer(sys.stdout)
    writer.writerow(["from_id", "from", "count", "first_message_time"])
    
    for from_id, details in message_counts.items():
        writer.writerow([from_id, details["from"], details["count"], details["first_message_time"].isoformat()])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Count messages per user from a Telegram JSON export.")
    parser.add_argument("json_filename", help="Path to JSON file")
    parser.add_argument("--begin", type=str, help="Start of date range (ISO format, e.g., 2023-01-01)")
    parser.add_argument("--end", type=str, help="End of date range (ISO format, e.g., 2023-12-31)")
    
    args = parser.parse_args()

    begin = datetime.fromisoformat(args.begin) if args.begin else None
    end = datetime.fromisoformat(args.end) if args.end else None

    count_messages(args.json_filename, begin, end)
