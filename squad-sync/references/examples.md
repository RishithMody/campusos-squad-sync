# Worked examples

Realistic student situations, with the texts Cubbie should produce. Plain text, short lines,
no Markdown — these arrive on a phone.

## 1. The study group that has been trying for a week

**Student:** "we've been trying to find a time for the 340 study group all week, can you help"

Cubbie reads her Google Calendar and Canvas for the week, builds the code, and replies:

```
Yeah. Here's your week as a share code - 12 busy blocks, no event names,
no places, no reasons.

SQSY1 TZ:America/Phoenix W:2026-10-26 L:busy B:1-0900-1015,1-1030-1145,... X:313e

Send it to the group and ask them to text theirs back. Want me to write that message?
```

She says yes. Cubbie drafts something she can paste, and **she** sends it — Cubbie never texts
the group. Two friends reply with codes.

```
Got Ben and Cal. All three of you are free:

Wed 28 Oct, 3-6pm
Sat 31 Oct, 2-10pm
Sun 1 Nov, all day

Dana hasn't sent hers. Pick one of these and I'll ask, or wait for her?
```

She picks Wednesday.

```
Want me to put Wed 3-5pm on your calendar and write the "locked in" message?
```

Only after she says yes does anything get created.

## 2. The one block she does not want to explain

Ana has therapy on Wednesday at 6pm. It is in her Google Calendar as "Therapy — Dr Oyelaran".

In the code, it is `3-1800-1900`. That is all. Not the title, not the clinician, not the
word therapy. The group learns she is busy 6–7pm on Wednesday, which is the only thing they
needed to know, and they learn it without anyone having to ask her to redact her own calendar.

This is the whole reason the Skill exists. If a change would make this block say anything
more, the change is wrong.

## 3. Asked for availability by a classmate

**Student:** "someone from my group project wants to know when I'm free thursday and friday, I
don't want to send him my whole calendar"

```
Here's just those two days:

SQSY1 TZ:America/Phoenix W:2026-10-26 L:busy B:4-0900-1015,4-1300-1700,5-0900-1015,5-1200-1300 X:9c2d

Busy blocks only, nothing about what they are. Send him that.
```

## 4. Nobody replies

**Student:** "only ben sent his"

```
Two of four. You and Ben are both free Wed 3-6pm and Sat afternoon.

Go with one of those for the two of you, or give it another day?
```

Not an error. A group that half-answers is the normal case.

## 5. Canvas is not connected

```
I can see your Google Calendar but not Canvas, so this won't include assignment
deadlines - just what's already on your calendar. Connect Canvas and I'll redo it,
or shall I go with what I have?
```

One line, one actionable choice.

## 6. A code arrives mangled

iMessage and autocorrect do damage. The checksum catches it.

```
Cal's code got cut off in the paste. Can you ask him to send it again?
```

Never guess at a damaged code. A misread block means the group is told a time that does not
work for someone.

## 7. They want to share more

**Student:** "can you show them which of my blocks are class vs work? they're trying to figure
out what I can move"

```
I can switch to the category level - the group would then see which blocks are
class, work or personal, as well as when. Still no titles or reasons.

Want that, or keep it to busy-only?
```

Going up a rung is her call, said out loud, every time.

## 8. Outside Cubbie, or no calendar at all

The script does not need Cubbie. If the student is in another agent, or nothing is connected:

```
Tell me your busy times for the week and I'll build the code -
something like "classes mon/wed 9-10:15, work tue and thu afternoons".
```

Same script, same output. The Skill degrades to a conversation, not an error.
