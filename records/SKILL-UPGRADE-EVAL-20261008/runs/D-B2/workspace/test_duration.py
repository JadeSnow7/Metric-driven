import unittest

from duration import parse_duration


class ParseDurationTests(unittest.TestCase):
    def test_seconds(self):
        self.assertEqual(parse_duration("45s"), 45)

    def test_hours(self):
        self.assertEqual(parse_duration("2h"), 7200)

    def test_minutes_and_seconds(self):
        self.assertEqual(parse_duration("1m30s"), 90)

    def test_hours_minutes_seconds(self):
        self.assertEqual(parse_duration("1h30m"), 5400)
        self.assertEqual(parse_duration("1h1m1s"), 3661)

    def test_rejects_garbage(self):
        with self.assertRaises(ValueError):
            parse_duration("soon")


if __name__ == "__main__":
    unittest.main()
