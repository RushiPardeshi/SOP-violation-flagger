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
