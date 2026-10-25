#!/usr/bin/env python3
"""squad-sync -- turn a calendar into a shareable free/busy code, and find the overlap.

Standard library only, on purpose. No install step, no network, no account, nothing
leaves the student's sandbox. The whole point of this Skill is that a group can find a
time without anyone publishing their calendar, so the tool that does it should not be
sending anything anywhere either.

Two commands:

    mine   busy blocks in  ->  one shareable line out
    merge  several lines in ->  the times everyone is free

A code looks like this, and this is all of it:

    SQSY1 TZ:America/Phoenix W:2026-10-27 L:busy B:1-0900-1030,1-1400-1600,3-1800-2000 X:7f3a

No name, no title, no location, no reason, no course, no email. A day number inside the
window, a start, an end. That is the privacy guarantee, and it is enforced in encode()
rather than left to the caller's good intentions.

    python3 scripts/squad_sync.py mine --week-start 2026-10-27 --tz America/Phoenix \
        --busy "mon 09:00-10:30" --busy "mon 14:00-16:00" --busy "wed 18:00-20:00"
    python3 scripts/squad_sync.py merge --code "SQSY1 ..." --code "SQSY1 ..." --need 90
    python3 scripts/squad_sync.py mine --sample
    python3 scripts/squad_sync.py merge --sample
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

VERSION = "SQSY1"
HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"

DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

# The disclosure ladder, smallest first. A code carries exactly one of these, and the
# level decides what a block is allowed to say -- not the caller.
LEVELS = {
    "none": "No times at all. The code answers yes/no to one proposed time and nothing else.",
    "busy": "Busy intervals only. No reason, no title, no location. The default.",
    "category": "Busy intervals plus one coarse word: class, work, or personal.",
}
# Deliberately blunt. 'personal' absorbs health, therapy, family, a date, a bad day.
# Never add 'medical' or anything like it: a category that says WHY someone is
# unavailable defeats the entire point of having a ladder.
CATEGORIES = ["class", "work", "personal"]

TIME_RE = re.compile(r"^([01]\d|2[0-3]):?([0-5]\d)$")
BLOCK_RE = re.compile(r"^([1-7])-([0-2]\d[0-5]\d)-([0-2]\d[0-5]\d)(?:-(class|work|personal))?$")


class BadInput(Exception):
    """Something the student or Cubbie can fix, phrased so Cubbie can say it out loud."""


# --------------------------------------------------------------------------- parsing


def parse_minutes(text: str) -> int:
    m = TIME_RE.match(text.strip())
    if not m:
        raise BadInput(f"'{text}' is not a time like 14:00")
    return int(m.group(1)) * 60 + int(m.group(2))


def fmt_minutes(mins: int) -> str:
    return f"{mins // 60:02d}{mins % 60:02d}"


def pretty_time(mins: int) -> str:
    h, m = divmod(mins, 60)
    suffix = "am" if h < 12 else "pm"
    h12 = h % 12 or 12
    return f"{h12}:{m:02d}{suffix}" if m else f"{h12}{suffix}"


def parse_busy(spec: str) -> dict:
    """'mon 09:00-10:30' or 'mon 09:00-10:30 class' -> a block.

    Accepts a weekday name or a 1-7 day number, because Cubbie will be filling these in
    from whatever Canvas and Calendar gave it and both shapes are natural.
    """
    parts = spec.strip().lower().split()
    if len(parts) < 2:
        raise BadInput(f"'{spec}' should look like: mon 09:00-10:30")
    day_token, span = parts[0], parts[1]
    category = parts[2] if len(parts) > 2 else None

    if day_token.isdigit():
        day = int(day_token)
        if not 1 <= day <= 7:
            raise BadInput(f"day {day} is outside 1-7")
    else:
        key = day_token[:3]
        if key not in DAYS:
            raise BadInput(f"'{parts[0]}' is not a weekday")
        day = DAYS.index(key) + 1

    if "-" not in span:
        raise BadInput(f"'{span}' should look like 09:00-10:30")
    start_s, _, end_s = span.partition("-")
    start, end = parse_minutes(start_s), parse_minutes(end_s)
    if end <= start:
        raise BadInput(f"'{span}' ends before it starts")
    if category and category not in CATEGORIES:
        raise BadInput(f"'{category}' is not one of: {', '.join(CATEGORIES)}")
    return {"day": day, "start": start, "end": end, "category": category}


def merge_overlapping(blocks: list[dict]) -> list[dict]:
    """Collapse touching or overlapping busy blocks on the same day.

    Also a privacy measure, not only tidiness: three separate 30-minute blocks in a row
    says something about the shape of an afternoon that one 90-minute block does not.
    """
    out: list[dict] = []
    for b in sorted(blocks, key=lambda b: (b["day"], b["start"], b["end"])):
        if out and out[-1]["day"] == b["day"] and b["start"] <= out[-1]["end"]:
            out[-1]["end"] = max(out[-1]["end"], b["end"])
            if out[-1].get("category") != b.get("category"):
                out[-1]["category"] = None  # merged blocks lose a category they no longer share
        else:
            out.append(dict(b))
    return out


# --------------------------------------------------------------------- encode / decode


def checksum(body: str) -> str:
    """Four hex characters, so a code mangled by autocorrect is caught rather than merged.

    Not a security feature and not described as one: it catches paste damage.
    """
    h = 0
    for ch in body:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return f"{h:08x}"[:4]


def require_monday(week_start: date) -> None:
    """Day 1 means Monday in every code, so the anchor has to actually be one.

    Found by reading the sample output: a Tuesday anchor shifted every weekday label by
    one, silently. Nothing crashed, the codes merged cleanly, and the suggested times
    were simply the wrong days. A group would have shown up on the wrong evening.
    """
    if week_start.weekday() != 0:
        monday = week_start - timedelta(days=week_start.weekday())
        raise BadInput(
            f"--week-start must be a Monday. {week_start.isoformat()} is a "
            f"{week_start.strftime('%A')}; you probably want {monday.isoformat()}"
        )


def encode(week_start: date, tz: str, level: str, blocks: list[dict]) -> str:
    require_monday(week_start)
    if level not in LEVELS:
        raise BadInput(f"level must be one of: {', '.join(LEVELS)}")
    if not tz or " " in tz:
        raise BadInput("timezone should look like America/Phoenix")

    if level == "none":
        blocks = []
    blocks = merge_overlapping(blocks)

    parts = []
    for b in blocks:
        piece = f"{b['day']}-{fmt_minutes(b['start'])}-{fmt_minutes(b['end'])}"
        if level == "category" and b.get("category"):
            piece += f"-{b['category']}"
        parts.append(piece)

    body = f"{VERSION} TZ:{tz} W:{week_start.isoformat()} L:{level} B:{','.join(parts)}"

    # The last line of defence. Everything above is supposed to produce intervals only;
    # this refuses to emit a code if anything else got in, because a leak here is
    # permanent -- the student pastes it into a group chat and cannot take it back.
    allowed = set("0123456789-,:/.")
    payload = body.split("B:", 1)[1]
    stray = {c for c in payload if c not in allowed and c not in "classworkpersonal"}
    if stray:
        raise BadInput(
            "refusing to build a code containing "
            f"{''.join(sorted(stray))!r} -- a share code may only contain times"
        )
    return f"{body} X:{checksum(body)}"


def decode(code: str) -> dict:
    code = " ".join(code.strip().split())
    if not code.startswith(VERSION + " "):
        raise BadInput(f"this does not look like a squad-sync code (expected {VERSION})")
    if " X:" not in code:
        raise BadInput("the code is missing its checksum -- it was probably cut off")
    body, _, given = code.rpartition(" X:")
    if checksum(body) != given.strip():
        raise BadInput("this code was changed or cut off in transit -- ask for it again")

    fields = {}
    for token in body.split(" "):
        if ":" in token:
            k, _, v = token.partition(":")
            fields[k] = v
    for required in ("TZ", "W", "L"):
        if required not in fields:
            raise BadInput(f"the code is missing {required}")
    require_monday(date.fromisoformat(fields["W"]))
    if fields["L"] not in LEVELS:
        raise BadInput(f"unknown disclosure level '{fields['L']}'")

    blocks = []
    for piece in filter(None, fields.get("B", "").split(",")):
        m = BLOCK_RE.match(piece)
        if not m:
            raise BadInput(f"'{piece}' is not a valid busy block")
        day, start, end, category = m.groups()
        blocks.append({
            "day": int(day),
            "start": int(start[:2]) * 60 + int(start[2:]),
            "end": int(end[:2]) * 60 + int(end[2:]),
            "category": category,
        })
    return {
        "tz": fields["TZ"],
        "week_start": date.fromisoformat(fields["W"]),
        "level": fields["L"],
        "blocks": blocks,
    }


# ----------------------------------------------------------------------------- merging


def free_windows(codes: list[dict], need: int, day_start: int, day_end: int) -> list[dict]:
    """Times every code is free for at least `need` minutes.

    A code at level 'none' enumerates nothing, so it cannot be intersected. It is counted
    as a participant who must be asked directly rather than silently treated as free --
    assuming free would quietly turn 'I did not want to share' into 'any time works'.
    """
    usable = [c for c in codes if c["level"] != "none"]
    abstained = len(codes) - len(usable)

    results = []
    for day in range(1, 8):
        busy = []
        for c in usable:
            busy += [b for b in c["blocks"] if b["day"] == day]
        cursor = day_start
        for b in merge_overlapping(busy):
            if b["start"] > cursor:
                gap = min(b["start"], day_end) - cursor
                if gap >= need:
                    results.append({"day": day, "start": cursor, "end": cursor + gap})
            cursor = max(cursor, b["end"])
            if cursor >= day_end:
                break
        if cursor < day_end and day_end - cursor >= need:
            results.append({"day": day, "start": cursor, "end": day_end})

    results.sort(key=lambda w: (-(w["end"] - w["start"]), w["day"], w["start"]))
    for w in results:
        w["abstained"] = abstained
    return results


# ------------------------------------------------------------------------------ output


def describe_window(w: dict, week_start: date) -> str:
    day_name = (week_start + timedelta(days=w["day"] - 1)).strftime("%a %-d %b")
    return f"{day_name}, {pretty_time(w['start'])}-{pretty_time(w['end'])}"


def cmd_mine(args: argparse.Namespace) -> int:
    if args.sample:
        sample = json.loads((ASSETS / "sample-week.json").read_text())
        week_start = date.fromisoformat(sample["week_start"])
        tz, level = sample["tz"], sample["level"]
        blocks = [parse_busy(b) for b in sample["busy"]]
    else:
        if not args.week_start:
            raise BadInput("--week-start is required, as the Monday of the week, e.g. 2026-10-27")
        week_start = date.fromisoformat(args.week_start)
        tz, level = args.tz, args.level
        blocks = [parse_busy(b) for b in (args.busy or [])]

    code = encode(week_start, tz, level, blocks)
    merged = merge_overlapping(blocks) if level != "none" else []

    print(code)
    print()
    print(f"What this shows about you: {LEVELS[level]}")
    print(f"Busy blocks shared: {len(merged)}")
    print("It contains no event names, places, people or reasons.")
    if level == "category":
        print("At 'category' it also says class/work/personal. Drop to 'busy' to share less.")
    return 0


def cmd_merge(args: argparse.Namespace) -> int:
    raw = list(args.code or [])
    if args.sample:
        raw = json.loads((ASSETS / "sample-codes.json").read_text())["codes"]
    if len(raw) < 2:
        raise BadInput("give at least two codes -- yours and a friend's")

    codes, weeks = [], set()
    for i, r in enumerate(raw, 1):
        try:
            c = decode(r)
        except BadInput as exc:
            raise BadInput(f"code {i}: {exc}") from None
        codes.append(c)
        weeks.add(c["week_start"])
    if len(weeks) > 1:
        raise BadInput(
            "these codes are for different weeks ("
            + ", ".join(sorted(w.isoformat() for w in weeks))
            + ") -- everyone needs to use the same Monday"
        )
    tzs = {c["tz"] for c in codes}
    week_start = weeks.pop()

    windows = free_windows(codes, args.need, parse_minutes(args.day_start), parse_minutes(args.day_end))

    if len(tzs) > 1:
        print(f"Heads up: these codes are in different time zones ({', '.join(sorted(tzs))}).")
        print("Times below are as each person wrote them; confirm before you commit.")
        print()
    if not windows:
        print(f"No {args.need}-minute window works for all {len(codes)} of you this week.")
        print("Try a shorter session, a wider day range, or next week.")
        return 0

    print(f"Times all {len(codes)} of you are free for {args.need}+ minutes:")
    print()
    for w in windows[: args.top]:
        print(f"  {describe_window(w, week_start)}  ({(w['end'] - w['start']) // 60}h{(w['end'] - w['start']) % 60 or ''})")
    abstained = windows[0]["abstained"]
    if abstained:
        print()
        print(f"{abstained} person did not share times. Ask them directly before you lock one in.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="squad_sync.py", description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    m = sub.add_parser("mine", help="build a shareable code from busy blocks")
    m.add_argument("--week-start", help="the Monday of the week, YYYY-MM-DD")
    m.add_argument("--tz", default="America/Phoenix", help="IANA zone, e.g. America/Phoenix")
    m.add_argument("--level", default="busy", choices=sorted(LEVELS), help="how much to reveal")
    m.add_argument("--busy", action="append", help="'mon 09:00-10:30' (repeatable)")
    m.add_argument("--sample", action="store_true", help="run on the bundled example week")
    m.set_defaults(func=cmd_mine)

    g = sub.add_parser("merge", help="find times everyone is free")
    g.add_argument("--code", action="append", help="a squad-sync code (repeatable)")
    g.add_argument("--need", type=int, default=60, help="minutes needed (default 60)")
    g.add_argument("--day-start", default="08:00", help="earliest hour to suggest")
    g.add_argument("--day-end", default="22:00", help="latest hour to suggest")
    g.add_argument("--top", type=int, default=5, help="how many options to print")
    g.add_argument("--sample", action="store_true", help="run on the bundled example codes")
    g.set_defaults(func=cmd_merge)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except BadInput as exc:
        print(f"squad-sync: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
