---
description: "Submit a job posting to the job tracker. Use this when the user runs /submit <url> or asks to track/save/add a job to the tracker."
argument-hint: <job-posting-url> [remote|hybrid|on_site]
allowed-tools: Bash(python3:*), Bash(curl:*)
---

## Step 1 — Guard: require URL

If `$ARGUMENTS` is empty, stop and tell the user:
> Usage: `/submit <job-posting-url> [work_type]`
> `work_type` is optional — one of `remote`, `hybrid`, or `on_site`. If omitted, it will be inferred from the posting.

---

## Step 2 — Parse arguments

Split `$ARGUMENTS` on whitespace:
- First token → `URL`
- Optional second token → `WORK_TYPE_OVERRIDE` (if present, must be `remote`, `hybrid`, or `on_site`)

If a second token is present but is not one of those three values, stop and tell the user:
> Invalid work_type `"[value]"`. Must be one of: `remote`, `hybrid`, `on_site`.

---

## Step 3 — Scrape the job posting

```bash
python3 scripts/scrape_position.py "$URL"
```

If the scraper exits with a non-zero code or produces no output, stop and tell the user the page could not be fetched, including the error message.

Parse the JSON output. The fields of interest are: `title`, `company`, `remote` (boolean or null), `url`.

---

## Step 4 — Fill in missing fields

**company / title:** If either is empty or missing in the scraped JSON, use your reasoning to infer them from the `description`, `requirements`, or the URL domain (e.g. `careers.acme.com` → company is likely "Acme"). If you still cannot determine a value, stop and ask the user to provide it.

**work_type:** Resolve as follows:
- If `WORK_TYPE_OVERRIDE` was provided → use it.
- Else if `remote == true` → `"remote"`
- Else if `remote == false` → `"on_site"`
- Else (`null` or missing) → stop and tell the user:
  > Could not determine work type from the posting. Re-run with an explicit override:
  > `/submit <url> hybrid`

---

## Step 5 — Preview

Show the user a one-line summary of what will be submitted:

> Submitting: **[title]** @ **[company]** (`[work_type]`) → `[url]`

---

## Step 6 — POST to the tracker API

Build the JSON payload with the four required fields: `company`, `title`, `work_type`, `url`.

Escape all field values properly for inclusion in a JSON string (handle quotes, backslashes, etc.) by constructing the payload via a Python one-liner:

```bash
python3 -c "
import json, sys
payload = json.dumps({
    'company': sys.argv[1],
    'title': sys.argv[2],
    'work_type': sys.argv[3],
    'url': sys.argv[4],
})
print(payload)
" "$COMPANY" "$TITLE" "$WORK_TYPE" "$URL" > /tmp/submit_payload.json
```

Then POST it:

```bash
HTTP_STATUS=$(curl -s -o /tmp/submit_response.json -w "%{http_code}" \
  -X POST http://127.0.0.1:8000/api/jobs/ \
  -H "Content-Type: application/json" \
  -d @/tmp/submit_payload.json)
```

---

## Step 7 — Report the result

Read `/tmp/submit_response.json` for the response body.

- **201** → Job tracked successfully. If the response contains an `id` field, report:
  > Job added to tracker (id: [id]).
- **4xx** → Show the response body. Tell the user the submission was rejected and explain the error (likely a validation issue).
- **5xx or connection refused** → Tell the user:
  > Could not reach the tracker. Make sure it is running at `127.0.0.1:8000`.
