import unittest
from datetime import date
from pick_message import pick_message


def fixture():
    """Tiny pool — pool sizes of 3 let us verify sequential rotation cleanly."""
    return {
        "holidays": {
            "ano_novo":    ["AN1", "AN2", "AN3"],
            "trabalhador": ["TR1", "TR2", "TR3"],
            "namorados":   ["NM1", "NM2", "NM3"],
            "finados":     ["FN1", "FN2", "FN3"],
            "natal":       ["NT1", "NT2", "NT3"],
            "reveillon":   ["RV1", "RV2", "RV3"],
            "sexta_13":    ["S13_1", "S13_2", "S13_3"],
        },
        "monday": ["MON1", "MON2", "MON3"],
        "odd":    ["ODD1", "ODD2", "ODD3"],
        "even":   ["EVN1", "EVN2", "EVN3"],
    }


class TestPickMessage(unittest.TestCase):
    def setUp(self):
        self.msgs = fixture()

    # --- Holiday detection (each fixed-date holiday) ---

    def test_ano_novo(self):
        self.assertIn(pick_message(date(2026, 1, 1), self.msgs),
                      self.msgs["holidays"]["ano_novo"])

    def test_trabalhador(self):
        self.assertIn(pick_message(date(2026, 5, 1), self.msgs),
                      self.msgs["holidays"]["trabalhador"])

    def test_namorados(self):
        self.assertIn(pick_message(date(2026, 6, 12), self.msgs),
                      self.msgs["holidays"]["namorados"])

    def test_finados(self):
        # 2026-11-02 is a Monday — also exercises Holiday > Monday priority.
        self.assertIn(pick_message(date(2026, 11, 2), self.msgs),
                      self.msgs["holidays"]["finados"])

    def test_natal(self):
        self.assertIn(pick_message(date(2026, 12, 25), self.msgs),
                      self.msgs["holidays"]["natal"])

    def test_reveillon(self):
        self.assertIn(pick_message(date(2026, 12, 31), self.msgs),
                      self.msgs["holidays"]["reveillon"])

    # --- Sexta-feira 13 ---

    def test_sexta_13(self):
        # 2026-02-13 is a Friday.
        self.assertIn(pick_message(date(2026, 2, 13), self.msgs),
                      self.msgs["holidays"]["sexta_13"])

    def test_friday_non_13_not_sexta(self):
        # 2026-02-06 is Friday but not the 13th — should fall through.
        msg = pick_message(date(2026, 2, 6), self.msgs)
        self.assertNotIn(msg, self.msgs["holidays"]["sexta_13"])

    # --- Monday ---

    def test_monday_non_holiday(self):
        # 2026-06-29 is a Monday with no holiday.
        self.assertIn(pick_message(date(2026, 6, 29), self.msgs),
                      self.msgs["monday"])

    # --- Parity fallback ---

    def test_odd_day(self):
        # 2026-06-25 is a Thursday, day 25 (odd).
        self.assertIn(pick_message(date(2026, 6, 25), self.msgs),
                      self.msgs["odd"])

    def test_even_day(self):
        # 2026-06-26 is a Friday, day 26 (even).
        self.assertIn(pick_message(date(2026, 6, 26), self.msgs),
                      self.msgs["even"])

    # --- Determinism + rotation ---

    def test_determinism(self):
        d = date(2026, 6, 25)
        self.assertEqual(pick_message(d, self.msgs),
                         pick_message(d, self.msgs))

    def test_sequential_rotation_within_odd_pool(self):
        # 2026-06-25 (Thu, odd), 2026-06-27 (Sat, odd), 2026-06-29 is Monday
        # so we use 06-27 and 06-29-skip. Use 06-25 and 06-27 — both odd, both
        # non-Monday, non-holiday. Indices differ by 2 (epoch_day differs by 2).
        m1 = pick_message(date(2026, 6, 25), self.msgs)
        m2 = pick_message(date(2026, 6, 27), self.msgs)
        i1 = self.msgs["odd"].index(m1)
        i2 = self.msgs["odd"].index(m2)
        self.assertEqual((i2 - i1) % len(self.msgs["odd"]), 2)


import json
from pathlib import Path


class TestRealMessagesFile(unittest.TestCase):
    def setUp(self):
        repo_root = Path(__file__).resolve().parent.parent
        with (repo_root / "messages" / "messages.json").open(encoding="utf-8") as f:
            self.msgs = json.load(f)

    def test_pool_counts(self):
        self.assertEqual(len(self.msgs["odd"]), 50)
        self.assertEqual(len(self.msgs["even"]), 50)
        self.assertEqual(len(self.msgs["monday"]), 20)
        for key in ("ano_novo", "trabalhador", "namorados",
                    "finados", "natal", "reveillon", "sexta_13"):
            self.assertEqual(len(self.msgs["holidays"][key]), 3, key)

    def test_all_messages_are_non_empty_strings(self):
        def walk(obj):
            if isinstance(obj, dict):
                for v in obj.values():
                    walk(v)
            elif isinstance(obj, list):
                for item in obj:
                    self.assertIsInstance(item, str)
                    self.assertTrue(item.strip(), "empty message")
                    self.assertLess(len(item), 2000, "Discord 2000-char cap")
        walk(self.msgs)

    def test_no_shell_metacharacters(self):
        forbidden = ("$", "`", "\\")
        def walk(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    walk(v, f"{path}/{k}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    walk(item, f"{path}[{i}]")
            elif isinstance(obj, str):
                for ch in forbidden:
                    self.assertNotIn(ch, obj,
                        f"shell metacharacter {ch!r} in {path}: {obj!r}")
        walk(self.msgs)

    def test_pick_message_works_against_real_file(self):
        # Smoke test: today's pick returns a non-empty string.
        from datetime import date
        msg = pick_message(date(2026, 6, 25), self.msgs)
        self.assertIsInstance(msg, str)
        self.assertTrue(msg.strip())


if __name__ == "__main__":
    unittest.main()
