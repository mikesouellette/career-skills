---
description: "View or initialize your jobseeker bio. Use this when the user runs /bio, asks to see their bio, or wants to set up their profile."
allowed-tools: Read, Write, Bash(test:*)
---

Check whether `data/bio.md` exists in the project root.

```bash
test -f data/bio.md
```

**If the file does NOT exist (exit code non-zero):**

Create `data/bio.md` with the following template content exactly as shown, then tell the user the file has been created and they should fill it in — it is the single source of truth used by `/position` to evaluate job postings.

```markdown
# Jobseeker Bio

> This file is the single source of truth for your career profile.
> Fill in each section. Remove placeholder text.
> Used by `/position <url>` to evaluate job postings.

---

## Contact

- **Name:** Your Name
- **Location:** City, State (e.g., Austin, TX)
- **Email:** you@example.com
- **Phone:** (optional)
- **LinkedIn:** https://linkedin.com/in/yourhandle
- **GitHub:** https://github.com/yourhandle
- **Portfolio/Website:** (optional)

---

## Professional Summary

2–3 sentences describing your background, what you do, and what you're looking for next.

---

## Target Role

- **Title(s):** e.g., Senior Software Engineer, Staff Engineer, Engineering Manager
- **Location preference:** Remote / Hybrid / Onsite / Open to relocation / Specific cities: ...
- **Base salary target:** $XXX,000
- **Total comp target:** $XXX,000
- **Industries of interest:** (optional) e.g., fintech, healthtech, developer tools
- **Company size preference:** (optional) e.g., startup, mid-size, enterprise
- **Not interested in:** (optional) e.g., defense, crypto

---

## Skills

### Primary (strong / daily use)
- Language/framework 1
- Language/framework 2

### Secondary (familiar / occasional use)
- Tool/technology 1
- Tool/technology 2

### Certifications / Credentials
- (optional)

---

## Work Experience

### Company Name | Job Title | Month Year – Month Year (or Present)

- Key accomplishment or responsibility
- Key accomplishment or responsibility
- Key accomplishment or responsibility

### Company Name | Job Title | Month Year – Month Year

- Key accomplishment or responsibility

---

## Project Experience

### Project Name | Brief description | Year

- What you built and why
- Technologies used
- Outcome / impact

---

## Education

- **Degree**, Major — University Name, Year
- (optional) Relevant coursework, honors, etc.

---

## Other

- Open source contributions, publications, talks, patents, etc.
```

**If the file DOES exist:**

Read `data/bio.md` and display its full contents, then add this note at the end of your response:

> **Tip:** Edit `data/bio.md` directly to update your profile. All `/position` analyses will use the latest version.
