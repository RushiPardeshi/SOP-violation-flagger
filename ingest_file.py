#!/usr/bin/env python3
"""
Ingest a single file (like sop.txt) into Pinecone via the FastAPI backend.
Usage: python ingest_file.py <file_path> [--doc-id <id>] [--title <title>]
"""

import sys
import argparse
import requests
from pathlib import Path

API_BASE_URL = "http://localhost:8000"


def ingest_file(file_path: str, doc_id: str = None, title: str = None, api_url: str = None) -> dict:
    """
    Read a file and post it to the /ingest endpoint.
    
    Args:
        file_path: Path to the file to ingest
        doc_id: Optional custom document ID (defaults to filename)
        title: Optional custom title (defaults to filename)
        api_url: Optional API base URL (defaults to API_BASE_URL)
    
    Returns:
        Response dict from the API
    """
    if api_url is None:
        api_url = API_BASE_URL
    
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Read file content
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Generate defaults if not provided
    if not doc_id:
        doc_id = path.stem  # filename without extension
    if not title:
        title = path.name  # filename with extension
    
    # Prepare request
    payload = {
        "doc_id": doc_id,
        "title": title,
        "content": content
    }
    
    # Post to API
    url = f"{api_url}/ingest"
    print(f"📤 Ingesting: {file_path}")
    print(f"   Doc ID: {doc_id}")
    print(f"   Title: {title}")
    print(f"   Content length: {len(content)} characters\n")
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        action = result.get("action", "ingested")
        
        if action == "updated":
            print(f"🔄 Updated existing document: {result}")
        else:
            print(f"✅ Added new document: {result}")
        
        return result
    except requests.exceptions.ConnectionError:
        print(f"❌ Error: Cannot connect to API at {api_url}")
        print(f"   Make sure the FastAPI server is running:")
        print(f"   uvicorn app.main:app --reload")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        print(f"   Response: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Ingest a file into the SOP violation flagger system"
    )
    parser.add_argument("file_path", help="Path to the file to ingest")
    parser.add_argument("--doc-id", help="Custom document ID (default: filename)")
    parser.add_argument("--title", help="Custom title (default: filename)")
    parser.add_argument("--api-url", help="API base URL (default: http://localhost:8000)")
    
    args = parser.parse_args()
    
    ingest_file(args.file_path, args.doc_id, args.title, args.api_url)


if __name__ == "__main__":
    main()
