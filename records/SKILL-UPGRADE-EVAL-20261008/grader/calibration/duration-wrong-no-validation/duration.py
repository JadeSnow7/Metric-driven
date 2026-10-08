import re

_UNITS = {"h": 3600, "m": 60, "s": 1}
_TOKEN = re.compile(r"(\d+)([hms])")
_VALID = re.compile(r"(?:\d+[hms])+")


def parse_duration(text: str) -> int:
    """Parse durations such as "1h30m" or "45s" into whole seconds."""
    return sum(int(amount) * _UNITS[unit] for amount, unit in _TOKEN.findall(text))
