#!/usr/bin/env python3
"""
Ingest Notion documents into Pinecone via the FastAPI backend.
Reads all pages the Notion integration has access to and uploads them to the vector index.
Usage: python ingest_notion.py [--api-url http://localhost:8000]
"""

import sys
import argparse
import requests
from notion_connector import list_all_pages, read_page

API_BASE_URL = "http://localhost:8000"


def extract_page_title(page: dict) -> str:
    """
    Extract page title from Notion page object.
    
    Args:
        page: Notion page object
    
    Returns:
        Page title or fallback to page ID
    """
    # Try to get title from properties
    properties = page.get("properties", {})
    
    # Common title properties
    for key in ["title", "Title", "Name", "name"]:
        if key in properties:
            title_prop = properties[key]
            if title_prop.get("type") == "title" and title_prop.get("title"):
                title_array = title_prop["title"]
                if title_array and len(title_array) > 0:
                    return title_array[0].get("plain_text", "").strip()
    
    # Fallback: try to get from page object directly
    if "title" in page:
        return page["title"]
    
    # Last resort: use page ID
    return f"Page {page.get('id', 'unknown')}"


def ingest_page(page: dict, api_url: str = API_BASE_URL) -> dict:
    """
    Ingest a single Notion page into the system.
    
    Args:
        page: Notion page object
        api_url: API base URL
    
    Returns:
        dict with 'success' (bool) and 'action' ("added" or "updated")
    """
    page_id = page.get("id", "")
    if not page_id:
        print(f"   ⚠️  Skipping page with no ID")
        return {"success": False, "action": None}
    
    # Extract title
    title = extract_page_title(page)
    
    print(f"\n📄 Processing: {title}")
    print(f"   ID: {page_id}")
    
    # Read page content
    content = read_page(page_id)
    
    if content.startswith("Error:"):
        print(f"   ❌ Failed to read: {content}")
        return {"success": False, "action": None}
    
    if not content.strip():
        print(f"   ⚠️  Skipping empty page")
        return {"success": False, "action": None}
    
    print(f"   Content length: {len(content)} characters")
    
    # Send to API
    url = f"{api_url}/ingest"
    payload = {
        "doc_id": page_id,
        "title": title,
        "content": content
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        action = result.get("action", "ingested")
        
        if action == "updated":
            print(f"   🔄 Updated existing document")
        else:
            print(f"   ✅ Added new document")
        
        return {"success": True, "action": action}
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Cannot connect to API at {api_url}")
        print(f"      Make sure the FastAPI server is running:")
        print(f"      uvicorn app.main:app --reload")
        return {"success": False, "action": None}
    except requests.exceptions.Timeout:
        print(f"   ⏱️  Timeout - page may be too large")
        return {"success": False, "action": None}
    except requests.exceptions.HTTPError as e:
        print(f"   ❌ HTTP Error: {e.response.status_code}")
        print(f"      Response: {e.response.text[:200]}")
        return {"success": False, "action": None}
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {"success": False, "action": None}


def run_ingestion(api_url: str = API_BASE_URL):
    """
    Main ingestion loop: fetch all Notion pages and ingest them.
    """
    print("🔄 Starting Notion document ingestion...")
    print(f"📡 API endpoint: {api_url}")
    print(f"📚 Fetching Notion pages...\n")
    
    # Test API connection
    try:
        health = requests.get(f"{api_url}/", timeout=5)
        health.raise_for_status()
        print(f"✅ Connected to API\n")
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print(f"   Start the server first: uvicorn app.main:app --reload\n")
        sys.exit(1)
    
    # Fetch all pages from Notion
    pages = list_all_pages()
    
    if not pages:
        print("⚠️  No pages found.")
        print("   Make sure you've:")
        print("   1. Created a Notion integration at https://www.notion.so/my-integrations")
        print("   2. Shared your pages with the integration")
        print("   3. Set NOTION_API_KEY in your .env file")
        sys.exit(1)
    
    print(f"📄 Found {len(pages)} Notion pages\n")
    print("=" * 60)
    
    # Ingest each page
    success_count = 0
    fail_count = 0
    added_count = 0
    updated_count = 0
    
    for i, page in enumerate(pages, 1):
        print(f"\n[{i}/{len(pages)}]", end=" ")
        
        result = ingest_page(page, api_url)
        
        if result["success"]:
            success_count += 1
            if result["action"] == "updated":
                updated_count += 1
            else:
                added_count += 1
        else:
            fail_count += 1
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"\n✨ Ingestion complete!")
    print(f"   ✅ Success: {success_count}")
    if added_count > 0:
        print(f"      📝 New documents added: {added_count}")
    if updated_count > 0:
        print(f"      🔄 Existing documents updated: {updated_count}")
    print(f"   ❌ Failed: {fail_count}")
    print(f"   📊 Total processed: {len(pages)}")
    print(f"\n💡 Note: Other documents in Pinecone remain untouched")
    
    if fail_count > 0:
        print(f"\n⚠️  Some pages failed to ingest. Check the logs above for details.")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Ingest Notion documents into SOP violation flagger system"
    )
    parser.add_argument(
        "--api-url",
        default=API_BASE_URL,
        help="API base URL (default: http://localhost:8000)"
    )
    
    args = parser.parse_args()
    
    run_ingestion(args.api_url)


if __name__ == "__main__":
    main()
