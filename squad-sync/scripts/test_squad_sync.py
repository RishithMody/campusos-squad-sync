#!/usr/bin/env python3
"""Tests for squad_sync.py. Standard library only, like the thing it tests.

    python3 scripts/test_squad_sync.py

The privacy tests are the point. Everything else is scheduling arithmetic; the ones under
"a code may contain times and nothing else" are the reason this Skill is worth shipping.
"""

import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import squad_sync as ss  # noqa: E402

MON = date(2026, 10, 26)


class Encoding(unittest.TestCase):
    def test_roundtrip(self):
        blocks = [ss.parse_busy("mon 09:00-10:15"), ss.parse_busy("wed 18:00-19:00")]
        got = ss.decode(ss.encode(MON, "America/Phoenix", "busy", blocks))
        self.assertEqual(got["week_start"], MON)
        self.assertEqual(got["tz"], "America/Phoenix")
        self.assertEqual([(b["day"], b["start"], b["end"]) for b in got["blocks"]],
                         [(1, 540, 615), (3, 1080, 1140)])

    def test_weekday_names_and_numbers_agree(self):
        self.assertEqual(ss.parse_busy("mon 09:00-10:00"), ss.parse_busy("1 09:00-10:00"))
        self.assertEqual(ss.parse_busy("sun 09:00-10:00")["day"], 7)

    def test_mangled_code_is_rejected_not_misread(self):
        code = ss.encode(MON, "America/Phoenix", "busy", [ss.parse_busy("mon 09:00-10:15")])
        broken = code.replace("0900", "0930")
        with self.assertRaises(ss.BadInput) as cm:
            ss.decode(broken)
        self.assertIn("changed or cut off", str(cm.exception))

    def test_truncated_code_is_rejected(self):
        code = ss.encode(MON, "America/Phoenix", "busy", [ss.parse_busy("mon 09:00-10:15")])
        with self.assertRaises(ss.BadInput):
            ss.decode(code[: len(code) // 2])

    def test_week_must_be_a_monday(self):
        # A Tuesday anchor shifted every weekday label by one, silently: nothing crashed,
        # codes merged, and the group would have been told the wrong day.
        with self.assertRaises(ss.BadInput) as cm:
            ss.encode(date(2026, 10, 27), "UTC", "busy", [])
        self.assertIn("Monday", str(cm.exception))
        self.assertIn("2026-10-26", str(cm.exception))

    def test_adjacent_blocks_are_merged(self):
        blocks = [ss.parse_busy("mon 09:00-10:00"), ss.parse_busy("mon 10:00-11:00"),
                  ss.parse_busy("mon 10:30-12:00")]
        got = ss.decode(ss.encode(MON, "UTC", "busy", blocks))["blocks"]
        self.assertEqual(len(got), 1)
        self.assertEqual((got[0]["start"], got[0]["end"]), (540, 720))

    def test_backwards_block_rejected(self):
        with self.assertRaises(ss.BadInput):
            ss.parse_busy("mon 14:00-09:00")


class ACodeMayContainTimesAndNothingElse(unittest.TestCase):
    def test_level_none_enumerates_nothing(self):
        blocks = [ss.parse_busy("mon 09:00-10:15"), ss.parse_busy("wed 18:00-19:00")]
        code = ss.encode(MON, "UTC", "none", blocks)
        self.assertEqual(ss.decode(code)["blocks"], [])
        self.assertNotIn("0900", code)

    def test_category_is_dropped_below_its_level(self):
        blocks = [ss.parse_busy("wed 18:00-19:00 personal")]
        code = ss.encode(MON, "UTC", "busy", blocks)
        self.assertNotIn("personal", code)
        self.assertIsNone(ss.decode(code)["blocks"][0]["category"])

    def test_category_survives_at_its_own_level(self):
        blocks = [ss.parse_busy("wed 18:00-19:00 personal")]
        self.assertEqual(ss.decode(ss.encode(MON, "UTC", "category", blocks))["blocks"][0]["category"],
                         "personal")

    def test_category_vocabulary_is_closed(self):
        # 'medical' as a category is a diagnosis in everything but name.
        for bad in ("medical", "therapy", "health", "interview"):
            with self.assertRaises(ss.BadInput):
                ss.parse_busy(f"wed 18:00-19:00 {bad}")

    def test_merged_blocks_lose_a_category_they_no_longer_share(self):
        blocks = [ss.parse_busy("mon 09:00-10:00 class"), ss.parse_busy("mon 10:00-11:00 personal")]
        got = ss.decode(ss.encode(MON, "UTC", "category", blocks))["blocks"]
        self.assertEqual(len(got), 1)
        self.assertIsNone(got[0]["category"], "a merged block must not inherit one side's category")

    def test_encode_refuses_free_text(self):
        # The last line of defence: if anything but times reaches the payload, no code.
        with self.assertRaises(ss.BadInput) as cm:
            ss.encode(MON, "UTC", "category",
                      [{"day": 3, "start": 1080, "end": 1140, "category": "therapy at 6"}])
        self.assertIn("may only contain times", str(cm.exception))

    def test_no_identifying_field_anywhere_in_a_code(self):
        blocks = [ss.parse_busy("mon 09:00-10:15 class")]
        code = ss.encode(MON, "America/Phoenix", "category", blocks)
        for leak in ("ana", "@", "CHEM", "Ruiz", "therapy", "Library"):
            self.assertNotIn(leak.lower(), code.lower())


class Merging(unittest.TestCase):
    def codes(self, *specs, level="busy"):
        return [ss.decode(ss.encode(MON, "UTC", level, [ss.parse_busy(b) for b in s]))
                for s in specs]

    def test_finds_the_gap_everyone_shares(self):
        got = ss.free_windows(self.codes(["mon 08:00-12:00"], ["mon 14:00-18:00"]),
                              need=60, day_start=480, day_end=1320)
        monday = [w for w in got if w["day"] == 1]
        self.assertIn((720, 840), [(w["start"], w["end"]) for w in monday])

    def test_respects_the_minimum_length(self):
        codes = self.codes(["mon 08:00-12:00", "mon 13:00-22:00"])
        self.assertTrue(ss.free_windows(codes, 60, 480, 1320))
        self.assertFalse([w for w in ss.free_windows(codes, 90, 480, 1320) if w["day"] == 1])

    def test_silence_is_not_availability(self):
        # Someone who shared nothing must be flagged, never counted as free.
        codes = self.codes(["mon 08:00-22:00"]) + self.codes([], level="none")
        got = ss.free_windows(codes, 60, 480, 1320)
        self.assertTrue(all(w["abstained"] == 1 for w in got))

    def test_a_fully_busy_day_yields_nothing(self):
        codes = self.codes(["mon 08:00-22:00"])
        self.assertFalse([w for w in ss.free_windows(codes, 60, 480, 1320) if w["day"] == 1])

    def test_day_bounds_are_honoured(self):
        got = ss.free_windows(self.codes([]), need=60, day_start=600, day_end=720)
        self.assertTrue(all(w["start"] >= 600 and w["end"] <= 720 for w in got))


class Samples(unittest.TestCase):
    def test_mine_sample_runs(self):
        self.assertEqual(ss.main(["mine", "--sample"]), 0)

    def test_merge_sample_runs(self):
        self.assertEqual(ss.main(["merge", "--sample", "--need", "90"]), 0)

    def test_bundled_codes_are_valid_and_same_week(self):
        import json
        codes = json.loads((ss.ASSETS / "sample-codes.json").read_text())["codes"]
        weeks = {ss.decode(c)["week_start"] for c in codes}
        self.assertEqual(len(weeks), 1)
        self.assertEqual(weeks.pop().weekday(), 0)

    def test_merge_refuses_mismatched_weeks(self):
        a = ss.encode(MON, "UTC", "busy", [ss.parse_busy("mon 09:00-10:00")])
        b = ss.encode(date(2026, 11, 2), "UTC", "busy", [ss.parse_busy("mon 09:00-10:00")])
        self.assertEqual(ss.main(["merge", "--code", a, "--code", b]), 2)

    def test_merge_needs_two_codes(self):
        a = ss.encode(MON, "UTC", "busy", [])
        self.assertEqual(ss.main(["merge", "--code", a]), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
