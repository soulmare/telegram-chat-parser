import json
import csv
import argparse
import sys


def parse_args():
    parser = argparse.ArgumentParser(description="Convert Telegram messages JSON to CSV with selected fields.")
    parser.add_argument("json_filename", help="Path to the JSON file")
    return parser.parse_args()


def main():
    args = parse_args()

    with open(args.json_filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    messages = data.get("messages", [])

    # Build a map of message_id to from_id
    id_to_user = {}
    for msg in messages:
        if msg.get("type") == "message" and "id" in msg and "from_id" in msg:
            id_to_user[msg["id"]] = msg["from_id"]

    writer = csv.DictWriter(sys.stdout, fieldnames=[
        "id", "reply_to_id", "reply_user_id", "date", "edited_date",
        "from", "from_id", "text_length", "text_entities_count",
        "media_type", "reactions_count"
    ])
    writer.writeheader()

    for msg in messages:
        if msg.get("type") != "message":
            continue

        text = msg.get("text", "")
        if isinstance(text, list):
            text = "".join(part if isinstance(part, str) else part.get("text", "") for part in text)

        reply_to_id = msg.get("reply_to_message_id")
        reply_user_id = id_to_user.get(reply_to_id) if reply_to_id else None

        writer.writerow({
            "id": msg.get("id"),
            "reply_to_id": reply_to_id,
            "reply_user_id": reply_user_id,
            "date": msg.get("date"),
            "edited_date": msg.get("edited"),
            "from": msg.get("from"),
            "from_id": msg.get("from_id"),
            "text_length": len(text),
            "text_entities_count": len(msg.get("text_entities", [])),
            "media_type": msg.get("media_type"),
            "reactions_count": len(msg.get("reactions", [])),
        })


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.stderr.close()
        sys.exit(0)
