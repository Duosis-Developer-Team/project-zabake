from typing import Optional

from .keys import normalize_name


def customer_code_equal(left: Optional[str], right: Optional[str]) -> bool:
    return normalize_name(left) == normalize_name(right)
