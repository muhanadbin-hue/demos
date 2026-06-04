# Verification Plan

This is the faster approach for reviewing each local landing page against the actual business.

## 1. Audit local page content against metadata

Run:

```bash
python scripts/audit_pages.py
```

This generates:

- `scripts/audit_report.json`
- `scripts/audit_report.md`
- `scripts/flagged_pages.txt`

It scans each page folder under `docs/`, compares `index.html` content against `_site_meta.json`, and flags pages that may need review.

## 2. Extract local page metadata

Run:

```bash
python scripts/extract_pages.py
```

This generates:

- `scripts/page_metadata.json`
- `scripts/page_metadata.txt`

It extracts business titles, phone numbers, and addresses from each `docs/*/index.html` file.

## 3. Build search queries from extracted metadata

Run:

```bash
python scripts/build_queries.py
```

This generates:

- `scripts/query_list.json`

It creates a search query for each business using the local page title and metadata.

## 3. Verify businesses in bulk against search results

Run:

```bash
python scripts/verify_businesses.py --limit 20
```

This will:

- query DuckDuckGo HTML search for each business
- parse the returned page text
- compare found addresses, phones, and names against the local page data
- write `scripts/change_list.md`

Use `--limit` for a fast pilot run, then remove the limit for full verification.

## 4. Review `scripts/change_list.md`

The Markdown output will contain:

- each directory that was checked
- local page title
- expected addresses and phones
- what the search page returned
- whether the local page appears to match

## 5. Enrich the website

Focus first on pages where:

- expected local address is not found in search results
- expected local phone is not found
- local business name/title does not match the SERP text

These are the likely pages requiring update.

## Notes

- This approach is much faster than loading every page in a browser manually.
- It is still a heuristic; flagged pages should be reviewed manually before publishing changes.
- If the DuckDuckGo HTML endpoint becomes unreliable, the next step is to switch to a business-data API or a paid directory service for authoritative data.
