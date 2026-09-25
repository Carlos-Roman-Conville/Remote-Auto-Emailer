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


RELEVANT_TAGS = {"python", "dev", "engineer", "backend", "api", "data", "ai",
                  "machine learning", "automation", "devops", "full stack",
                  "software", "database", "sql", "etl", "scraping", "scripting",
                  "ops", "admin", "analyst", "manager", "project management",
                  "operations", "coordinator", "executive", "non tech",
                  "customer support", "marketing", "sales", "hr"}


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

    listings = data[1:] if len(data) > 1 else []
    jobs = []

    for item in listings:
        title = item.get("position", "")
        company = item.get("company", "")
        location = item.get("location", "Remote")
        description = item.get("description", "")
        item_tags = [t.lower() for t in item.get("tags", [])]
        tags_text = " ".join(item_tags)
        url = item.get("url", "")
        job_id = make_job_id("remoteok", str(item.get("id", "")))
        date = item.get("date", "")

        if not title:
            continue

        # Skip irrelevant jobs — must have at least one relevant tag
        if item_tags and not any(t in RELEVANT_TAGS for t in item_tags):
            continue

        combined_text = f"{title} {description} {tags_text}"

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
            "https://remotive.com/api/remote-jobs",
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


def fetch_arbeitnow() -> list[dict]:
    """Fetch jobs from Arbeitnow JSON API."""
    print("Fetching from Arbeitnow...")
    try:
        resp = requests.get("https://www.arbeitnow.com/api/job-board-api", timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  Arbeitnow fetch failed: {e}")
        return []

    listings = data.get("data", [])
    jobs = []

    for item in listings:
        title = item.get("title", "")
        company = item.get("company_name", "")
        location = item.get("location", "Remote")
        description = item.get("description", "")
        tags = " ".join(item.get("tags", []))
        url = item.get("url", "")
        job_id = make_job_id("arbeitnow", item.get("slug", str(hash(title + company))))
        date = item.get("created_at", "")

        if not title or not item.get("remote", False):
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
            "posted_date": str(date),
            "keyword_score": keyword_score(combined_text),
        })

    print(f"  Arbeitnow: {len(jobs)} remote jobs passed filters")
    return jobs


def fetch_jobicy() -> list[dict]:
    """Fetch jobs from Jobicy JSON API."""
    print("Fetching from Jobicy...")
    try:
        resp = requests.get(
            "https://jobicy.com/api/v2/remote-jobs?count=50&tag=python",
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  Jobicy fetch failed: {e}")
        return []

    listings = data.get("jobs", [])
    jobs = []

    for item in listings:
        title = item.get("jobTitle", "")
        company = item.get("companyName", "")
        location = item.get("jobGeo", "Remote")
        description = item.get("jobDescription", "")
        url = item.get("url", "")
        job_id = make_job_id("jobicy", str(item.get("id", "")))
        date = item.get("pubDate", "")

        if not title:
            continue

        combined_text = f"{title} {description}"

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

    print(f"  Jobicy: {len(jobs)} jobs passed filters")
    return jobs


def run_api_scraper(max_jobs: int = DAILY_SCRAPE_TARGET, min_keyword_score: float = 1.5) -> list[dict]:
    """Fetch from all API sources, dedupe, and insert into DB."""
    all_jobs = []
    all_jobs.extend(fetch_remoteok())
    all_jobs.extend(fetch_remotive())
    all_jobs.extend(fetch_arbeitnow())
    all_jobs.extend(fetch_jobicy())

    # Filter out low-relevance jobs and sort by keyword score
    all_jobs = [j for j in all_jobs if j["keyword_score"] >= min_keyword_score]
    all_jobs.sort(key=lambda j: j["keyword_score"], reverse=True)

    print(f"\n{len(all_jobs)} jobs above minimum keyword score ({min_keyword_score})")

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
