# SOP-violation-flagger

## Notion polling

Polls Notion every 1 day and reads all documents the integration has access to.

```bash
pip install -r requirements.txt
# Set NOTION_API_KEY in .env
python main.py
```

**Setup:** Create an integration at [notion.so/my-integrations](https://www.notion.so/my-integrations), enable "Read content", and share your pages with the integration.
Slack connector for streaming messages and sending replies.

## Quick start

```bash
pip install -r requirements.txt
# Set SLACK_APP_TOKEN and SLACK_BOT_TOKEN in .env
python main.py
```

Streams messages from all channels the bot is in. To send: `channel_id message` or `channel_id1,channel_id2 message`

## Library usage

```python
from notion_connector import list_all_pages, read_page

# List all accessible pages
pages = list_all_pages()

# Read a specific page
content = read_page("page-id-or-url")
```
from slack_connector import stream_messages, send_message

# Stream from all channels (real-time, chronological)
for channel_id, user_id, message, timestamp in stream_messages():
    print(f"[{channel_id}] {user_id}: {message}")

# Send to one or more channels
send_message("C0ABC123", "Hello")
send_message(["C0ABC123", "C0XYZ789"], "Hello everyone")
```
