"""
Slack Connector - Slack connections and message streaming.
Streams messages from ALL channels the bot is in, in real-time order (by timestamp).
Yields (channel_id, user_id, message, timestamp) for each message.

Setup in Slack:
  - Settings > Socket Mode: Enable
  - Basic Information > App-Level Tokens: connections:write
  - Event Subscriptions: message.channels, message.groups, message.im, message.mpim
  - OAuth scopes: chat:write, channels:history, groups:history, im:history, mpim:history, users:read
"""

import os
import threading
from queue import Queue
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode.request import SocketModeRequest

load_dotenv()

SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")

# Shared web client for send_message (initialized on first stream_messages call)
_web_client: WebClient | None = None


def stream_messages():
    """
    Generator that yields (channel_id, user_id, message, timestamp) for each incoming message
    from ALL channels the bot is in. Messages arrive in real-time chronological order.
    """
    global _web_client
    if not SLACK_APP_TOKEN or not SLACK_BOT_TOKEN:
        raise RuntimeError(
            "Set SLACK_APP_TOKEN and SLACK_BOT_TOKEN in .env. "
            "See slack_connector.py docstring for setup."
        )

    queue: Queue[tuple[str, str, str, str] | None] = Queue()

    def on_request(client: SocketModeClient, req: SocketModeRequest) -> None:
        if req.type != "events_api":
            return
        response = SocketModeResponse(envelope_id=req.envelope_id)
        client.send_socket_mode_response(response)

        event = req.payload.get("event", {})
        if event.get("type") != "message" or event.get("bot_id"):
            return
        # Skip edits, deletes, joins, etc. Thread replies typically have no subtype (just thread_ts)
        subtype = event.get("subtype", "")
        if subtype and subtype not in ("thread_broadcast",):
            return

        queue.put((
            event.get("channel", ""),
            event.get("user", ""),
            event.get("text", ""),
            event.get("ts", ""),
        ))

    _web_client = WebClient(token=SLACK_BOT_TOKEN)
    socket_client = SocketModeClient(
        app_token=SLACK_APP_TOKEN,
        web_client=_web_client,
    )
    socket_client.socket_mode_request_listeners.append(on_request)

    thread = threading.Thread(target=socket_client.connect, daemon=True)
    thread.start()

    while True:
        item = queue.get()
        if item is None:
            break
        yield item


def send_message(channel_ids: str | list[str], text: str) -> None:
    """Send a message to one or more channels. Pass channel ID or list of channel IDs."""
    client = _web_client or WebClient(token=SLACK_BOT_TOKEN)
    ids = [channel_ids] if isinstance(channel_ids, str) else channel_ids
    for cid in ids:
        client.chat_postMessage(channel=cid, text=text)
