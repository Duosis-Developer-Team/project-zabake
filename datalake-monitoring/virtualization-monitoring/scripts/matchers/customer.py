from typing import Optional

from .keys import normalize_name


def parse_customer_code_from_name(name: Optional[str]) -> str:
    normalized = normalize_name(name)
    if not normalized:
        return ""
    for separator in ("-", "_", "."):
        if separator in normalized:
            return normalized.split(separator, 1)[0].strip()
    return normalized


def resolve_customer_code(row: Optional[dict]) -> str:
    if not row:
        return ""
    explicit = normalize_name(row.get("customer_code"))
    if explicit:
        return explicit
    name_candidates = [
        row.get("vmname"),
        row.get("vm_name"),
        row.get("lparname"),
        row.get("name"),
    ]
    for candidate in name_candidates:
        parsed = parse_customer_code_from_name(candidate)
        if parsed:
            return parsed
    return ""


def customer_code_equal(left: Optional[str], right: Optional[str]) -> bool:
    return normalize_name(left) == normalize_name(right)
