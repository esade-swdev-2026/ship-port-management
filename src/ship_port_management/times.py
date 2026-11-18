from datetime import datetime

TIME_EXAMPLE = "2026-10-18T09:30"


def parse_time(text: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        raise ValueError(f"{label} must look like {TIME_EXAMPLE}, got {text}") from None
    if parsed.tzinfo is not None:
        raise ValueError(f"{label} must be a local time without a timezone, got {text}")
    return parsed


def current_time() -> str:
    return datetime.now().isoformat(timespec="minutes")
