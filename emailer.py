import smtplib
import anthropic
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from config import SMTP_EMAIL, SMTP_PASSWORD, ANTHROPIC_API_KEY, RESUME_PATH
from db import get_unsent_jobs, insert_contact, insert_outreach, mark_sent

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

EMAIL_PROMPT = """Write a short, professional cold email from a job seeker to a hiring manager.

CONTEXT:
- Sender: Carlos R., freelance Python developer specializing in web scraping, automation, and AI integration
- Recipient: {contact_name}, {contact_title} at {company}
- Job: {job_title}
- Job Description Summary: {job_summary}

RULES:
- Keep it under 150 words
- Open with something specific about the company or role (not generic flattery)
- Mention 2-3 relevant skills that match the job
- End with a clear, low-pressure call to action (e.g., "happy to chat for 15 minutes")
- Professional but human tone — not robotic or overly formal
- Do NOT use phrases like "I came across your posting" or "I'm reaching out because"

Respond with ONLY a JSON object:
{{"subject": "<email subject line>", "body": "<the email body>"}}
"""


def generate_email(job: dict, contact: dict) -> tuple[str, str]:
    prompt = EMAIL_PROMPT.format(
        contact_name=contact.get("name", "Hiring Manager"),
        contact_title=contact.get("title", "Hiring Manager"),
        company=job["company"],
        job_title=job["title"],
        job_summary=job.get("ai_summary", job.get("description", "")[:500]),
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )

    import json
    text = response.content[0].text.strip()
    try:
        data = json.loads(text)
        return data["subject"], data["body"]
    except (json.JSONDecodeError, KeyError):
        return f"Application: {job['title']} at {job['company']}", text


def send_email(to_email: str, subject: str, body: str, attach_resume: bool = True):
    msg = MIMEMultipart()
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    if attach_resume and os.path.exists(RESUME_PATH):
        with open(RESUME_PATH, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(RESUME_PATH)}")
            msg.attach(part)

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, to_email, msg.as_string())


def send_top_emails(dry_run: bool = True):
    jobs = get_unsent_jobs(limit=5)

    if not jobs:
        print("No unsent jobs above the score threshold.")
        return

    print(f"Found {len(jobs)} jobs to email:\n")

    for job in jobs:
        print(f"  [{job['ai_score']}/10] {job['title']} @ {job['company']}")
        print(f"         {job.get('ai_summary', 'No summary')}")

        contact = {
            "job_id": job["id"],
            "name": "Hiring Manager",
            "title": "Hiring Manager",
            "email": None,
            "linkedin_profile_url": None,
            "source": "manual",
        }

        subject, body = generate_email(job, contact)

        print(f"\n  Subject: {subject}")
        print(f"  Body:\n{body}\n")

        if dry_run:
            print("  [DRY RUN] Email not sent. Run with --send to actually send.\n")
        else:
            if contact.get("email"):
                contact_id = insert_contact(contact)
                outreach_id = insert_outreach({
                    "job_id": job["id"],
                    "contact_id": contact_id,
                    "email_subject": subject,
                    "email_body": body,
                    "status": "sending",
                })
                send_email(contact["email"], subject, body)
                mark_sent(outreach_id)
                print(f"  SENT to {contact['email']}\n")
            else:
                print("  [SKIP] No email found for this contact.\n")

    print("Done.")


if __name__ == "__main__":
    import sys
    dry = "--send" not in sys.argv
    if dry:
        print("=== DRY RUN MODE (add --send to actually send emails) ===\n")
    send_top_emails(dry_run=dry)
