#!/usr/bin/env python3
"""
Clear all vectors from Pinecone namespace.
Usage: python clear_pinecone.py [--namespace <name>]
"""

import argparse
from pinecone import Pinecone
from dotenv import load_dotenv
import os

load_dotenv()

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_INDEX_HOST = os.environ.get("PINECONE_INDEX_HOST")
PINECONE_NAMESPACE = os.environ.get("PINECONE_NAMESPACE", "default")


def clear_namespace(namespace: str):
    """Delete all vectors from a Pinecone namespace."""
    print(f"🗑️  Clearing Pinecone namespace: {namespace}")
    print(f"📡 Index host: {PINECONE_INDEX_HOST}")
    
    if not PINECONE_API_KEY or not PINECONE_INDEX_HOST:
        print("❌ Error: PINECONE_API_KEY and PINECONE_INDEX_HOST must be set in .env")
        return False
    
    try:
        # Connect to Pinecone
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(host=PINECONE_INDEX_HOST)
        
        # Get index stats before deletion
        stats = index.describe_index_stats()
        namespace_stats = stats.get('namespaces', {}).get(namespace, {})
        vector_count = namespace_stats.get('vector_count', 0)
        
        if vector_count == 0:
            print(f"✅ Namespace '{namespace}' is already empty (0 vectors)")
            return True
        
        print(f"📊 Found {vector_count} vectors in namespace '{namespace}'")
        print(f"⚠️  WARNING: This will delete ALL vectors!")
        
        # Confirm deletion
        response = input(f"\nType 'yes' to confirm deletion: ")
        if response.lower() != 'yes':
            print("❌ Deletion cancelled")
            return False
        
        # Delete all vectors in namespace
        print(f"\n🗑️  Deleting all vectors...")
        index.delete(delete_all=True, namespace=namespace)
        
        print(f"✅ Successfully cleared namespace '{namespace}'")
        
        # Verify deletion
        stats_after = index.describe_index_stats()
        namespace_stats_after = stats_after.get('namespaces', {}).get(namespace, {})
        vector_count_after = namespace_stats_after.get('vector_count', 0)
        
        if vector_count_after == 0:
            print(f"✅ Verified: namespace now has 0 vectors")
        else:
            print(f"⚠️  Warning: namespace still has {vector_count_after} vectors (may take a moment to fully clear)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error clearing namespace: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Clear all vectors from Pinecone namespace"
    )
    parser.add_argument(
        "--namespace",
        default=PINECONE_NAMESPACE,
        help=f"Namespace to clear (default: {PINECONE_NAMESPACE})"
    )
    
    args = parser.parse_args()
    
    clear_namespace(args.namespace)


if __name__ == "__main__":
    main()
