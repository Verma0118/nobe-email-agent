#!/usr/bin/env python3
"""Hard-fail checker for NOBE outreach drafts. Mechanical rules only; the
nobe-email-reviewer agent still judges the hook, warmth, and truth.

Draft file format:
    Subject: <subject line>
    <blank line>
    <body, plain text or HTML>

Usage:
    lint_draft.py DRAFT --committee consulting|tech|pd [--profile profile.json] [--config config/nobe.json]
Exit 0 = PASS (warnings allowed), 1 = FAIL, 2 = usage error.

The subject label, semester, and the fixed pitch paragraph are built from
config/nobe.json, so a new semester only needs a config change.
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIN_WORDS, MAX_WORDS = 110, 200

BANNED = [
    "leverage", "synergy", "alignment", "value-add", "at the intersection of", "ecosystem",
    "cutting-edge", "thought leader", "caught my eye", "caught my attention",
    "piqued my interest", "i was struck by", "couldn't help but notice",
    "could not help but notice", "delve", "unpack", "deep dive", "reach out", "reaching out",
    "finds you well", "i hope all is well", "passionate about", "excited to", "would love to",
    "i serve as", "what draws me to", "p.s.",
]
WARN_WORDS = ["align", "solutions", "innovative", "free"]

CONTRACTION = re.compile(
    r"\b\w+n['’]t\b|\b\w+['’](m|re|ve|ll|d)\b|\b(it|that|there|what|here|let|he|she|who|where|how)['’]s\b",
    re.I)
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")
ATTACH_LINE = "I have also attached a brief overview of NOBE for your reference."


def pitch(cfg, committee):
    c, com = cfg["cycle"], cfg["committees"][committee]
    return (f"We propose a {c['weeks']}-week project from {c['start_month']} to {c['end_month']}, "
            f"with an option to continue into {c['extension']}. All we ask is a short check-in with "
            f"your team every week or two. Our members get real {com['experience']} experience, and "
            f"you get a dedicated student team working on a problem you care about.")


def to_text(body):
    body = re.sub(r"(?i)<br\s*/?>|</p>|</div>", "\n", body)
    body = re.sub(r"<[^>]+>", "", body)
    return html.unescape(body)


def split_draft(raw):
    lines = raw.strip("\n").splitlines()
    if not lines or not lines[0].lower().startswith("subject:"):
        return None, raw
    return lines[0].split(":", 1)[1].strip(), "\n".join(lines[1:]).strip("\n")


def split_signature(text):
    """Return (greeting, middle, signature). Signature starts at a line 'Best,'."""
    lines = [l.rstrip() for l in text.strip().splitlines()]
    sig_at = next((i for i, l in enumerate(lines) if l.strip().lower() in ("best,", "best")), len(lines))
    first = next((i for i, l in enumerate(lines) if l.strip()), 0)
    greeting = lines[first] if lines else ""
    return greeting, "\n".join(lines[first + 1:sig_at]), "\n".join(lines[sig_at:])


def sentences(text):
    flat = " ".join(text.split())
    return [s for s in re.split(r"(?<=[.!?])\s+", flat) if s]


def lint(raw, committee, cfg, profile):
    fails, warns = [], []
    com = cfg["committees"][committee]
    subject, body_raw = split_draft(raw)
    text = to_text(body_raw)
    greeting, middle, signature = split_signature(text)
    visible = f"{greeting}\n{middle}"
    low = " ".join(visible.lower().split())

    # subject
    want = rf"^[^|]+ x NOBE \| {re.escape(com['subject_label'])}, {re.escape(cfg['cycle']['semester'])}$"
    if subject is None:
        fails.append("no 'Subject:' first line")
    elif not re.match(want, subject):
        fails.append(f"subject must be '[Company] x NOBE | {com['subject_label']}, "
                     f"{cfg['cycle']['semester']}', got {subject!r}")

    # greeting: named or generic, Morning/Afternoon, ends with '!'
    if not re.fullmatch(r"Good (Morning|Afternoon)( [A-Z][\w.'’-]*( [A-Z][\w.'’-]*)?)?!", greeting.strip()):
        fails.append(f"greeting {greeting.strip()!r} must be 'Good Morning [Name]!' or 'Good Morning!'")

    # punctuation and format
    if "—" in text:
        fails.append("em dash (—) found")
    if re.search(r"\s[-–]\s", visible):
        fails.append("hyphen/en dash used as a clause connector ( - )")
    if ";" in visible:
        fails.append("semicolon found")
    for m in CONTRACTION.finditer(visible):
        fails.append(f"contraction: {m.group(0)!r}")
    if re.search(r"(?m)^\s*([-*•]|\d+\.)\s+", middle):
        fails.append("bullet or numbered list in body")
    if re.search(r"\*\*|<b>|<strong>", body_raw, re.I):
        fails.append("bold text in body")
    if EMOJI.search(visible) or (subject and EMOJI.search(subject)):
        fails.append("emoji found")
    if re.search(r"https?://", visible):
        fails.append("bare URL in visible text (use an <a href> with display text)")

    # language
    for phrase in BANNED + [b.lower() for b in cfg.get("banned_extra", [])]:
        if re.search(r"(?<!\w)" + re.escape(phrase.lower()) + r"(?!\w)", low):
            fails.append(f"banned phrase: {phrase!r}")
    for w in WARN_WORDS:
        if re.search(rf"\b{w}\w*\b", low):
            warns.append(f"check usage of {w!r}")

    # fixed lines
    for req in (pitch(cfg, committee), ATTACH_LINE):
        if " ".join(req.lower().split()) not in low:
            fails.append(f"missing or edited fixed line: {req!r}")
    for other, ocom in cfg["committees"].items():
        if other != committee and ocom["subject_label"].lower() in low:
            warns.append(f"mentions another committee's label {ocom['subject_label']!r}")

    # "I" streak
    streak = best = 0
    for s in sentences(middle):
        streak = streak + 1 if re.match(r"I\b", s) else 0
        best = max(best, streak)
    if best > 2:
        fails.append(f"{best} consecutive sentences start with 'I' (max 2)")

    # CTA
    if re.search(r"\bzoom\b", low):
        fails.append("mentions Zoom; the CTA is a Calendar Invite")
    if "calendar invite" not in low:
        fails.append("missing CTA: 'Calendar Invite'")

    # signature
    if not signature:
        fails.append("no signature block (starts with 'Best,')")
    else:
        for key in ("name", "sending_email"):
            val = profile.get(key)
            if val and val not in signature:
                fails.append(f"signature missing profile {key} {val!r}")
        if "NOBE" not in signature:
            fails.append("signature missing the '<role>, NOBE at UIUC' line")

    # length
    words = len(re.findall(r"[A-Za-z0-9][\w'’.-]*", middle))
    if not MIN_WORDS <= words <= MAX_WORDS:
        fails.append(f"body is {words} words; needs {MIN_WORDS}-{MAX_WORDS}")
    return fails, warns, words


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("draft")
    ap.add_argument("--committee", required=True)
    ap.add_argument("--profile", default=str(ROOT / "profile.json"))
    ap.add_argument("--config", default=str(ROOT / "config" / "nobe.json"))
    a = ap.parse_args()

    cfg = json.loads(Path(a.config).expanduser().read_text())
    if a.committee not in cfg["committees"]:
        print(f"unknown committee {a.committee!r}; known: {', '.join(cfg['committees'])}")
        return 2
    prof_path = Path(a.profile).expanduser()
    if not prof_path.exists():
        print(f"no profile at {prof_path}; run install.sh or start the agent once to create it")
        return 2
    profile = json.loads(prof_path.read_text())
    fails, warns, words = lint(Path(a.draft).read_text(), a.committee, cfg, profile)
    for f in fails:
        print(f"FAIL  {f}")
    for w in warns:
        print(f"WARN  {w}")
    print(f"RESULT: {'FAIL' if fails else 'PASS'} ({a.committee}, {words} words, "
          f"{len(fails)} fail, {len(warns)} warn)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
