# Safe disclosure rules

Read this before changing anything about what a share code contains.

A squad-sync code gets pasted into a group chat. That is the whole design, and it is also the
whole risk: once it is sent, it cannot be taken back, it can be screenshotted, and it will be
read by people the student did not choose. Everything below follows from that one fact.

## The rule

**A code may contain times. Nothing else, ever.**

Not a title. Not a location. Not a course code. Not a person. Not a reason. Not the student's
name, email, phone, school, or student number. Not a free-text note, however short.

`scripts/squad_sync.py` enforces this in `encode()` — it inspects the payload it is about to
emit and refuses to produce a code containing characters outside the allowed set. That check
exists because "the caller will pass clean data" is not a guarantee, and a leak here is
permanent.

## The ladder

| Level | Carries | Cannot carry |
|---|---|---|
| `none` | Nothing. A yes/no to one proposed time | Any enumeration of times |
| `busy` | Busy intervals | Reason, title, place, people, category |
| `category` | Intervals + one of `class`, `work`, `personal` | Free text of any kind |

Default is `busy`. Going up is the student's explicit choice, and Cubbie says in one line what
changes before it happens.

## Why `category` has exactly three values

`class`, `work`, `personal`. That is the complete list and it should stay that way.

`personal` deliberately absorbs health, therapy, a family emergency, a date, a funeral, a bad
day. The moment someone adds `medical` as "more useful", the category stops describing
availability and starts describing the person — and a weekly `medical` block at the same hour
is a diagnosis in everything but name.

A category that reveals **why** someone is unavailable defeats the entire point of having a
ladder. If a future version needs more granularity, the answer is a direct conversation between
the people involved, not a finer enum.

## Three things that look harmless and are not

**Adjacent blocks.** Three separate 30-minute blocks in a row say something about the shape of
an afternoon that one 90-minute block does not. `merge_overlapping()` collapses them. This is a
privacy measure, not tidiness.

**Silence read as consent.** A friend who shares nothing is not free — they are someone who has
not answered. `free_windows()` counts them separately and the output says "ask them directly".
Treating a non-answer as availability turns "I did not want to share" into "any time works".

**Precision.** Times are minutes, which is already fine-grained. Do not add seconds, and do not
add a "confidence" or "tentative" field — a tentative block invites the question "tentative
why?", which is the question this whole design exists to avoid.

## What the student must be told, every time

Before they share a code, Cubbie states what it reveals in one sentence. Not once at setup —
**every time**, because the thing being shared changes each week and consent to share in
general is not consent to share this.

The script prints that sentence itself, so Cubbie has something accurate to repeat rather than
a description it composed.

## Other people's data

The student's agent reads the student's calendar. Nobody else's, ever — not a shared calendar,
not a friend's code "to check it", not a group calendar that happens to be visible.

The other people in the group are not Cubbie's students. They have agreed to share one line of
free/busy with their friend, and nothing more. Their codes are used to compute an overlap and
are not stored, logged, or sent anywhere.

## If this Skill ever grows a backend

It does not have one today: no server, no account, no network call. If a later version adds
one, that fact goes in `SKILL.md` in plain words, above the fold, before any of it ships. A
student who installed a Skill that keeps everything on their phone should not discover by
accident that a newer version does not.
