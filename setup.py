"""One-time setup: creates the Notion bookkeeping database.

Usage:
    NOTION_API_KEY=secret_... NOTION_PARENT_PAGE_ID=<page-id> python setup.py

Prints NOTION_DATABASE_ID to stdout. Copy it into your GitHub Secrets.
"""
import os
import sys
from notion_client import create_database


def main():
    api_key = os.environ.get("NOTION_API_KEY")
    parent_page_id = os.environ.get("NOTION_PARENT_PAGE_ID")

    if not api_key or not parent_page_id:
        print("Error: set NOTION_API_KEY and NOTION_PARENT_PAGE_ID environment variables")
        sys.exit(1)

    db_id = create_database(parent_page_id, api_key)
    print("\nNotion database created successfully!")
    print(f"NOTION_DATABASE_ID={db_id}")
    print("\nAdd this as a GitHub Secret named NOTION_DATABASE_ID")


if __name__ == "__main__":
    main()
