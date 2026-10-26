#!/usr/bin/env python3
"""NOBE shared outreach brain client. The brain is a Google Sheet behind an
Apps Script web app (server/Code.gs) owned by one exec member. Nobody else
needs a Google or GitHub account: this tool calls the web app with the shared
key from brain.key (or the NOBE_BRAIN_KEY environment variable).

A contact is CLAIMED before drafting. The server handles one write at a time,
so if two people claim the same email at once the second is told it is taken.
Same person can never be emailed twice. Same company is allowed (different
contact, maybe a different committee) but always warns with who already has it.

brain/vault/ is an Obsidian vault rebuilt from the Sheet on every command
(local only, read-only). Open that folder in Obsidian to browse.

Usage:
    brain.py sync                                  fetch + rebuild vault + summary
    brain.py check EMAIL [--company NAME]          exit 0 new, 3 blocked
    brain.py claim --email E --name N --company C --committee consulting|tech|pd
                   [--role R] [--domain D] [--note TEXT]
    brain.py set EMAIL STATUS [--note TEXT] [--draft-id ID]
    brain.py list [--company C] [--sender S] [--status S] [--committee C]
    brain.py stale [--days 7]                      claims never sent

Statuses: claimed, drafted, sent, replied, call, client, dead, released.
Only 'released' (never sent) frees a contact for someone else.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VAULT = ROOT / "brain" / "vault"
STATUSES = ["claimed", "drafted", "sent", "replied", "call", "client", "dead", "released"]
BLOCKED = 3


class BrainDown(Exception):
    pass


def cfg():
    return json.loads((ROOT / "config" / "nobe.json").read_text())


def sender():
    p = ROOT / "profile.json"
    return json.loads(p.read_text()).get("name", "unknown") if p.exists() else "unknown"


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


# ---------- server ----------

def call(action, **payload):
    url = os.environ.get("NOBE_BRAIN_URL") or cfg().get("brain_url", "")
    key_file = ROOT / "brain.key"
    key = os.environ.get("NOBE_BRAIN_KEY") or (key_file.read_text().strip() if key_file.exists() else "")
    if not url:
        raise BrainDown("no brain_url in config/nobe.json (owner: see server/SETUP.md)")
    if not key:
        raise BrainDown("no brain key. Ask the owner for it and run ./install.sh again")
    body = json.dumps(dict(payload, action=action, key=key)).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        # Apps Script answers a POST with a redirect to the result; urllib follows it as a GET.
        with urllib.request.urlopen(req, timeout=30) as r:
            res = json.loads(r.read().decode())
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise BrainDown(f"cannot reach the brain ({e})")
    if res.get("error") == "bad key":
        raise BrainDown("the brain rejected your key. Ask the owner for the current one")
    return res


def load_all():
    return call("list")["rows"]


# ---------- data ----------

def norm_company(name):
    n = re.sub(r"[^a-z0-9 ]", "", (name or "").lower())
    n = re.sub(r"\b(inc|llc|ltd|corp|corporation|co|company|technologies|technology|labs)\b", "", n)
    return " ".join(n.split())


def domain_of(email):
    return email.split("@", 1)[1].lower() if "@" in email else ""


def find(rows, email):
    email = email.strip().lower()
    return next((r for r in rows if r["email"] == email), None)


def same_company(rows, company, domain, email):
    key = norm_company(company)
    return [r for r in rows if r["email"] != email.strip().lower()
            and ((key and norm_company(r.get("company")) == key) or (domain and r.get("domain") == domain))]


def describe(r):
    return (f"{r['name']} <{r['email']}> | {r.get('company')} | {r.get('committee')} | "
            f"{r.get('status')} | by {r.get('sender')} {str(r.get('updated_at', ''))[:10]}")


def report(rows, email, company):
    """Print the dedupe verdict. Returns True if the contact is blocked."""
    row = find(rows, email)
    blocked = bool(row and row.get("status") != "released")
    if blocked:
        print(f"BLOCKED: already in the brain\n  {describe(row)}")
    elif row:
        print(f"RELEASED earlier (never sent), free to claim\n  {describe(row)}")
    else:
        print(f"NEW: {email} has never been contacted by NOBE")
    others = same_company(rows, company or (row or {}).get("company", ""), domain_of(email), email)
    if others:
        print(f"WARN: {len(others)} other contact(s) at this company. Coordinate before sending:")
        for o in others:
            print(f"  {describe(o)}")
    return blocked


# ---------- vault ----------

def safe(name):
    return re.sub(r'[\\/:*?"<>|#^\[\]]', "", name).strip() or "unknown"


def contact_note(r):
    return safe(f"{r['name']} ({r.get('company', '')})")


def rebuild_vault(rows):
    for sub in ("Companies", "Contacts"):
        d = VAULT / sub
        d.mkdir(parents=True, exist_ok=True)
        for old in d.glob("*.md"):
            old.unlink()
    committees = cfg()["committees"]

    by_company, names = {}, {}
    for r in sorted(rows, key=lambda r: str(r.get("claimed_at", ""))):
        key = norm_company(r.get("company")) or r.get("domain") or "unknown"
        names.setdefault(key, r.get("company") or r.get("domain") or "unknown")
        r = dict(r, company=names[key])
        by_company.setdefault(names[key], []).append(r)
        hist = "\n".join(f"- {h['at']} **{h['status']}** by {h['by']}" + (f": {h['note']}" if h.get("note") else "")
                         for h in r.get("history", []))
        (VAULT / "Contacts" / f"{contact_note(r)}.md").write_text(
            f"---\nemail: {r['email']}\ncompany: \"{r.get('company', '')}\"\nrole: \"{r.get('role', '')}\"\n"
            f"committee: {r.get('committee')}\nstatus: {r.get('status')}\nsender: \"{r.get('sender')}\"\n"
            f"tags: [nobe-contact, {r.get('status')}]\n---\n"
            f"# {r['name']}\n\n{r.get('role', '')} at [[{safe(r.get('company') or 'unknown')}]]\n\n"
            f"Committee: {committees.get(r.get('committee'), {}).get('name', r.get('committee'))}\n\n"
            f"## History\n{hist}\n\n## Notes\n{r.get('notes', '')}\n")

    for company, rs in by_company.items():
        coms = sorted({r.get("committee") for r in rs})
        lines = "\n".join(f"| [[{contact_note(r)}]] | {r.get('role', '')} | {r.get('committee')} | "
                          f"{r.get('status')} | {r.get('sender')} | {str(r.get('updated_at', ''))[:10]} |" for r in rs)
        (VAULT / "Companies" / f"{safe(company)}.md").write_text(
            f"---\ncommittees: [{', '.join(coms)}]\ncontacts: {len(rs)}\ntags: [nobe-company]\n---\n"
            f"# {company}\n\n| Contact | Role | Committee | Status | Sender | Updated |\n|---|---|---|---|---|---|\n{lines}\n")

    count = lambda key: {k: sum(1 for r in rows if r.get(key) == k) for k in sorted({r.get(key) for r in rows})}
    recent = sorted(rows, key=lambda r: str(r.get("updated_at", "")), reverse=True)[:25]
    (VAULT / "Dashboard.md").write_text(
        f"# NOBE Outreach Brain\n\nRebuilt {now()} from the shared brain (do not edit this vault, "
        f"it is regenerated on every sync).\n\n"
        f"**{len(rows)} contacts at {len(by_company)} companies**\n\n"
        f"By status: {count('status')}\n\nBy committee: {count('committee')}\n\nBy sender: {count('sender')}\n\n"
        f"## Most recent\n" + "\n".join(f"- {str(r.get('updated_at', ''))[:10]} [[{contact_note(r)}]] "
                                       f"{r.get('status')} ({r.get('committee')}, {r.get('sender')})" for r in recent) + "\n")


# ---------- commands ----------

def cmd_sync(a):
    rows = load_all()
    rebuild_vault(rows)
    print(f"brain: {len(rows)} contacts | vault: {VAULT}")
    return 0


def cmd_check(a):
    return BLOCKED if report(load_all(), a.email, a.company) else 0


def cmd_claim(a):
    if a.committee not in cfg()["committees"]:
        print(f"unknown committee {a.committee!r}")
        return 2
    email = a.email.strip().lower()
    rows = load_all()
    if report(rows, email, a.company):
        return BLOCKED
    # reuse the spelling already in the brain so one company stays one company
    match = same_company(rows, a.company, domain_of(email), email)
    company = match[0]["company"] if match else a.company
    by, at = sender(), now()
    row = {"email": email, "name": a.name, "role": a.role or "", "company": company,
           "domain": a.domain or domain_of(email), "committee": a.committee, "sender": by,
           "status": "claimed", "claimed_at": at, "updated_at": at, "gmail_draft_id": "",
           "notes": a.note or "", "history": [{"at": at, "by": by, "status": "claimed", "note": a.note or ""}]}
    res = call("claim", row=row)
    if res.get("blocked"):
        print(f"BLOCKED: someone claimed this contact a moment ago.\n  {describe(res['row'])}")
        return BLOCKED
    if not res.get("ok"):
        print(f"Claim failed: {res.get('error')}. Not claimed, do not draft.")
        return BLOCKED
    rebuild_vault(load_all())
    print(f"CLAIMED: {email} for {by} ({a.committee}). Go ahead and draft.")
    return 0


def cmd_set(a):
    if a.status not in STATUSES:
        print(f"status must be one of {', '.join(STATUSES)}")
        return 2
    res = call("set", email=a.email.strip().lower(), status=a.status, note=a.note or "",
               draft_id=a.draft_id or "", by=sender(), at=now())
    if not res.get("ok"):
        print(f"Not updated: {res.get('error')}")
        return 1
    rebuild_vault(load_all())
    print(f"{a.email}: {a.status}")
    return 0


def cmd_list(a):
    rows = load_all()
    for key in ("status", "committee"):
        if getattr(a, key):
            rows = [r for r in rows if r.get(key) == getattr(a, key)]
    if a.company:
        rows = [r for r in rows if norm_company(a.company) in norm_company(r.get("company"))]
    if a.sender:
        rows = [r for r in rows if a.sender.lower() in r.get("sender", "").lower()]
    for r in sorted(rows, key=lambda r: (r.get("company", ""), r["email"])):
        print(describe(r))
    print(f"--- {len(rows)} contacts")
    return 0


def cmd_stale(a):
    today = date.today()
    stale = [r for r in load_all() if r.get("status") in ("claimed", "drafted")
             and (today - datetime.strptime(str(r["updated_at"])[:10], "%Y-%m-%d").date()).days >= a.days]
    for r in stale:
        print(describe(r))
    print(f"--- {len(stale)} claimed/drafted {a.days}+ days ago and never sent. "
          f"Send them, or 'set EMAIL released' so someone else can.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("sync")
    p = sub.add_parser("check"); p.add_argument("email"); p.add_argument("--company")
    p = sub.add_parser("claim")
    for f in ("email", "name", "company", "committee"):
        p.add_argument(f"--{f}", required=True)
    for f in ("role", "domain", "note"):
        p.add_argument(f"--{f}")
    p = sub.add_parser("set"); p.add_argument("email"); p.add_argument("status")
    p.add_argument("--note"); p.add_argument("--draft-id")
    p = sub.add_parser("list")
    for f in ("company", "sender", "status", "committee"):
        p.add_argument(f"--{f}")
    p = sub.add_parser("stale"); p.add_argument("--days", type=int, default=7)
    a = ap.parse_args()
    try:
        return {"sync": cmd_sync, "check": cmd_check, "claim": cmd_claim, "set": cmd_set,
                "list": cmd_list, "stale": cmd_stale}[a.cmd](a)
    except BrainDown as e:
        print(f"BRAIN UNAVAILABLE: {e}\nDrafting is blocked until this works, so no one gets emailed twice.")
        return BLOCKED


if __name__ == "__main__":
    sys.exit(main())
