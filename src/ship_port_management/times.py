from datetime import datetime


def is_valid_iso_time(text: str) -> bool:
    try:
        datetime.fromisoformat(text)
    except ValueError:
        return False
    return True
