#!/usr/bin/env python3
"""NOBE shared outreach brain. One JSON file per contact in brain/contacts/,
synced through this git repo so every exec member sees every claim.

A contact is CLAIMED before drafting: the claim is committed and pushed. If two
people claim the same email at once, git rejects the second push, the tool
pulls, sees the claim, and refuses. Same person can never be emailed twice.
Same company is allowed (different contact, maybe a different committee) but
always warns with who already has it.

brain/vault/ is an Obsidian vault rebuilt from the JSON on every command
(gitignored, never conflicts). Open that folder in Obsidian to browse.

Usage:
    brain.py sync                                  pull + rebuild vault + summary
    brain.py check EMAIL [--company NAME]          exit 0 new, 3 blocked
    brain.py claim --email E --name N --company C --committee consulting|tech|pd
                   [--role R] [--domain D] [--note TEXT]
    brain.py set EMAIL STATUS [--note TEXT] [--draft-id ID]
    brain.py list [--company C] [--sender S] [--status S] [--committee C]
    brain.py stale [--days 7]                      claims never sent
    brain.py import FILE.json                      seed rows (list of contact dicts)

Statuses: claimed, drafted, sent, replied, call, client, dead, released.
Only 'released' (never sent) frees a contact for someone else.
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRAIN = ROOT / "brain"
CONTACTS = BRAIN / "contacts"
VAULT = BRAIN / "vault"
STATUSES = ["claimed", "drafted", "sent", "replied", "call", "client", "dead", "released"]
BLOCKED = 3


def cfg():
    return json.loads((ROOT / "config" / "nobe.json").read_text())


def sender():
    p = ROOT / "profile.json"
    return json.loads(p.read_text()).get("name", "unknown") if p.exists() else "unknown"


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


# ---------- git ----------

def git(*args, check=True):
    r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr.strip() or r.stdout.strip()}")
    return r


def has_remote():
    return bool(git("remote", check=False).stdout.strip())


def pull():
    """Pull latest claims. Returns False if a remote exists but cannot be reached."""
    if not has_remote():
        return True
    r = git("pull", "--rebase", "--autostash", "-q", check=False)
    if r.returncode:
        git("rebase", "--abort", check=False)
        print(f"PULL FAILED: {r.stderr.strip()}")
        return False
    return True


def commit_and_push(path, message):
    """Commit one contact file and push. Returns 'ok', 'conflict', or 'offline'."""
    git("add", str(path))
    git("commit", "-q", "-m", message)
    if not has_remote():
        return "ok"
    for _ in range(3):
        if not git("push", "-q", check=False).returncode:
            return "ok"
        r = git("pull", "--rebase", "-q", check=False)
        if r.returncode:  # same file changed remotely: someone else got there first
            git("rebase", "--abort", check=False)
            git("reset", "--keep", "HEAD~1", check=False)
            pull()
            return "conflict"
    git("reset", "--keep", "HEAD~1", check=False)
    return "offline"


# ---------- data ----------

def slug(email):
    return re.sub(r"[^a-z0-9._-]", "_", email.strip().lower().replace("@", "_at_"))


def norm_company(name):
    n = re.sub(r"[^a-z0-9 ]", "", (name or "").lower())
    n = re.sub(r"\b(inc|llc|ltd|corp|corporation|co|company|technologies|technology|labs)\b", "", n)
    return " ".join(n.split())


def domain_of(email):
    return email.split("@", 1)[1].lower() if "@" in email else ""


def load_all():
    rows = []
    for f in sorted(CONTACTS.glob("*.json")):
        try:
            rows.append(json.loads(f.read_text()))
        except json.JSONDecodeError:
            print(f"WARN: unreadable {f.name}")
    return rows


def find(email):
    f = CONTACTS / f"{slug(email)}.json"
    return (json.loads(f.read_text()), f) if f.exists() else (None, f)


def same_company(rows, company, domain, email):
    key = norm_company(company)
    return [r for r in rows if r["email"].lower() != email.lower()
            and ((key and norm_company(r.get("company")) == key) or (domain and r.get("domain") == domain))]


def describe(r):
    return (f"{r['name']} <{r['email']}> | {r.get('company')} | {r.get('committee')} | "
            f"{r.get('status')} | by {r.get('sender')} {r.get('updated_at', '')[:10]}")


def report(email, company):
    """Print the dedupe verdict. Returns True if the contact is blocked."""
    row, _ = find(email)
    blocked = bool(row and row.get("status") != "released")
    if blocked:
        print(f"BLOCKED: already in the brain\n  {describe(row)}")
    elif row:
        print(f"RELEASED earlier (never sent), free to claim\n  {describe(row)}")
    else:
        print(f"NEW: {email} has never been contacted by NOBE")
    others = same_company(load_all(), company or (row or {}).get("company", ""), domain_of(email), email)
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
    for r in sorted(rows, key=lambda r: r.get("claimed_at", "")):
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
                          f"{r.get('status')} | {r.get('sender')} | {r.get('updated_at', '')[:10]} |" for r in rs)
        (VAULT / "Companies" / f"{safe(company)}.md").write_text(
            f"---\ncommittees: [{', '.join(coms)}]\ncontacts: {len(rs)}\ntags: [nobe-company]\n---\n"
            f"# {company}\n\n| Contact | Role | Committee | Status | Sender | Updated |\n|---|---|---|---|---|---|\n{lines}\n")

    count = lambda key: {k: sum(1 for r in rows if r.get(key) == k) for k in sorted({r.get(key) for r in rows})}
    recent = sorted(rows, key=lambda r: r.get("updated_at", ""), reverse=True)[:25]
    (VAULT / "Dashboard.md").write_text(
        f"# NOBE Outreach Brain\n\nRebuilt {now()} from brain/contacts/ (do not edit this vault, "
        f"it is regenerated on every sync).\n\n"
        f"**{len(rows)} contacts at {len(by_company)} companies**\n\n"
        f"By status: {count('status')}\n\nBy committee: {count('committee')}\n\nBy sender: {count('sender')}\n\n"
        f"## Most recent\n" + "\n".join(f"- {r.get('updated_at', '')[:10]} [[{contact_note(r)}]] "
                                       f"{r.get('status')} ({r.get('committee')}, {r.get('sender')})" for r in recent) + "\n")


# ---------- commands ----------

def write_row(row, path, message):
    CONTACTS.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(row, indent=2, ensure_ascii=False) + "\n")
    return commit_and_push(path, message)


def cmd_sync(a):
    ok = pull()
    rows = load_all()
    rebuild_vault(rows)
    print(f"brain: {len(rows)} contacts{'' if ok else ' (OFFLINE, may be stale)'} | vault: {VAULT}")
    return 0 if ok else 1


def cmd_check(a):
    if not pull():
        print("Cannot reach the shared brain. Do not draft until sync works.")
        return BLOCKED
    return BLOCKED if report(a.email, a.company) else 0


def cmd_claim(a):
    if a.committee not in cfg()["committees"]:
        print(f"unknown committee {a.committee!r}")
        return 2
    if not pull():
        print("Cannot reach the shared brain, so the claim cannot be guaranteed. Not claiming.")
        return BLOCKED
    a.email = a.email.strip().lower()
    if report(a.email, a.company):
        return BLOCKED
    # reuse the spelling already in the brain so one company stays one company
    match = same_company(load_all(), a.company, domain_of(a.email), a.email)
    company = match[0]["company"] if match else a.company
    by, at = sender(), now()
    old, path = find(a.email)
    history = (old or {}).get("history", []) + [{"at": at, "by": by, "status": "claimed", "note": a.note or ""}]
    row = {"email": a.email, "name": a.name, "role": a.role or "", "company": company,
           "domain": a.domain or domain_of(a.email), "committee": a.committee, "sender": by,
           "status": "claimed", "claimed_at": at, "updated_at": at, "gmail_draft_id": "",
           "notes": a.note or "", "history": history}
    result = write_row(row, path, f"brain: {by} claims {a.email} ({company}, {a.committee})")
    if result == "conflict":
        print("BLOCKED: someone claimed this contact a moment ago.")
        report(a.email, a.company)
        return BLOCKED
    if result == "offline":
        print("Push failed. Claim NOT saved. Check your connection and try again.")
        return BLOCKED
    rebuild_vault(load_all())
    print(f"CLAIMED: {a.email} for {by} ({a.committee}). Go ahead and draft.")
    return 0


def cmd_set(a):
    if a.status not in STATUSES:
        print(f"status must be one of {', '.join(STATUSES)}")
        return 2
    if not pull():
        return 1
    row, path = find(a.email)
    if not row:
        print(f"{a.email} is not in the brain. Claim it first.")
        return 1
    if a.status == "released" and row["status"] not in ("claimed", "drafted"):
        print(f"cannot release: status is {row['status']} (already sent). It stays blocked.")
        return 1
    by, at = sender(), now()
    row.update(status=a.status, updated_at=at)
    if a.draft_id:
        row["gmail_draft_id"] = a.draft_id
    if a.note:
        row["notes"] = (row.get("notes", "") + f"\n{at[:10]} {by}: {a.note}").strip()
    row.setdefault("history", []).append({"at": at, "by": by, "status": a.status, "note": a.note or ""})
    result = write_row(row, path, f"brain: {a.email} -> {a.status} by {by}")
    if result != "ok":
        print("Update not saved (someone changed this contact at the same time). Run it again.")
        return 1
    rebuild_vault(load_all())
    print(f"{a.email}: {a.status}")
    return 0


def cmd_list(a):
    pull()
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
    pull()
    today = date.today()
    stale = [r for r in load_all() if r.get("status") in ("claimed", "drafted")
             and (today - datetime.strptime(r["updated_at"][:10], "%Y-%m-%d").date()).days >= a.days]
    for r in stale:
        print(describe(r))
    print(f"--- {len(stale)} claimed/drafted {a.days}+ days ago and never sent. "
          f"Send them, or 'set EMAIL released' so someone else can.")
    return 0


def cmd_import(a):
    if not pull():
        return 1
    rows, added = json.loads(Path(a.file).read_text()), 0
    CONTACTS.mkdir(parents=True, exist_ok=True)
    for r in rows:
        r["email"] = r["email"].strip().lower()
        existing, path = find(r["email"])
        if existing:
            continue
        r.setdefault("domain", domain_of(r["email"]))
        r.setdefault("history", [{"at": r.get("updated_at", now()), "by": r.get("sender", "import"),
                                  "status": r["status"], "note": "imported"}])
        path.write_text(json.dumps(r, indent=2, ensure_ascii=False) + "\n")
        git("add", str(path))
        added += 1
    if added:
        git("commit", "-q", "-m", f"brain: import {added} contacts")
        if has_remote() and git("push", "-q", check=False).returncode:
            print("push failed; run 'git pull --rebase && git push'")
    rebuild_vault(load_all())
    print(f"imported {added}, skipped {len(rows) - added} already present")
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
    p = sub.add_parser("import"); p.add_argument("file")
    a = ap.parse_args()
    return {"sync": cmd_sync, "check": cmd_check, "claim": cmd_claim, "set": cmd_set,
            "list": cmd_list, "stale": cmd_stale, "import": cmd_import}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
