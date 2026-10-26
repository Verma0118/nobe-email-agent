# NOBE Email Agent

A Claude Code agent that finds client companies and drafts outreach emails for NOBE's three
committees: **Consulting**, **Tech**, and **Product Development**. It researches the company,
writes the email in NOBE's standard format, checks it, and hands it to you. It never sends anything.

## Setup (5 minutes, once)

You need:
- [Claude Code](https://claude.com/claude-code) installed and signed in (a Claude Pro account).
- The **brain key**, sent to you privately by whoever runs the agent for NOBE.

No GitHub account needed. Paste this in Terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/Verma0118/nobe-email-agent/main/get.sh | bash
```

It downloads the agent to `~/nobe-email-agent`, asks for the brain key, and sets everything up.
**To update later, run the same command.** Your profile and key are kept.

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

Every contact anyone at NOBE has emailed lives in one shared brain: a Google Sheet the owner
runs, reached over the internet with the brain key. Nobody else needs a Google or GitHub account.
Before writing a word, the agent **claims** the contact. If someone already has that person, you
get BLOCKED with who and when. The server handles one claim at a time, so if two people claim the
same person at the same second, one wins and the other is BLOCKED. If the brain cannot be reached
(no internet, wrong key), drafting is blocked rather than risking a double email.

Contacting the same company again is allowed (a different contact, maybe a different committee),
but the agent shows you who else at that company is already in progress.

Keep statuses current by telling the agent: "sent", "jane@acme.com replied", "call booked with
Acme", "mark Acme dead". It runs `tools/brain.py set`.

**Browse it in Obsidian:** open the folder `brain/vault/` as a vault. It has a Dashboard, one
note per company, and one note per contact, rebuilt every time the agent runs. It is read-only:
edits there get overwritten. Add notes through the agent instead ("note on jane@acme.com: ...").

## Each semester (one person on exec)

The owner edits `cycle` in `config/nobe.json` (semester, months), runs `tests/run_tests.sh`, and
pushes. Everyone else reruns the install command to update. The pitch paragraph and checker
update from that one file.

## Owner setup (once)

The brain server is a Google Sheet with a small script. Steps: `server/SETUP.md`. Then put the
web app URL in `config/nobe.json` as `brain_url`, and send the key to exec privately.

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
brain/vault/             Obsidian view of the brain (generated, local only)
server/                  the brain server (Google Apps Script) + owner setup steps
get.sh / install.sh      one-line install and update, no git needed
agents/                  reviewer that reads the draft as the recipient would
tests/                   checker + brain tests (run_tests.sh, uses a local fake server)
targets/                 your target lists (gitignored, local only)
```

## Rules that never bend

- It never sends email. You send.
- Every fact in the hook comes from a page it actually read.
- No draft without a claim in the shared brain. Same person is never emailed twice.
