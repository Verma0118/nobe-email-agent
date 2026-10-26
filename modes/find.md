# Mode: find (build a target list)

Trigger: "find 10 Champaign robotics startups for PD", "who should Consulting email", "targets".

## 1. Scope
From the request (ask only what is missing): committee, how many (default 10), where (default
Champaign-Urbana first, then Chicago, then remote-friendly US startups), and any industry.
Use the committee's `good_targets` in `config/nobe.json` as the default filter.

## 2. Search (run in parallel)
- Web search for lists: incubator tenant pages (EnterpriseWorks, UIUC Research Park), Cozad
  finalists and winners pages (as a source of startups, never mentioned in the email), local
  business directories, Chicago startup lists, industry news.
- If an `exa` MCP tool is available, use `company_research` / web search for each candidate.
- Prior NOBE clients are the easiest yes: `brain.py list --status client` and `--status call`.

## 3. Check each candidate
For each company, `python3 tools/research.py <site> --links`, then the team or about page.
Run `python3 tools/brain.py list --company "<name>"` for each. Contacts already in the brain are
never listed again. A company with active threads goes in the table with a note "in brain: <who>".
Keep it only if all are true:
- Real and active (site loads, recent news, product, or job post within ~12 months).
- Small enough to want a student team (startups, SMBs, nonprofits). A big company goes in tier 3
  as "sponsorship route", not a cold project pitch.
- There is a concrete deliverable from the committee's `deliverables` that fits them.

## 4. Output
Show a table, then save the same rows to `targets/<committee>-<YYYY-MM-DD>.csv`
(columns: tier, company, site, what_they_do, project_idea, contact_name, contact_role,
contact_email, email_evidence, source_url).

```
Tier | Company | What they do | Project idea (committee) | Contact | Source
1    | ...     | ...          | ...                      | ...     | url
```

Tiers: **1** small team + clear project + named contact. **2** good fit but generic inbox or
weaker project. **3** large company, sponsorship route only.

Contacts: name + role from the company's own team page. Email only with evidence (listed on the
site, or a documented pattern + `dig +short MX <domain>`). Otherwise leave it blank and write
"needs email".

Then ask: "Draft emails for tier 1?" Hand off to `modes/draft.md`, one company at a time.
