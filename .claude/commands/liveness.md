---
description: "Check whether active job postings in the tracker are still live. Use this when the user runs /liveness or asks to check/verify which jobs are still open."
allowed-tools: Bash(curl:*), Bash(python3:*)
---

## Step 1 — Fetch active jobs from the tracker

```bash
curl -s -o /tmp/liveness_jobs.json -w "%{http_code}" http://127.0.0.1:8000/api/jobs/active/
```

If the HTTP status is not 200 or the command fails, stop and tell the user:
> Could not reach the job tracker. Make sure it is running at `127.0.0.1:8000`.

Read `/tmp/liveness_jobs.json`. If the result is an empty list (`[]`), stop and tell the user:
> No active jobs found in the tracker.

---

## Step 2 — Check each job

Parse the job list. Extract each entry's `id`, `company`, `title`, and `url`.

For each job (process one at a time):

1. Announce progress to the user: `Checking [N/Total]: [company] — [title]`
2. Run the scraper:
   ```bash
   python3 scripts/scrape_position.py "<url>"
   ```
3. Determine status from the result:
   - **Non-zero exit code** → `dead` (use stderr output as `reason`)
   - **Exit 0, meaningful data** (non-empty `title` or `description`) → `live` (reason: `"Job posting found: [title]"`)
   - **Exit 0, empty/minimal data** (blank `title` and `description`) → `uncertain` (reason: `"Page loaded but no job content detected"`)

---

## Step 3 — Output the report

Collect results into groups: **dead**, **uncertain/error**, and **live**.

### Section 1 — Suspected dead or uncertain jobs

If any jobs have status `dead`, `uncertain`, or `error`, list them under this heading:

For each, show:
- **[company] — [title]** (tracker ID: [id])
  - URL: `[url]`
  - Status: `[status]`
  - Reason: [reason]

If all jobs are live, skip this section and tell the user:
> All [N] active jobs appear to still be live.

### Section 2 — Full status table

| ID | Title | Company | Status | Reason |
|----|-------|---------|--------|--------|
| [id] | [title] | [company] | [status] | [reason] |

Sort the table: dead first, then uncertain/error, then live.

---

## Step 4 — Closing note

If any dead or uncertain jobs were found, add:

> **Note:** This is a heuristic check — false positives are possible, especially for JavaScript-rendered pages. Verify flagged jobs manually before marking them inactive in the tracker.
