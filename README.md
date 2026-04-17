# career-skills

A Claude Code toolkit for evaluating job postings against your personal career profile. Uses custom slash commands and a lightweight Python scraper — no external dependencies required.

## What it does

| Command | Description |
|---------|-------------|
| `/bio` | View or initialize your jobseeker profile |
| `/position <url>` | Analyze a job posting against your bio (skills, location, comp, seniority, company reputation) |
| `/position` | Batch-analyze all URLs in `data/positions.md` |
| `/submit <url>` | Add a job to the tracker API |
| `/liveness` | Check whether tracked jobs are still live |

`/position` scrapes the posting, runs web searches for company reputation (Glassdoor, layoffs, funding), and produces a scored report with a clear Apply / Maybe / Skip recommendation.

## Requirements

- [Claude Code](https://claude.ai/code) (CLI or desktop app)
- Python 3.8+ (stdlib only — no `pip install` needed)
- `/submit` and `/liveness` require the optional [JobSearchLog](https://github.com/mikesouellette/JobSearchLog) running at `http://127.0.0.1:8000`

## Setup

```bash
git clone https://github.com/mikesouellette/career-skills.git
cd career-skills
```

Open the project in Claude Code, then run:

```
/bio
```

This creates `data/bio.md` from a template. Fill in your profile — it is the source of truth for all `/position` analyses.

## Usage

### Evaluate a single posting

```
/position https://boards.greenhouse.io/acme/jobs/12345
```

Claude scrapes the posting, researches the company, and returns a report like:

```
## Senior Engineer @ Acme Corp

**Overall: Strong Match** — Score: 8/10
Skills align well; remote-friendly; comp slightly below target.

### Dimension Breakdown
| Dimension    | Score | Notes                          |
|--------------|-------|--------------------------------|
| Skills       | 9/10  | Covers 8/10 required skills    |
| Location     | ✓     | Remote, matches preference     |
| Compensation | ~     | $190–210k posted, target $220k |
| Seniority    | ✓     | IC5 level, matches experience  |
| Company      | ✓     | Glassdoor 4.2/5 · No layoffs   |

### Recommendation: Apply
Strong skills match and remote role; comp gap is negotiable.
```

### Batch evaluation

Add one URL per line to `data/positions.md`, then run `/position` with no arguments. Claude processes each URL and outputs a ranked summary table.

### Track a job

```
/submit https://boards.greenhouse.io/acme/jobs/12345
/submit https://boards.greenhouse.io/acme/jobs/12345 hybrid
```

Requires the tracker API. Work type (`remote`, `hybrid`, `on_site`) is inferred from the posting or can be passed explicitly.

### Check liveness

```
/liveness
```

Scrapes all active jobs in the tracker and flags any that appear to have been taken down.

## Project layout

```
.
├── .claude/
│   └── commands/          # Custom slash command definitions
│       ├── bio.md
│       ├── liveness.md
│       ├── position.md
│       └── submit.md
├── data/
│   ├── bio.md             # Your profile (gitignored — created by /bio)
│   └── positions.md       # URLs to batch-analyze (gitignored)
└── scripts/
    └── scrape_position.py # Stdlib-only job posting scraper
```

## Scraper details

`scripts/scrape_position.py` fetches a job posting URL and returns structured JSON:

```json
{
  "title": "Senior Engineer",
  "company": "Acme Corp",
  "location": "Austin, TX",
  "remote": true,
  "salary": "USD190000–USD210000 YEAR",
  "description": "...",
  "requirements": "...",
  "url": "https://..."
}
```

Extraction priority:
1. JSON-LD `schema.org/JobPosting` — works on Greenhouse, Lever, LinkedIn, Workday, and most modern ATS platforms
2. `<main>` / `<article>` content fallback for everything else

## License

MIT — see [LICENSE](LICENSE).
