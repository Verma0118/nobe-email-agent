# NOBE Email Agent

A Claude Code agent that finds client companies and drafts outreach emails for NOBE's three
committees: **Consulting**, **Tech**, and **Product Development**. It researches the company,
writes the email in NOBE's standard format, checks it, and hands it to you. It never sends anything.

## Setup (5 minutes, once)

You need [Claude Code](https://claude.com/claude-code) installed and signed in, plus Python 3.9+
(already on every Mac).

```bash
git clone <this repo> ~/nobe-email-agent
cd ~/nobe-email-agent
./install.sh
```

Then type:

```bash
nobe-email-agent
```

The first time, it asks for your name, NOBE role, committee, and contact info, and saves them to
`profile.json` (stays on your computer, never committed).

**Optional:** connect Gmail in Claude (claude.ai > Settings > Connectors) so approved emails land
straight in your Gmail Drafts. Without it, the agent prints the final email for you to paste.

## Using it

Start it with `nobe-email-agent` and tell it what you need:

| You type | What happens |
|---|---|
| `find 10 Champaign hardware startups for PD` | Searches, checks each site, returns a tiered list with project ideas and contacts, saves a CSV to `targets/` |
| `draft for acme.com, tech` | Researches Acme, picks a contact, writes the email, lints and reviews it, shows it to you |
| `what could Consulting do for acme.com?` | Research brief only, no email |
| `draft tier 1 from targets/pd-2027-01-10.csv` | One email per company, each shown to you for approval |

Say **approve** to put an email in Gmail Drafts. Then attach the NOBE overview PDF and send it
yourself.

## The email

Subject: `[Company] x NOBE x [Committee] Project`, for example
`Acme x NOBE x Consulting Project`, `Acme x NOBE x Tech Project`, `Acme x NOBE x Product Development Project`.
The committee is picked per contact, so one company can hear from more than one committee.

```
Good Morning [Name]!

I hope your week has been off to a good start!

My name is [you], a [year] studying [major] at the University of Illinois Urbana-Champaign.
I am a [role] at NOBE (National Organization for Business and Engineering), a student
business and engineering organization on campus.

[2-3 sentences: one real, sourced fact about their company + one concrete thing your
committee could build or deliver for them.]

We propose a 12-week project from January to April, with an option to continue into the fall.
All we ask is a short check-in with your team every week or two. Our members get real
[engineering] experience, and you get a dedicated student team working on a problem you care about.

I have also attached a brief overview of NOBE for your reference. Would you be open to a
20-minute call to talk through what a project could look like? I can send a Calendar Invite
for whatever time works best.

Looking forward to hearing from you!
```

Full rules: `rules/template.md` and `rules/writing-rules.md`.

## The shared brain (no double emails)

Every contact anyone on exec has emailed lives in `brain/contacts/` in this repo, one file per
person. The agent pulls it before every draft and **claims** the contact (commit + push) before
writing a word. If someone else already has that person, you get BLOCKED with who and when. If
two people claim the same person at the same second, git rejects the second push and that
person gets BLOCKED. Contacting the same company again is allowed (a different contact, maybe a
different committee), but the agent shows you who else at that company is already in progress.

Keep statuses current by telling the agent: "sent", "jane@acme.com replied", "call booked with
Acme", "mark Acme dead". It runs `tools/brain.py set`.

**Browse it in Obsidian:** open the folder `brain/vault/` as a vault. It has a Dashboard, one
note per company, and one note per contact, rebuilt every time the agent runs. It is read-only:
edits there get overwritten. Add notes through the agent instead ("note on jane@acme.com: ...").

You need write access to this repo (ask the owner to add you) because claims are pushed.

## Each semester (one person on exec)

Edit `cycle` in `config/nobe.json` (semester, months), run `tests/run_tests.sh`, commit, push.
Everyone else runs `git pull`. The pitch paragraph and checker update from that one file.

## What's in here

```
SKILL.md                 startup + routing (what the agent reads first)
config/nobe.json         semester, NOBE description, CCs, committee deliverables
profile.example.json     what your profile.json looks like
rules/template.md        subject, email skeleton, hook examples per committee
rules/writing-rules.md   banned words, who to email, approval rules
modes/find.md            building a target list
modes/draft.md           research > draft > check > approve
tools/research.py        fetches a company page: summary, headings, emails, links
tools/lint_draft.py      hard-fail checker (format, banned words, fixed lines, length)
tools/brain.py           shared brain: check, claim, set status, list, stale, sync
brain/contacts/          one JSON per contacted person (written only by brain.py)
brain/vault/             Obsidian view of the brain (generated, gitignored)
agents/                  reviewer that reads the draft as the recipient would
tests/                   checker tests (run_tests.sh)
targets/                 your target lists (gitignored, local only)
```

## Rules that never bend

- It never sends email. You send.
- Every fact in the hook comes from a page it actually read.
- No draft without a claim in the shared brain. Same person is never emailed twice.
