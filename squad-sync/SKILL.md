---
name: squad-sync
description: "Finds a time a group of friends can actually meet, by turning each person's calendar into a short share code that reveals only free and busy — never what anyone is doing. Use this whenever the student wants to get a group together and is stuck on when: a study group, a project team, a gym session, a ride share, dinner with friends, office hours with a classmate, or any 'when is everyone free' / 'we keep trying to find a time' / 'nobody answers the group chat' moment. Also use it when the student has been asked for their availability and does not want to hand over their whole calendar, or when a group has been going back and forth for days. Different from study-plan-builder: that plans one student's solo study time, this negotiates a shared time across several people's calendars without any of them publishing what is on it."
license: Apache-2.0
compatibility: "Python 3.9+ (standard library only — nothing to install)"
metadata:
  project: CampusOS
---

# squad-sync

Four friends try to find two hours this week. Someone says "I'm free whenever", someone
screenshots their calendar, two people never answer, and it dies. A week later nobody has met.

squad-sync fixes the part that actually breaks: **sharing when you are free should not mean
sharing what you are doing.** Each person's calendar becomes one short line of text — day
numbers and times, nothing else — and the student pastes that into the group chat. Paste the
replies back and this finds the overlap.

```
SQSY1 TZ:America/Phoenix W:2026-10-26 L:busy B:1-0900-1015,1-1400-1600,3-1800-1900 X:313e
```

That is a whole week of availability. No event names. No places. No people. No reasons. "Busy
Wednesday 6–7pm" is in there; "therapy Wednesday 6pm" cannot be, because the code has nowhere
to put it.

## When to use this

The student wants a group together and the blocker is *when*. Study group, project team,
gym, carpool, dinner, rehearsal. Also when someone has asked the student for their
availability and they would rather not forward their calendar.

**Not** for planning one student's own study time — Cubbie's built-in `study-plan-builder`
does that, and it does it better. This one is for the case where other people's calendars
are involved and nobody wants to publish theirs.

## Setup

None. The script uses only the Python standard library — no install, no account, no key, no
network. If Python is missing, say so and fall back to the no-script path below.

## The workflow

### 1. Work out the week and how long they need

Ask once, with a default they can accept by saying yes:

> "Which week — this one or next? And how long do you need, 2 hours?"

The week is always anchored to its **Monday**. If today is Wednesday and they say "this week",
use the Monday just past.

### 2. Collect the student's own busy times

Read the student's **Google Calendar** for that week, and their **Canvas** assignments and
class meetings. Anything that blocks time becomes a busy block.

- **Google not connected?** Ask them to connect it, or ask for their busy times in plain words
  ("classes Mon/Wed 9–10:15, work Tue and Thu afternoons") and use those.
- **Canvas not connected?** Carry on with the calendar alone and say so in one line. A missing
  Canvas connection means a missed deadline crunch, not a broken flow.
- Neither connected and they do not want to connect? Ask for the busy times directly. The
  whole flow still works; it is the same script either way.

**Only the student's own calendar.** Never read, infer or ask for anyone else's — the other
people in this group are not Cubbie's students and have not agreed to anything.

### 3. Build their share code

Run it from the skill folder:

```
python3 scripts/squad_sync.py mine --week-start 2026-10-26 --tz America/Phoenix \
  --busy "mon 09:00-10:15" --busy "mon 14:00-16:00" --busy "wed 18:00-19:00"
```

Pass the student's **local** date and timezone — the sandbox clock may be somewhere else.

The script prints the code and a plain-language note about exactly what it reveals. **Show the
student that note before they share anything**, and show it every time, not just the first:

> Here's your code for this week. It shows 12 busy blocks and nothing else — no event
> names, no places, no reasons.
>
> SQSY1 TZ:America/Phoenix W:2026-10-26 L:busy B:1-0900-1015,... X:313e
>
> Send that to the group and ask them to text theirs back. Want me to write the message?

Then **offer to draft the group message, and let the student send it.** Cubbie texts only its
own student; it never messages the friends. Drafting it and handing it over is the whole
interaction with the rest of the group.

### 4. Merge the replies

As codes come back, paste them in:

```
python3 scripts/squad_sync.py merge --code "SQSY1 ..." --code "SQSY1 ..." --need 120
```

Add `--day-start 08:00 --day-end 22:00` to bound the hours, `--top 5` for how many options.

The script handles the things that go wrong in a real group chat: a code mangled by
autocorrect fails its checksum and is rejected rather than silently misread; codes for
different weeks are refused with the dates named; a friend who shared nothing is counted as
**someone to ask**, never as free.

### 5. Propose, confirm, then act

Give the student the top two or three options and let them pick. **Then and only then**, after
an explicit yes:

- add it to their **Google Calendar**
- draft the "locked in for Thursday 4pm?" message for them to send
- offer a **reminder** an hour before, or a **check-in** the morning of

Never add the event, send a message or set a recurring check-in before they say yes.

### If someone never replies

Say so plainly and offer the smaller thing:

> Two of four sent times. Want to go with the best slot for the three of us, or wait?

A group that half-answers is the normal case, not an error.

## Disclosure levels

The student chooses with `--level`. Default is `busy`, which is right almost always.

| Level | What the code carries | Use when |
|---|---|---|
| `none` | No times at all | They will only answer yes/no to one specific proposed time |
| `busy` | Busy intervals. No reason, title, place or category | **Default.** Almost always this |
| `category` | Intervals plus one word: `class`, `work`, `personal` | The group needs to know what is moveable |

Going up a rung is the student's call, never Cubbie's. If they ask for `category`, say in one
line what changes: the group learns which blocks are class versus work versus personal.

`personal` is deliberately vague and covers health, family, a date, a bad day. **Never** invent
a more specific category, and never put a reason anywhere in a code.

## Where the detail lives

| File | Read it when |
|---|---|
| `references/examples.md` | You want the actual wording for a reply. Eight worked situations: the group that half-answers, the block she will not explain, Canvas not connected, a mangled code, a student asking to share more |
| `references/disclosure.md` | **Before changing anything about what a code contains.** The full rules and why each exists |

Full disclosure rules, and the reasoning behind them: `references/disclosure.md`.

## Try it without any data

```
python3 scripts/squad_sync.py mine --sample
python3 scripts/squad_sync.py merge --sample --need 90
```

Runs on a bundled example week in `assets/`. No calendar, no account, no network, and it
leaves nothing behind.

## Replies

Keep replies to a few short lines of plain text — no Markdown, no headings, no tables; iMessage
shows the symbols literally. Put the share code on its own line so it is easy to copy.

Lead with the answer. For merged results, give the top two or three times as short lines, not a
table. If there are more than five options, give three and offer the rest.

Always state what a code reveals before the student shares it, in one sentence.

Ask one question at a time, with a default they can accept by saying "yes".

When something fails, say the one useful thing: "That code got cut off — can you ask Ben to
send it again?" rather than an error.

## Rules this Skill does not bend

- **Only the student's own calendar is read.** Never anyone else's.
- **The code never carries a reason.** No titles, no locations, no people, no course names.
  The script refuses to build a code containing anything but times.
- **Cubbie texts only the student.** Reaching the group happens by the student sending.
- **Nothing is added, sent or scheduled without an explicit yes.**
- **Nothing leaves the student's phone and sandbox.** No server, no account, no upload. If a
  future version ever sends data anywhere, it says so here, in plain words, first.
