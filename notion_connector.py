"""
Notion Connector - Read Notion pages and return content as text/markdown.

Setup:
  - Create an integration at https://www.notion.so/my-integrations
  - Share the page(s) with your integration
  - Set NOTION_API_KEY in .env
  - Enable "Read content" capability for your integration
"""

import os
import re
from dotenv import load_dotenv
import requests

load_dotenv()

NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
NOTION_API_VERSION = "2022-06-28"


def _normalize_page_id(page_id: str) -> str:
    """Convert page ID to UUID format (with dashes). Accepts UUID, 32-char hex, or Notion URL."""
    raw = page_id.strip()
    match = re.search(r"([a-fA-F0-9]{32})", raw)
    if match:
        clean = match.group(1)
        return f"{clean[:8]}-{clean[8:12]}-{clean[12:16]}-{clean[16:20]}-{clean[20:]}"
    if re.match(r"^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$", raw):
        return raw
    return ""


def list_all_pages() -> list[dict]:
    """
    List all pages the integration has access to via Notion search.
    Returns list of page objects with at least id, object.
    """
    if not NOTION_API_KEY:
        return []

    url = "https://api.notion.com/v1/search"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_API_VERSION,
    }
    pages = []
    cursor = None

    while True:
        body = {
            "filter": {"property": "object", "value": "page"},
            "page_size": 100,
        }
        if cursor:
            body["start_cursor"] = cursor

        try:
            resp = requests.post(url, headers=headers, json=body, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.RequestException:
            break

        for item in data.get("results", []):
            if item.get("object") == "page" and not item.get("in_trash", False):
                pages.append(item)

        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
        if not cursor:
            break

    return pages


def read_page(page_id: str) -> str:
    """
    Read a Notion page and return its content as markdown text.
    Returns: Page content as markdown string, or error message on failure.
    """
    if not NOTION_API_KEY:
        return "Error: NOTION_API_KEY not set in .env"

    pid = _normalize_page_id(page_id)
    if not pid:
        return "Error: Invalid page ID."

    url = f"https://api.notion.com/v1/pages/{pid}/markdown"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_API_VERSION,
    }

    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("markdown", "")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return "Error: Page not found or integration has no access."
        if e.response.status_code == 403:
            return "Error: Integration lacks read permission."
        return f"Error: {e.response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"
