import os
import sys
import logging

from gmail_reader import fetch_unread_transactions
from email_parser import parse_transaction
from categorizer import categorize
from notion_client import record_exists, create_record

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)


def main():
    gmail_address = os.environ["GMAIL_ADDRESS"]
    app_password = os.environ["GMAIL_APP_PASSWORD"]
    notion_api_key = os.environ["NOTION_API_KEY"]
    database_id = os.environ["NOTION_DATABASE_ID"]

    emails = fetch_unread_transactions(gmail_address, app_password)
    log.info(f"Fetched {len(emails)} unseen email(s)")

    written = 0
    skipped = 0

    for item in emails:
        try:
            tx = parse_transaction(item["body"])
        except ValueError as e:
            log.warning(f"Skipping unparseable email: {e}")
            continue

        if record_exists(database_id, tx["date"], tx["merchant"], tx["amount"], notion_api_key):
            log.info(f"Duplicate, skipping: {tx['date']} {tx['merchant']} {tx['amount']}")
            skipped += 1
            continue

        category = categorize(tx["merchant"])
        create_record(
            database_id, tx["date"], tx["merchant"], tx["amount"], category, notion_api_key
        )
        log.info(f"Recorded: {tx['date']} | {tx['merchant']} | {tx['amount']} | {category}")
        written += 1

    log.info(f"Done. Written: {written}, Skipped duplicates: {skipped}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error(f"Fatal error: {e}")
        sys.exit(1)
