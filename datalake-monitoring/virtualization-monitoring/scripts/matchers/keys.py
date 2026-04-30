from typing import Optional


def normalize_uuid(value: Optional[str]) -> str:
    if not value:
        return ""
    return value.strip().lower()


def normalize_name(value: Optional[str]) -> str:
    if not value:
        return ""
    return " ".join(value.strip().lower().split())
