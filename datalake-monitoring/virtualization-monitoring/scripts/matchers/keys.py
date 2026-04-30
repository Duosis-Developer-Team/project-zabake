def normalize_uuid(value: str | None) -> str:
    if not value:
        return ""
    return value.strip().lower()


def normalize_name(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.strip().lower().split())
