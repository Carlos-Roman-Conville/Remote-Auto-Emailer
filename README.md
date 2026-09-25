# Job Outreach (archived)

**Archived 2026-09-25. Not maintained.**

A July 2026 prototype: fetch remote jobs (RemoteOK, Remotive, a LinkedIn scraper), score them with Claude, then have
Claude write cold emails to hiring managers and send them over SMTP with a resume attached. It never sent an email:
there was no way to find hiring-manager addresses, so the outreach step had nothing to send to.

Replaced by:
- **job-auto-applier-v3**: finding, scoring and applying to jobs, without a LinkedIn password.
- **Inbox** (CRC Solutions): reading, sorting and answering job mail. Replies use the owner's own templates; a model
  never writes the sentences.

Kept for reference only.
