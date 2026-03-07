#!/usr/bin/env python3
"""
Poll Notion every 1 day and read all documents the integration has access to.
"""

import time
from datetime import datetime

from notion_connector import list_all_pages, read_page

POLL_INTERVAL_DAYS = 1
POLL_INTERVAL_SECONDS = POLL_INTERVAL_DAYS * 24 * 60 * 60


def poll_and_read():
    """List all pages, read each one, and yield (page_id, content)."""
    pages = list_all_pages()
    if not pages:
        print("No pages found. Share pages with your Notion integration.")
        return

    for page in pages:
        page_id = page.get("id", "")
        if not page_id:
            continue
        content = read_page(page_id)
        if content.startswith("Error:"):
            print(f"  Skip {page_id}: {content}")
            continue
        yield page_id, content


def run():
    """Poll Notion every 1 day, read all documents, print to terminal."""
    print(f"Polling Notion every {POLL_INTERVAL_DAYS} day(s). Ctrl+C to stop.\n")

    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{now}] Fetching all Notion pages...")

        count = 0
        for page_id, content in poll_and_read():
            count += 1
            preview = content[:200] + "..." if len(content) > 200 else content
            print(f"\n--- Page {page_id} ---\n{preview}\n")

        print(f"[{now}] Read {count} page(s). Next poll in {POLL_INTERVAL_DAYS} day(s).\n")
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\nStopped.")

"""
Main - Terminal display and message input.
Streams messages from all channels. To send: channel_id message or channel_id1,channel_id2 message
"""

import re
import threading
from datetime import datetime

from slack_connector import stream_messages, send_message

# Slack channel IDs start with C (public), G (private), D (DM)
CHANNEL_ID_PATTERN = re.compile(r"^[CGD][A-Z0-9]+$")


def parse_send_input(line: str) -> tuple[list[str], str] | None:
    """Parse 'channel_id message' or '#channel_id message' or 'channel_id1,channel_id2 message'. Returns (channel_ids, message) or None."""
    line = line.strip()
    if not line:
        return None
    parts = line.split(None, 1)  # split on first whitespace
    if len(parts) < 2:
        return None
    first, rest = parts
    first = first.lstrip("#")  # allow #C0ABC123
    if "," in first:
        ids = [x.strip().lstrip("#") for x in first.split(",") if x.strip()]
    else:
        ids = [first]
    if not all(CHANNEL_ID_PATTERN.match(cid) for cid in ids):
        return None
    return (ids, rest)


def run() -> None:
    """Run terminal UI: display streamed messages from all channels, send with channel_id message."""
    print("\n--- Streaming from all channels. To send: channel_id message (e.g. C0ABC123 Hello) ---\n", flush=True)

    def consume_stream():
        for channel_id, user_id, message, ts in stream_messages():
            time_str = datetime.fromtimestamp(float(ts)).strftime("%H:%M:%S") if ts else ""
            print(f"[{time_str}] #{channel_id} <{user_id}>: {message}\n> ", end="", flush=True)

    stream_thread = threading.Thread(target=consume_stream, daemon=True)
    stream_thread.start()

    print("> ", end="", flush=True)
    while True:
        try:
            line = input()
        except (EOFError, KeyboardInterrupt):
            break
        if not line.strip():
            print("> ", end="", flush=True)
            continue
        parsed = parse_send_input(line)
        if not parsed:
            print("  Format: channel_id message  or  channel_id1,channel_id2 message\n> ", end="", flush=True)
            continue
        channel_ids, message = parsed
        try:
            send_message(channel_ids, message)
            print(f"  [sent to {', '.join(channel_ids)}]\n> ", end="", flush=True)
        except Exception as e:
            print(f"  [failed: {e}]\n> ", end="", flush=True)


def main():
    try:
        run()
    except KeyboardInterrupt:
        print("\nBye.")


if __name__ == "__main__":
    main()
