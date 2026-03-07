# SOP-violation-flagger

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
from slack_connector import stream_messages, send_message

# Stream from all channels (real-time, chronological)
for channel_id, user_id, message, timestamp in stream_messages():
    print(f"[{channel_id}] {user_id}: {message}")

# Send to one or more channels
send_message("C0ABC123", "Hello")
send_message(["C0ABC123", "C0XYZ789"], "Hello everyone")
```