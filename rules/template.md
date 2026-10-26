# NOBE Client Outreach Template

One template for all three committees. The skeleton never changes. Only the hook paragraph and
the subject label change by committee. `{field}` values come from `profile.json` (the sender) and
`config/nobe.json` (the org, the cycle, the committee).

## Subject

```
[Company] x NOBE x [Committee] Project
```
The last part is the committee this contact's project belongs to:
- `Acme Robotics x NOBE x Product Development Project`
- `Prairie Heat x NOBE x Consulting Project`
- `FieldLens x NOBE x Tech Project`

Pick the committee per contact, not per company. A big company can get a Tech email to an
engineering manager and a Consulting email to a strategy lead, as separate contacts. Lowercase
"x", single spaces, nothing else in the line.

## Body (110-200 words between greeting and signature)

```
Good Morning [First Name]!

I hope your week has been off to a good start!

My name is {name}, a {year} studying {major} at the University of Illinois Urbana-Champaign.
I am a {nobe_role} at NOBE ({org.full_name}), a student business and engineering
organization on campus.

[HOOK PARAGRAPH, 2-3 sentences. See "Hook" below.]

We propose a {cycle.weeks}-week project from {cycle.start_month} to {cycle.end_month}, with an
option to continue into {cycle.extension}. All we ask is a short check-in with your team every
week or two. Our members get real {committee.experience} experience, and you get a dedicated
student team working on a problem you care about.

I have also attached a brief overview of NOBE for your reference. Would you be open to a
20-minute call to talk through what a project could look like? I can send a Calendar Invite
for whatever time works best.

Looking forward to hearing from you!

Best,
{name}
{nobe_role}, NOBE at UIUC
{degree_line}
<a href="{linkedin_url}">{linkedin_display}</a>
{phone} | {sending_email}
```

The pitch paragraph and the line "I have also attached a brief overview of NOBE for your
reference." are fixed. `tools/lint_draft.py` fails the draft if either is changed.

## Greeting

- Named person (founder@, firstname@, a person found on the team page): `Good Morning [First Name]!`
- Generic inbox (info@, hello@, team@, contact@): `Good Morning!` with no name.
- Before 12pm: Morning. From 12pm: Afternoon. If the draft will be schedule-sent at 8am, use Morning.
- The warm line after the greeting rotates: "I hope your week has been off to a good start!",
  "I hope you are having a good week!", "Hope your week is going well!"

## Hook (the only paragraph written fresh every time)

Examples below use made-up companies. Never copy their facts into a real email.

Pattern: one sourced fact about the company, then one concrete thing the committee could build or
deliver for them. Name the deliverable. "Help with your product" is not a deliverable.

**Consulting** (market, strategy, operations):
> I saw that Prairie Heat is moving its thermal batteries from pilot sites into commercial
> customers this year. Our consulting team could put together a market-sizing study on which
> industrial heat users in the Midwest would be the best first customers, with the interview
> notes behind it.

**Tech** (software):
> I noticed that FieldLens publishes field data from its rover runs as downloadable reports.
> Our software team could build a web dashboard that lets growers compare runs across plots
> and seasons, connected to the data format you already export.

**Product Development** (hardware, CAD, testing):
> I saw that Acme Robotics recently launched a new version of its gripper. Our engineering team
> could take one subsystem, such as the finger joint or the wrist mount, and deliver a CAD
> redesign focused on part count and cost, with 3D-printed prototypes for your team to test.

Rules:
- The fact comes from a page you actually fetched (`tools/research.py`). Keep the URL in the brief.
- Warmth test: swap in a competitor's name. If the paragraph still works, it is too generic.
- Champaign-Urbana or Research Park company: say so ("Since you are right here in Research Park,
  our team could meet with yours in person."). Proximity is the strongest signal NOBE has.
- Never promise outcomes ("we will cut your costs by 20%"). Offer the work, not the result.
- Past NOBE client: replace the hook with "Our team worked with you on [project] last
  [semester], and we would like to offer a follow-on project this {semester}."

## Never

- COZAD or competition talk. This is client outreach.
- Personal resume, personal portfolio, or other clubs. The email is about NOBE.
- "free", "unpaid", "free labor". Say "dedicated student team".
- More than one ask. The ask is the 20-minute call with a Calendar Invite.
