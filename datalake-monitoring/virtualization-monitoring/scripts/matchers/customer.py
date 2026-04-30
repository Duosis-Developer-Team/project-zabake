from .keys import normalize_name


def customer_code_equal(left: str | None, right: str | None) -> bool:
    return normalize_name(left) == normalize_name(right)
