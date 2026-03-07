#!/usr/bin/env python3
"""
CLI wrapper for SOP Violation Flagger
Provides convenient commands for running the system.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def start_server():
    """Start the FastAPI server."""
    print("🚀 Starting FastAPI server...")
    try:
        subprocess.run(["uvicorn", "app.main:app", "--reload"], check=True)
    except KeyboardInterrupt:
        print("\n✋ Server stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)


def start_bot():
    """Start the Slack compliance bot."""
    print("🤖 Starting Slack compliance bot...")
    try:
        subprocess.run(["python", "slack_bot.py"], check=True)
    except KeyboardInterrupt:
        print("\n✋ Bot stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start bot: {e}")
        sys.exit(1)


def ingest_notion():
    """Ingest documents from Notion."""
    print("📚 Ingesting Notion documents...")
    try:
        subprocess.run(["python", "ingest_notion.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Ingestion failed: {e}")
        sys.exit(1)


def clear_pinecone():
    """Clear all vectors from Pinecone."""
    print("🗑️  Clearing Pinecone database...")
    try:
        subprocess.run(["python", "clear_pinecone.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Clear failed: {e}")
        sys.exit(1)


def ingest_file(file_path: str, doc_id: str = None, title: str = None):
    """Ingest a single file."""
    cmd = ["python", "ingest_file.py", file_path]
    if doc_id:
        cmd.extend(["--doc-id", doc_id])
    if title:
        cmd.extend(["--title", title])
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Ingestion failed: {e}")
        sys.exit(1)


def check_setup():
    """Check if environment is properly configured."""
    print("🔍 Checking setup...\n")
    
    issues = []
    
    # Check .env file
    env_file = Path(".env")
    if not env_file.exists():
        issues.append("❌ .env file not found. Run: cp .env.example .env")
    else:
        print("✅ .env file exists")
        
        # Check for required keys
        with open(env_file) as f:
            env_content = f.read()
            
        required_keys = [
            "OPENAI_API_KEY",
            "PINECONE_API_KEY",
            "PINECONE_INDEX",
            "PINECONE_INDEX_HOST"
        ]
        
        for key in required_keys:
            if f"{key}=" in env_content:
                value = [line for line in env_content.split('\n') if line.startswith(f"{key}=")]
                if value and not value[0].endswith("..."):
                    print(f"✅ {key} is set")
                else:
                    issues.append(f"⚠️  {key} needs to be configured in .env")
            else:
                issues.append(f"❌ {key} missing from .env")
    
    # Check virtual environment
    if sys.prefix == sys.base_prefix:
        issues.append("⚠️  Virtual environment not activated. Run: source .venv/bin/activate")
    else:
        print("✅ Virtual environment active")
    
    # Check dependencies
    try:
        import fastapi
        import openai
        import pinecone
        from slack_sdk import WebClient
        print("✅ All dependencies installed")
    except ImportError as e:
        issues.append(f"❌ Missing dependency: {e.name}. Run: pip install -r requirements.txt")
    
    print()
    
    if issues:
        print("⚠️  Issues found:\n")
        for issue in issues:
            print(f"   {issue}")
        print()
        return False
    else:
        print("✅ Setup looks good! You're ready to go.\n")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="SOP Violation Flagger CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py check-setup           # Verify environment setup
  python cli.py start-server          # Start FastAPI backend
  python cli.py start-bot             # Start Slack compliance bot
  python cli.py clear-pinecone        # Clear all vectors from Pinecone
  python cli.py ingest-notion         # Import SOPs from Notion
  python cli.py ingest-file sop.txt   # Import single file
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # check-setup command
    subparsers.add_parser("check-setup", help="Check if environment is properly configured")
    
    # start-server command
    subparsers.add_parser("start-server", help="Start the FastAPI server")
    
    # start-bot command
    subparsers.add_parser("start-bot", help="Start the Slack compliance bot")
    
    # clear-pinecone command
    subparsers.add_parser("clear-pinecone", help="Clear all vectors from Pinecone database")
    
    # ingest-notion command
    subparsers.add_parser("ingest-notion", help="Ingest documents from Notion")
    
    # ingest-file command
    ingest_parser = subparsers.add_parser("ingest-file", help="Ingest a single file")
    ingest_parser.add_argument("file_path", help="Path to file to ingest")
    ingest_parser.add_argument("--doc-id", help="Document ID")
    ingest_parser.add_argument("--title", help="Document title")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    if args.command == "check-setup":
        check_setup()
    elif args.command == "start-server":
        start_server()
    elif args.command == "start-bot":
        start_bot()
    elif args.command == "clear-pinecone":
        clear_pinecone()
    elif args.command == "ingest-notion":
        ingest_notion()
    elif args.command == "ingest-file":
        ingest_file(args.file_path, args.doc_id, args.title)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
