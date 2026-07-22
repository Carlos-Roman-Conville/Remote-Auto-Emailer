import random
import time
import re
from playwright.sync_api import sync_playwright
from config import LINKEDIN_EMAIL, LINKEDIN_PASSWORD, KEYWORDS, NEGATIVE_KEYWORDS, DAILY_SCRAPE_TARGET
from db import insert_job, already_scraped


def random_delay(min_s=2, max_s=6):
    time.sleep(random.uniform(min_s, max_s))


def login(page):
    page.goto("https://www.linkedin.com/login")
    random_delay(1, 3)
    page.fill('input[name="session_key"]', LINKEDIN_EMAIL)
    random_delay(0.5, 1.5)
    page.fill('input[name="session_password"]', LINKEDIN_PASSWORD)
    random_delay(0.5, 1)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle", timeout=15000)
    random_delay(2, 4)


def build_search_url(keywords: list[str], page_num: int = 0) -> str:
    query = " OR ".join(keywords[:5])
    start = page_num * 25
    return (
        f"https://www.linkedin.com/jobs/search/"
        f"?keywords={query}"
        f"&location=United%20States"
        f"&f_TPR=r86400"  # past 24 hours
        f"&f_WT=2"  # remote
        f"&start={start}"
    )


def has_negative_keyword(text: str) -> bool:
    text_lower = text.lower()
    return any(neg in text_lower for neg in NEGATIVE_KEYWORDS)


def keyword_score(text: str) -> float:
    text_lower = text.lower()
    matches = sum(1 for kw in KEYWORDS if kw.lower() in text_lower)
    return matches / len(KEYWORDS) * 10


def extract_job_id(url: str) -> str | None:
    match = re.search(r"/jobs/view/(\d+)", url)
    if match:
        return match.group(1)
    match = re.search(r"currentJobId=(\d+)", url)
    if match:
        return match.group(1)
    return None


def scrape_job_listings(page, max_jobs: int = DAILY_SCRAPE_TARGET) -> list[dict]:
    jobs = []
    page_num = 0

    while len(jobs) < max_jobs:
        url = build_search_url(KEYWORDS, page_num)
        page.goto(url)
        random_delay(3, 6)

        job_cards = page.query_selector_all(".job-card-container, .jobs-search-results__list-item")

        if not job_cards:
            print(f"No job cards found on page {page_num}, stopping.")
            break

        for card in job_cards:
            if len(jobs) >= max_jobs:
                break

            try:
                title_el = card.query_selector(".job-card-list__title, .job-card-container__link")
                title = title_el.inner_text().strip() if title_el else ""

                company_el = card.query_selector(".job-card-container__primary-description, .artdeco-entity-lockup__subtitle")
                company = company_el.inner_text().strip() if company_el else ""

                location_el = card.query_selector(".job-card-container__metadata-item, .artdeco-entity-lockup__caption")
                location = location_el.inner_text().strip() if location_el else ""

                link_el = card.query_selector("a[href*='/jobs/view/']")
                job_url = link_el.get_attribute("href") if link_el else ""
                if job_url and not job_url.startswith("http"):
                    job_url = "https://www.linkedin.com" + job_url

                job_id = extract_job_id(job_url) if job_url else None

                if not job_id or not title:
                    continue

                if already_scraped(job_id):
                    continue

                if has_negative_keyword(title):
                    continue

                card.click()
                random_delay(2, 4)

                desc_el = page.query_selector(".jobs-description__content, .jobs-box__html-content")
                description = desc_el.inner_text().strip() if desc_el else ""

                if has_negative_keyword(description):
                    continue

                score = keyword_score(title + " " + description)

                job = {
                    "linkedin_job_id": job_id,
                    "title": title,
                    "company": company,
                    "location": location,
                    "description": description[:5000],
                    "job_url": job_url,
                    "posted_date": None,
                }

                db_id = insert_job(job)
                if db_id:
                    jobs.append({**job, "id": db_id, "keyword_score": score})
                    print(f"[{len(jobs)}/{max_jobs}] {title} @ {company} (kw_score: {score:.1f})")

            except Exception as e:
                print(f"Error processing card: {e}")
                continue

            random_delay(1, 3)

        page_num += 1
        random_delay(3, 6)

    return jobs


def run_scraper():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        )
        page = context.new_page()

        print("Logging into LinkedIn...")
        login(page)
        print("Logged in. Starting job scrape...")

        jobs = scrape_job_listings(page)
        print(f"\nScraped {len(jobs)} jobs total.")

        browser.close()
        return jobs


if __name__ == "__main__":
    run_scraper()
