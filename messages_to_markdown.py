import json
import argparse
import sys
from datetime import datetime

def parse_iso_date(date_str):
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        print(f"Invalid date format: '{date_str}'. Use YYYY-MM-DD.", file=sys.stderr)
        sys.exit(1)

def extract_markdown_messages(json_data, ignore_users, include_users, begin_date, end_date, include_uids):
    messages = json_data.get("messages", [])
    markdown_lines = []
    id_to_user = {}

    # First pass: build message ID to sender name map
    for msg in messages:
        if msg.get("type") == "message":
            msg_id = msg.get("id")
            sender = msg.get("from", "Unknown")
            if msg_id is not None:
                id_to_user[msg_id] = sender

    # Second pass: build markdown
    for message in messages:
        if message.get("type") != "message":
            continue

        sender = message.get("from", "Unknown")
        sender_id = str(message.get("from_id", ""))

        # Apply whitelist filter (if defined)
        if include_users:
            if sender not in include_users and sender_id not in include_users:
                continue

        # Apply ignore filter (ignored only if not whitelisted)
        if sender in ignore_users or sender_id in ignore_users:
            continue

        date_raw = message.get("date", None)
        if not date_raw:
            continue

        try:
            msg_dt = datetime.fromisoformat(date_raw)
        except ValueError:
            continue

        if begin_date and msg_dt < begin_date:
            continue
        if end_date and msg_dt > end_date:
            continue

        date_str = date_raw.replace("T", " ")

        # Reply metadata
        reply_info = ""
        reply_to_id = message.get("reply_to_message_id")
        if reply_to_id is not None:
            original_sender = id_to_user.get(reply_to_id, "Unknown")
            reply_info = f"reply to **{original_sender}**, "

        # Sender formatting
        if include_uids:
            sender_formatted = f"{sender} ({sender_id})"
        else:
            sender_formatted = sender

        # Message text
        if message.get("media_type") == "sticker" and message.get("mime_type") == "application/x-tgsticker":
            text = "<STICKER>"
        else:
            text_content = message.get("text")
            if isinstance(text_content, str):
                text = text_content
            elif isinstance(text_content, list):
                text = ''.join(part if isinstance(part, str) else part.get("text", "") for part in text_content)
            else:
                text = ""

        text = text.replace('\n', ' ').strip()
        markdown_lines.append(f"- **{sender_formatted}** ({reply_info}{date_str}): {text}")

    return markdown_lines

def main():
    parser = argparse.ArgumentParser(description="Convert Telegram chat JSON export to Markdown list.")
    parser.add_argument("-i", "--input", required=True, help="Path to Telegram JSON export file.")
    parser.add_argument("-n", "--ignore-user", action="append", default=[], help="Username or user ID to ignore (can be repeated).")
    parser.add_argument("--include-user", action="append", default=[], help="Username or user ID to include (whitelist mode).")
    parser.add_argument("--begin", type=str, help="Start of date range (ISO format, e.g., 2023-01-01)")
    parser.add_argument("--end", type=str, help="End of date range (ISO format, e.g., 2023-12-31)")
    parser.add_argument("--include-uids", action="store_true", help="Include user IDs in output.")
    args = parser.parse_args()

    begin_date = parse_iso_date(args.begin) if args.begin else None
    end_date = parse_iso_date(args.end) if args.end else None

    try:
        with open(args.input, 'r', encoding='utf-8') as file:
            chat_data = json.load(file)
    except Exception as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        sys.exit(1)

    ignore_set = set(args.ignore_user)
    include_set = set(args.include_user)

    markdown_messages = extract_markdown_messages(
        chat_data,
        ignore_set,
        include_set,
        begin_date,
        end_date,
        args.include_uids
    )

    for line in markdown_messages:
        print(line)

if __name__ == "__main__":
    main()
