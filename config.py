import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
DB_URL = os.getenv("DB_URL", "postgresql://localhost:5432/job_outreach")

DAILY_SCRAPE_TARGET = 40
DAILY_EMAIL_LIMIT = 5
TOP_N_TO_EMAIL = 5

KEYWORDS = [
    "python",
    "web scraping",
    "automation",
    "data pipeline",
    "api integration",
    "selenium",
    "beautifulsoup",
    "fastapi",
    "streamlit",
    "sql",
    "postgresql",
    "ai",
    "llm",
    "claude",
    "openai",
    "data entry",
    "backend",
]

NEGATIVE_KEYWORDS = [
    "senior staff",
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
]

MIN_SCORE_TO_EMAIL = 6.0

RESUME_PATH = os.path.join(os.path.dirname(__file__), "assets", "resume.pdf")
COVER_LETTER_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "assets", "cover_letter_template.txt")
