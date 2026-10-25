# squad-sync

**Find a time your group can actually meet — without anyone sharing what's on their calendar.**

A [Cubbie](https://cubbie.ai) Skill, and a standard [Agent Skill](https://agentskills.io) that
also runs in Claude Code and Codex.

---

Four friends try to find two hours this week. Someone says "I'm free whenever", someone
screenshots their calendar, two people never answer, and it dies. A week later nobody has met.

The part that actually breaks is social, not technical: **sharing when you are free should not
mean sharing what you are doing.** So nobody shares.

squad-sync turns your week into one line of text:

```
SQSY1 TZ:America/Phoenix W:2026-10-26 L:busy B:1-0900-1015,1-1400-1600,3-1800-1900 X:313e
```

That is a whole week of availability. Day numbers and times — no event names, no places, no
people, no reasons. Paste it in the group chat, your friends paste theirs back, and squad-sync
finds the overlap.

"Busy Wednesday 6–7pm" is in there. "Therapy Wednesday 6pm" **cannot** be, because the code has
nowhere to put it.

## Install

Text this link to Cubbie:

```
https://github.com/RishithMody/campusos-squad-sync/tree/main/squad-sync
```

Cubbie asks first, then installs it. Then just say what you need:

> "we've been trying to find a time for the 340 study group all week"

## Try it without installing anything

No account, no key, no network, no setup — the script is Python standard library only.

```bash
git clone https://github.com/RishithMody/campusos-squad-sync.git
cd campusos-squad-sync/squad-sync

python3 scripts/squad_sync.py mine --sample
python3 scripts/squad_sync.py merge --sample --need 90
```

The first prints a share code for an example week. The second finds the times three friends
are all free.

## What it will and will not do

**Will**

- Read *your* Canvas and Google Calendar to build *your* code
- Show you exactly what a code reveals, before you send it, every time
- Draft the group message for you to send
- Find windows everyone has free, and say who hasn't answered
- Add the agreed time to your calendar and set a reminder — after you say yes

**Will not**

- Put a title, place, person or reason in a code. The script refuses to build one
- Read anyone else's calendar
- Message your friends. Cubbie texts only you; you share the code
- Send, book or schedule anything before you say yes
- Send your data anywhere. There is no server and no account. Nothing leaves your phone

## Disclosure levels

| Level | What your code carries |
|---|---|
| `none` | No times. You will answer yes/no to one proposed time |
| `busy` | **Default.** Busy intervals. No reason, title, place or category |
| `category` | Intervals plus one word: `class`, `work`, `personal` |

`personal` deliberately covers health, family, a date, a bad day. There is no finer category
and there should not be: one that says *why* you are unavailable defeats the point.

The full rules, and the reasoning: [`squad-sync/references/disclosure.md`](squad-sync/references/disclosure.md).

## Tests

```bash
python3 squad-sync/scripts/test_squad_sync.py
```

24 tests. The ones under `ACodeMayContainTimesAndNothingElse` are the ones that matter.

## Licence

Apache-2.0. See [LICENSE](LICENSE).
