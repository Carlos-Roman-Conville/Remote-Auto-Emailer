import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
DB_PATH = os.path.join(os.path.dirname(__file__), "job_outreach.db")

DAILY_SCRAPE_TARGET = 40
DAILY_EMAIL_LIMIT = 5
TOP_N_TO_EMAIL = 5

KEYWORDS = [
    # Automation / scripting (your tech skills)
    "python",
    "automation",
    "web scraping",
    "scraping",
    "data entry",
    "api",
    "sql",
    "database",
    "scripting",
    "ai",
    "reporting",
    "spreadsheet",
    "excel",
    "google sheets",
    # Operations / admin / analyst
    "operations",
    "operations manager",
    "operations specialist",
    "operations coordinator",
    "technical operations",
    "project manager",
    "project coordinator",
    "project management",
    "process improvement",
    "workflow",
    "coordinator",
    "administrative",
    "analyst",
    "data analyst",
    "business analyst",
    "logistics",
    "account manager",
    "customer success",
    "virtual assistant",
    "executive assistant",
    "office manager",
]

NEGATIVE_KEYWORDS = [
    "senior staff",
    "staff engineer",
    "principal",
    "director",
    "vp ",
    "vice president",
    "10+ years",
    "8+ years",
    "phd required",
    "clearance required",
    "ts/sci",
    "java",
    "c++",
    "rust",
    "golang",
    ".net",
    "c#",
    "kernel engineer",
    "site reliability",
    "devops engineer",
    "full-stack engineer",
    "full stack engineer",
    "software engineer",
    "software developer",
    "frontend engineer",
    "react engineer",
    "node.js engineer",
]

MIN_SCORE_TO_EMAIL = 6.0

RESUME_PATH = os.path.join(os.path.dirname(__file__), "assets", "resume.pdf")
COVER_LETTER_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "assets", "cover_letter_template.txt")
