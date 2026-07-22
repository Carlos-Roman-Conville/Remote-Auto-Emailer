"""
Job Outreach Pipeline
=====================
Fetch jobs from APIs (RemoteOK, Remotive) -> Score with Claude -> Email top matches

Usage:
    python main.py              # Full pipeline (dry run for emails)
    python main.py --send       # Full pipeline with actual email sending
    python main.py scrape       # API scrape only (RemoteOK + Remotive)
    python main.py scrape-linkedin  # LinkedIn scrape (requires login)
    python main.py score        # Score only
    python main.py email        # Email only (dry run)
    python main.py email --send # Email only (real send)
    python main.py init         # Initialize database
"""

import sys
from db import init_db


def run_pipeline(send_emails: bool = False):
    print("=" * 60)
    print("JOB OUTREACH PIPELINE")
    print("=" * 60)

    print("\n[1/3] FETCHING JOBS FROM APIs...")
    print("-" * 40)
    from scraper_api import run_api_scraper
    jobs = run_api_scraper()

    if not jobs:
        print("No new jobs found. Exiting.")
        return

    print(f"\n[2/3] SCORING {len(jobs)} JOBS WITH CLAUDE...")
    print("-" * 40)
    from scorer import score_all_unscored
    score_all_unscored()

    print("\n[3/3] GENERATING EMAILS FOR TOP 5...")
    print("-" * 40)
    from emailer import send_top_emails
    send_top_emails(dry_run=not send_emails)

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)


def main():
    args = sys.argv[1:]
    send = "--send" in args
    command = next((a for a in args if not a.startswith("--")), None)

    if command == "init":
        print("Initializing database...")
        init_db()
        print("Database ready.")

    elif command == "scrape":
        from scraper_api import run_api_scraper
        run_api_scraper()

    elif command == "scrape-linkedin":
        from scraper import run_scraper
        run_scraper()

    elif command == "score":
        from scorer import score_all_unscored
        score_all_unscored()

    elif command == "email":
        from emailer import send_top_emails
        if not send:
            print("=== DRY RUN MODE (add --send to actually send) ===\n")
        send_top_emails(dry_run=not send)

    else:
        run_pipeline(send_emails=send)


if __name__ == "__main__":
    main()
