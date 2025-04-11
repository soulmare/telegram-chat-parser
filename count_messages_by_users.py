import json
import sys
import csv
from collections import defaultdict
from datetime import datetime
import argparse

def count_messages(json_filename, begin=None, end=None, sort=False):
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

    sorted_items = sorted(
        message_counts.items(),
        key=lambda item: item[1]["count"],
        reverse=True
    ) if sort else message_counts.items()
    
    for from_id, details in sorted_items:
        writer.writerow([from_id, details["from"], details["count"], details["first_message_time"].isoformat()])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Count messages per user from a Telegram JSON export.")
    parser.add_argument("json_filename", help="Path to JSON file")
    parser.add_argument("--begin", type=str, help="Start of date range (ISO format, e.g., 2023-01-01)")
    parser.add_argument("--end", type=str, help="End of date range (ISO format, e.g., 2023-12-31)")
    parser.add_argument("--sort", action="store_true", help="Sort output by count in descending order")
    
    args = parser.parse_args()

    begin = datetime.fromisoformat(args.begin) if args.begin else None
    end = datetime.fromisoformat(args.end) if args.end else None

    count_messages(args.json_filename, begin, end, args.sort)
