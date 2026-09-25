import anthropic
from config import ANTHROPIC_API_KEY, KEYWORDS
from db import update_scores, get_conn

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SCORING_PROMPT = """You are a job match scorer. Rate how well this job matches the candidate's profile.

CANDIDATE PROFILE:
- Background: Technical Operations Specialist (2+ years), freelance automation work
- Skills: Python (scripting/automation, NOT software engineering), web scraping (Selenium, BeautifulSoup), API integration, Claude/OpenAI APIs, SQL, Streamlit, FastAPI, data entry, process automation
- Education: B.A. Political Science, Rowan University
- Looking for: Remote operations, admin, data, automation, project coordination, or analyst roles. Entry to mid level. NOT a software developer/engineer — do not match to roles requiring CS degrees, system design, or production software engineering

JOB LISTING:
Title: {title}
Company: {company}
Location: {location}
Description:
{description}

Score this job from 1-10 based on:
- Skill match (do the requirements align with the candidate's skills?)
- Experience level fit (is this entry/mid level or does it require 5+ years?)
- Remote friendliness
- Overall opportunity quality

Respond with ONLY a JSON object, no other text:
{{"score": <number 1-10>, "summary": "<2-3 sentence explanation of fit>"}}
"""


def score_job(job: dict) -> tuple[float, str]:
    prompt = SCORING_PROMPT.format(
        title=job["title"],
        company=job["company"],
        location=job.get("location", "Not specified"),
        description=job.get("description", "No description available")[:3000],
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()

    import json
    try:
        data = json.loads(text)
        return float(data["score"]), data["summary"]
    except (json.JSONDecodeError, KeyError):
        print(f"Failed to parse scoring response: {text}")
        return 0.0, "Scoring failed"


def score_all_unscored():
    conn = get_conn()
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs WHERE status = 'scraped' ORDER BY keyword_score DESC")
    jobs = cur.fetchall()
    conn.close()

    print(f"Scoring {len(jobs)} unscored jobs...")

    for i, job in enumerate(jobs):
        kw_score = job["keyword_score"]
        ai_score, summary = score_job(job)
        update_scores(job["id"], kw_score, ai_score, summary)
        print(f"[{i+1}/{len(jobs)}] {job['title']} @ {job['company']} -> AI: {ai_score}/10 | KW: {kw_score:.1f}/10")
        print(f"         {summary}")

    print("Scoring complete.")


if __name__ == "__main__":
    score_all_unscored()
