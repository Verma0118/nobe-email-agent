#!/usr/bin/env python3
"""Builds lint fixtures from config/nobe.json, so they stay valid when the cycle changes.
Writes one pass__<committee>__good.txt per committee and fail__* variants of the pd draft."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))
from lint_draft import ATTACH_LINE, pitch  # noqa: E402

cfg = json.loads((HERE.parent / "config" / "nobe.json").read_text())
HOOKS = {
    "consulting": "I saw that Prairie Heat is moving its thermal batteries from pilot sites into commercial customers this year. Our consulting team could put together a market-sizing study on which industrial heat users in the Midwest would be the best first customers, with the interview notes behind it.",
    "tech": "I noticed that FieldLens publishes field data from its rover runs as downloadable reports. Our software team could build a web dashboard that lets growers compare runs across plots and seasons, connected to the data format you already export.",
    "pd": "I saw that Acme Robotics recently launched a new version of its gripper. Our engineering team could take one subsystem, such as the finger joint or the wrist mount, and deliver a CAD redesign focused on part count and cost, with 3D-printed prototypes for your team to test.",
}
COMPANY = {"consulting": "Prairie Heat", "tech": "FieldLens", "pd": "Acme Robotics"}


def draft(com):
    return f"""Subject: {COMPANY[com]} x NOBE x {cfg['committees'][com]['subject_label']}

Good Morning Sam!

I hope your week has been off to a good start!

My name is Jordan Lee, a Junior studying Mechanical Engineering at the University of Illinois Urbana-Champaign. I am a Project Manager at NOBE (National Organization for Business and Engineering), a student business and engineering organization on campus.

{HOOKS[com]}

{pitch(cfg, com)}

{ATTACH_LINE} Would you be open to a 20-minute call to talk through what a project could look like? I can send a Calendar Invite for whatever time works best.

Looking forward to hearing from you!

Best,
Jordan Lee
Project Manager, NOBE at UIUC
B.S. Mechanical Engineering
<a href="https://www.linkedin.com/in/jordanlee/">www.linkedin.com/in/jordanlee</a>
jlee@illinois.edu
"""


FAILS = {
    "em_dash": lambda d: d.replace("this year.", "this year — and growing.").replace("recently launched", "recently — launched"),
    "contraction": lambda d: d.replace("I am a Project", "I'm a Project"),
    "old_subject_format": lambda d: d.replace("x NOBE x Product Development Project", "x NOBE | Engineering Project, Fall 2026"),
    "wrong_committee_label": lambda d: d.replace("Product Development Project", "Tech Project"),
    "old_pitch_months": lambda d: d.replace(cfg["cycle"]["start_month"] + " to", "September to"),
    "edited_pitch": lambda d: d.replace("All we ask is", "We just need"),
    "no_attach_line": lambda d: d.replace(ATTACH_LINE + " ", ""),
    "hi_greeting": lambda d: d.replace("Good Morning Sam!", "Hi Sam,"),
    "banned_phrase": lambda d: d.replace("I hope your week has been off to a good start!", "I wanted to reach out about a project."),
    "cozad": lambda d: d.replace("organization on campus.", "organization on campus that competes in COZAD."),
    "bare_url": lambda d: d.replace("to test.", "to test, see https://acme.example."),
    "zoom_cta": lambda d: d.replace("I can send a Calendar Invite", "I can send a Zoom link"),
    "no_signature_nobe": lambda d: d.replace("Project Manager, NOBE at UIUC\n", ""),
}

out = HERE / "fixtures"
out.mkdir(exist_ok=True)
for com in HOOKS:
    (out / f"pass__{com}__good.txt").write_text(draft(com))
(out / "pass__pd__generic_greeting.txt").write_text(draft("pd").replace("Good Morning Sam!", "Good Morning!"))
for name, fn in FAILS.items():
    (out / f"fail__pd__{name}.txt").write_text(fn(draft("pd")))
print(f"wrote {len(list(out.glob('*.txt')))} fixtures")
