import unittest

from duration import parse_duration


class ParseDurationTests(unittest.TestCase):
    def test_seconds(self):
        self.assertEqual(parse_duration("45s"), 45)

    def test_hours(self):
        self.assertEqual(parse_duration("2h"), 7200)

    def test_minutes_and_seconds(self):
        self.assertEqual(parse_duration("1m30s"), 90)

    def test_hours_and_minutes(self):
        self.assertEqual(parse_duration("1h30m"), 5400)

    def test_all_three_units(self):
        self.assertEqual(parse_duration("1h2m3s"), 3723)

    def test_rejects_garbage(self):
        with self.assertRaises(ValueError):
            parse_duration("soon")


if __name__ == "__main__":
    unittest.main()
