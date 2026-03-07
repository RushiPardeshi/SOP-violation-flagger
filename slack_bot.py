#!/usr/bin/env python3
"""
Real-time Slack SOP Compliance Monitor
Streams messages from Slack, checks for violations via API, and responds with warnings.
Usage: python slack_bot.py [--api-url http://localhost:8000]
"""

import sys
import argparse
import requests
from datetime import datetime
from slack_connector import stream_messages, send_message

API_BASE_URL = "http://localhost:8000"

# Emoji mapping for severity levels
SEVERITY_EMOJI = {
    "low": "⚠️",
    "medium": "🟡",
    "high": "🔴",
    "critical": "🚨"
}


def format_violation_message(result: dict, original_message: str) -> str:
    """
    Format a violation result into a user-friendly Slack message.
    
    Args:
        result: API response with violated, rule, severity, explanation
        original_message: The original message that triggered the violation
    
    Returns:
        Formatted Slack message string
    """
    severity = result.get("severity", "medium")
    emoji = SEVERITY_EMOJI.get(severity, "⚠️")
    rule = result.get("rule", "Unknown rule")
    explanation = result.get("explanation", "No explanation provided")
    
    # Create message with blocks for better formatting
    message = f"""{emoji} **SOP Violation Detected** ({severity.upper()})

**Rule Violated:** {rule}

**Why this is a violation:**
{explanation}

**Original message:**
> {original_message[:200]}{"..." if len(original_message) > 200 else ""}

Please review our SOPs and ensure compliance. If you believe this is a false positive, contact your manager."""
    
    return message


def check_message_compliance(channel_id: str, user_id: str, message_text: str, timestamp: str, api_url: str = API_BASE_URL) -> dict | None:
    """
    Check a message for SOP violations via the API.
    
    Returns:
        API response dict or None if request failed
    """
    url = f"{api_url}/check-message"
    payload = {
        "channel_id": channel_id,
        "user_id": user_id,
        "message_text": message_text,
        "timestamp": timestamp
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to API at {api_url}")
        print(f"   Make sure the FastAPI server is running:")
        print(f"   uvicorn app.main:app --reload")
        return None
    except requests.exceptions.Timeout:
        print(f"⏱️  Timeout checking message: {message_text[:50]}...")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"❌ API Error: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None


def run_bot(api_url: str = API_BASE_URL):
    """
    Main bot loop: stream messages, check compliance, respond to violations.
    """
    print("🤖 SOP Compliance Bot starting...")
    print(f"📡 API endpoint: {api_url}")
    print(f"👂 Listening to all Slack channels...\n")
    
    # Test API connection
    try:
        health = requests.get(f"{api_url}/", timeout=5)
        health.raise_for_status()
        print(f"✅ Connected to API\n")
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print(f"   Start the server first: uvicorn app.main:app --reload\n")
        sys.exit(1)
    
    message_count = 0
    violation_count = 0
    
    try:
        for channel_id, user_id, message, ts in stream_messages():
            message_count += 1
            time_str = datetime.fromtimestamp(float(ts)).strftime("%H:%M:%S") if ts else ""
            
            print(f"[{time_str}] #{channel_id} <{user_id}>: {message[:80]}{'...' if len(message) > 80 else ''}")
            
            # Check message for violations
            result = check_message_compliance(channel_id, user_id, message, ts, api_url)
            
            if result is None:
                print(f"   ⚠️  Failed to check message (API error)")
                continue
            
            # If violation detected, send warning
            if result.get("violated", False):
                violation_count += 1
                severity = result.get("severity", "medium")
                rule = result.get("rule", "Unknown")
                
                print(f"   🚨 VIOLATION DETECTED!")
                print(f"      Severity: {severity.upper()}")
                print(f"      Rule: {rule}")
                
                # Format and send warning message
                warning = format_violation_message(result, message)
                
                try:
                    send_message(channel_id, warning)
                    print(f"   ✅ Warning sent to channel")
                except Exception as e:
                    print(f"   ❌ Failed to send warning: {e}")
            else:
                print(f"   ✓ Compliant")
            
            # Print stats every 10 messages
            if message_count % 10 == 0:
                print(f"\n📊 Stats: {message_count} messages checked, {violation_count} violations detected\n")
            
            print()  # Blank line for readability
            
    except KeyboardInterrupt:
        print(f"\n\n🛑 Bot stopped")
        print(f"📊 Final stats: {message_count} messages checked, {violation_count} violations detected")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Real-time Slack SOP compliance monitor"
    )
    parser.add_argument(
        "--api-url", 
        default=API_BASE_URL,
        help="API base URL (default: http://localhost:8000)"
    )
    
    args = parser.parse_args()
    
    run_bot(args.api_url)


if __name__ == "__main__":
    main()
