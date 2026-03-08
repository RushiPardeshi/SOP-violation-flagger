"""
Slack Connector - Slack connections and message streaming.
Streams messages from ALL channels the bot is in, in real-time order (by timestamp).
Handles slash commands (/check-sop) and reaction_added for feedback.

Setup in Slack:
  - Settings > Socket Mode: Enable
  - Basic Information > App-Level Tokens: connections:write
  - Event Subscriptions: message.channels, message.groups, message.im, message.mpim, reaction_added
  - Slash Commands: /check-sop, /sop-analytics
  - OAuth scopes: chat:write, channels:history, groups:history, im:history, mpim:history, users:read, reactions:write
"""

import os
import threading
import time
import requests
from queue import Queue
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode.request import SocketModeRequest

load_dotenv()

SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")

# Shared web client (initialized on first stream_messages call)
_web_client: WebClient | None = None
_socket_client: SocketModeClient | None = None


def _get_client() -> WebClient:
    return _web_client or WebClient(token=SLACK_BOT_TOKEN)


def stream_messages(api_url: str = "http://localhost:8000"):
    """
    Generator that yields (channel_id, user_id, message, timestamp) for each incoming message.
    Also handles /check-sop slash commands and reaction_added for feedback.
    """
    global _web_client, _socket_client
    if not SLACK_APP_TOKEN or not SLACK_BOT_TOKEN:
        raise RuntimeError(
            "Set SLACK_APP_TOKEN and SLACK_BOT_TOKEN in .env. "
            "See slack_connector.py docstring for setup."
        )

    queue: Queue[tuple[str, str, str, str] | None] = Queue()

    def on_request(client: SocketModeClient, req: SocketModeRequest) -> None:
        # Always ack quickly
        response = SocketModeResponse(envelope_id=req.envelope_id)

        # Slash command: /check-sop or /sop-analytics
        if req.type == "slash_commands":
            payload = req.payload or {}
            cmd = payload.get("command", "")
            if os.environ.get("SLACK_DEBUG"):
                print(f"[Slack] Slash command: {cmd} from {payload.get('user_id')}")

            # /sop-analytics [since date] - e.g. /sop-analytics 2025-01-01
            if cmd == "/sop-analytics":
                since = payload.get("text", "").strip() or None
                try:
                    r = requests.get(
                        f"{api_url}/analytics/stats",
                        params={"since": since} if since else {},
                        timeout=10,
                    )
                    data = r.json() if r.ok else {}
                    total = data.get("total_violations", 0)
                    by_sev = data.get("by_severity", {})
                    by_ch = data.get("by_channel", [])[:5]
                    by_rule = data.get("by_rule", [])[:5]
                    fb = data.get("feedback", {})

                    lines = [
                        f"📊 *SOP Analytics*" + (f" (since {since})" if since else ""),
                        f"Total violations: *{total}*",
                        "",
                        "*By severity:* " + ", ".join(f"{k}: {v}" for k, v in by_sev.items()) or "—",
                        "",
                        "*Top channels:*",
                    ]
                    for row in by_ch:
                        lines.append(f"  • {row.get('channel_id', '?')}: {row.get('count', 0)}")
                    if not by_ch:
                        lines.append("  —")
                    lines.extend(["", "*Top rules:*"])
                    for row in by_rule:
                        rule = (row.get("rule", "?") or "")[:50]
                        lines.append(f"  • {rule}: {row.get('count', 0)}")
                    if not by_rule:
                        lines.append("  —")
                    lines.extend([
                        "",
                        f"*Feedback:* 👍 {fb.get('correct', 0)} correct, ❌ {fb.get('false_positives', 0)} false positives",
                    ])
                    msg = "\n".join(lines)
                except Exception as e:
                    msg = f":warning: Could not fetch analytics: {e}"
                response = SocketModeResponse(envelope_id=req.envelope_id, payload={"text": msg})
                client.send_socket_mode_response(response)
                return

            elif cmd == "/check-sop":
                text = payload.get("text", "").strip()
                user_id = payload.get("user_id", "")
                channel_id = payload.get("channel_id", "")
                try:
                    r = requests.post(
                        f"{api_url}/check-message",
                        json={
                            "channel_id": channel_id,
                            "user_id": user_id,
                            "message_text": text or "(empty)",
                            "timestamp": str(time.time()),
                        },
                        timeout=10,
                    )
                    data = r.json() if r.ok else {}
                    if data.get("violated"):
                        msg = (
                            f":rotating_light: *Would violate:* {data.get('rule', 'Unknown')}\n"
                            f"*Severity:* {data.get('severity', 'medium').upper()}\n"
                            f"*Why:* {data.get('explanation', '')}\n\n"
                            f"Consider revising before posting."
                        )
                    else:
                        msg = ":white_check_mark: *Looks compliant* — No SOP violations detected for this message."
                except Exception as e:
                    msg = f":warning: Could not check: {e}"
                response = SocketModeResponse(envelope_id=req.envelope_id, payload={"text": msg})
            else:
                # Unknown slash command (from another app or misconfigured)
                response = SocketModeResponse(envelope_id=req.envelope_id)
            client.send_socket_mode_response(response)
            return

        # Reaction added (feedback on our violation messages)
        if req.type == "events_api":
            event = req.payload.get("event", {})
            if event.get("type") == "reaction_added":
                reaction = event.get("reaction", "")
                item = event.get("item", {})
                if item.get("type") == "message" and reaction in ("x", "no", "white_check_mark", "heavy_check_mark"):
                    channel_id = item.get("channel", "")
                    message_ts = item.get("ts", "")
                    user_id = event.get("user", "")
                    feedback_type = "false_positive" if reaction in ("x", "no") else "correct"
                    try:
                        requests.post(
                            f"{api_url}/feedback",
                            json={
                                "channel_id": channel_id,
                                "bot_message_ts": message_ts,
                                "feedback_type": feedback_type,
                                "user_id": user_id,
                            },
                            timeout=5,
                        )
                    except Exception:
                        pass
                client.send_socket_mode_response(response)
                return

            # Regular message
            if event.get("type") != "message" or event.get("bot_id"):
                client.send_socket_mode_response(response)
                return
            subtype = event.get("subtype", "")
            if subtype and subtype not in ("thread_broadcast",):
                client.send_socket_mode_response(response)
                return

            queue.put((
                event.get("channel", ""),
                event.get("user", ""),
                event.get("text", ""),
                event.get("ts", ""),
            ))

        client.send_socket_mode_response(response)

    _web_client = WebClient(token=SLACK_BOT_TOKEN)
    _socket_client = SocketModeClient(
        app_token=SLACK_APP_TOKEN,
        web_client=_web_client,
    )
    _socket_client.socket_mode_request_listeners.append(on_request)

    thread = threading.Thread(target=_socket_client.connect, daemon=True)
    thread.start()

    while True:
        item = queue.get()
        if item is None:
            break
        yield item


def send_message(
    channel_ids: str | list[str],
    text: str,
    thread_ts: str | None = None,
) -> str | None:
    """
    Send a message to one or more channels.
    Returns the ts of the first message sent (for violation recording), or None.
    """
    client = _get_client()
    ids = [channel_ids] if isinstance(channel_ids, str) else channel_ids
    first_ts = None
    for cid in ids:
        resp = client.chat_postMessage(channel=cid, text=text, thread_ts=thread_ts)
        if first_ts is None and resp.get("ok"):
            first_ts = resp.get("ts")
    return first_ts


def add_reaction(channel_id: str, message_ts: str, emoji: str) -> None:
    """Add a reaction to a message (e.g. for feedback prompts)."""
    client = _get_client()
    client.reactions_add(channel=channel_id, timestamp=message_ts, name=emoji.replace(":", ""))


def send_onboarding_dm(user_id: str, text: str) -> bool:
    """Open a DM with user and send onboarding message. Returns True if sent."""
    try:
        client = _get_client()
        resp = client.conversations_open(users=[user_id])
        if not resp.get("ok"):
            return False
        channel_id = resp.get("channel", {}).get("id")
        if not channel_id:
            return False
        client.chat_postMessage(channel=channel_id, text=text)
        return True
    except Exception:
        return False
