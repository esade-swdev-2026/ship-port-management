from datetime import datetime


def is_valid_iso_time(text: str) -> bool:
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return False
    return parsed.tzinfo is None
