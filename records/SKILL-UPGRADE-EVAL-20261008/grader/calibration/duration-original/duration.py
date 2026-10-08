import re

_UNITS = {"h": 3600, "m": 60, "s": 1}
_TOKEN = re.compile(r"(\d+)([hms])")
_VALID = re.compile(r"(?:\d+[hms])+")


def parse_duration(text: str) -> int:
    """Parse durations such as "1h30m" or "45s" into whole seconds."""
    if not text or not _VALID.fullmatch(text):
        raise ValueError(f"invalid duration: {text!r}")
    match = _TOKEN.match(text)
    return int(match.group(1)) * _UNITS[match.group(2)]
