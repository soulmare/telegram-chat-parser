import json
import sys
import csv
from collections import defaultdict
from datetime import datetime

def count_messages(json_filename):
    with open(json_filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    message_counts = defaultdict(lambda: {"from": "", "count": 0, "first_message_time": None})
    
    for message in data.get("messages", []):
        from_id = message.get("from_id")
        from_name = message.get("from")
        timestamp = message.get("date")
        
        if from_id and from_name and timestamp:
            dt = datetime.fromisoformat(timestamp)
            
            message_counts[from_id]["from"] = from_name
            message_counts[from_id]["count"] += 1
            
            if message_counts[from_id]["first_message_time"] is None or dt < message_counts[from_id]["first_message_time"]:
                message_counts[from_id]["first_message_time"] = dt
    
    writer = csv.writer(sys.stdout)
    writer.writerow(["from_id", "from", "count", "first_message_time"])
    
    for from_id, details in message_counts.items():
        writer.writerow([from_id, details["from"], details["count"], details["first_message_time"].isoformat()])

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <json_filename>", file=sys.stderr)
        sys.exit(1)
    
    json_filename = sys.argv[1]
    count_messages(json_filename)
