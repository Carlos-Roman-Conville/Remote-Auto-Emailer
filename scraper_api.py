"""
API-based job scrapers for RemoteOK and Remotive.
No login, no Playwright, no bot detection — just JSON APIs.
"""

import requests
import hashlib
from config import KEYWORDS, NEGATIVE_KEYWORDS, DAILY_SCRAPE_TARGET
from db import insert_job, already_scraped


def has_negative_keyword(text: str) -> bool:
    text_lower = text.lower()
    return any(neg in text_lower for neg in NEGATIVE_KEYWORDS)


def keyword_score(text: str) -> float:
    text_lower = text.lower()
    matches = sum(1 for kw in KEYWORDS if kw.lower() in text_lower)
    return matches / len(KEYWORDS) * 10


def make_job_id(source: str, unique_part: str) -> str:
    return f"{source}_{unique_part}"


def fetch_remoteok() -> list[dict]:
    """Fetch jobs from RemoteOK JSON API."""
    print("Fetching from RemoteOK...")
    try:
        resp = requests.get(
            "https://remoteok.com/api",
            headers={"User-Agent": "job-outreach-bot/1.0"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  RemoteOK fetch failed: {e}")
        return []

    # First item is metadata, skip it
    listings = data[1:] if len(data) > 1 else []
    jobs = []

    for item in listings:
        title = item.get("position", "")
        company = item.get("company", "")
        location = item.get("location", "Remote")
        description = item.get("description", "")
        tags = " ".join(item.get("tags", []))
        url = item.get("url", "")
        job_id = make_job_id("remoteok", str(item.get("id", "")))
        date = item.get("date", "")

        if not title:
            continue

        combined_text = f"{title} {description} {tags}"

        if has_negative_keyword(combined_text):
            continue

        jobs.append({
            "linkedin_job_id": job_id,
            "title": title,
            "company": company,
            "location": location,
            "description": description[:5000],
            "job_url": url if url.startswith("http") else f"https://remoteok.com{url}",
            "posted_date": date,
            "keyword_score": keyword_score(combined_text),
        })

    print(f"  RemoteOK: {len(jobs)} jobs passed filters")
    return jobs


def fetch_remotive() -> list[dict]:
    """Fetch jobs from Remotive JSON API."""
    print("Fetching from Remotive...")
    try:
        resp = requests.get(
            "https://remotive.com/api/remote-jobs?category=software-dev",
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  Remotive fetch failed: {e}")
        return []

    listings = data.get("jobs", [])
    jobs = []

    for item in listings:
        title = item.get("title", "")
        company = item.get("company_name", "")
        location = item.get("candidate_required_location", "Remote")
        description = item.get("description", "")
        url = item.get("url", "")
        job_id = make_job_id("remotive", str(item.get("id", "")))
        date = item.get("publication_date", "")
        tags = " ".join(item.get("tags", []))

        if not title:
            continue

        combined_text = f"{title} {description} {tags}"

        if has_negative_keyword(combined_text):
            continue

        jobs.append({
            "linkedin_job_id": job_id,
            "title": title,
            "company": company,
            "location": location,
            "description": description[:5000],
            "job_url": url,
            "posted_date": date,
            "keyword_score": keyword_score(combined_text),
        })

    print(f"  Remotive: {len(jobs)} jobs passed filters")
    return jobs


def run_api_scraper(max_jobs: int = DAILY_SCRAPE_TARGET) -> list[dict]:
    """Fetch from all API sources, dedupe, and insert into DB."""
    all_jobs = []
    all_jobs.extend(fetch_remoteok())
    all_jobs.extend(fetch_remotive())

    # Sort by keyword score descending, take top N
    all_jobs.sort(key=lambda j: j["keyword_score"], reverse=True)

    saved = []
    for job in all_jobs:
        if len(saved) >= max_jobs:
            break

        if already_scraped(job["linkedin_job_id"]):
            continue

        score = job.pop("keyword_score")
        db_id = insert_job(job)
        if db_id:
            saved.append({**job, "id": db_id, "keyword_score": score})
            print(f"  [{len(saved)}/{max_jobs}] {job['title']} @ {job['company']} (kw: {score:.1f})")

    print(f"\nSaved {len(saved)} new jobs to database.")
    return saved


if __name__ == "__main__":
    run_api_scraper()
