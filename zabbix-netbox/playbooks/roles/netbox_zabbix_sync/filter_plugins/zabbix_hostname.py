# -*- coding: utf-8 -*-
"""Ansible filters: Zabbix technical host name (ASCII-safe, Turkish transliteration)."""

from __future__ import annotations

import re
import unicodedata

# Zabbix host name max length (API / UI constraint)
_MAX_HOST_LEN = 128

# Turkish-specific letters before generic NFKD pass
_TR_MAP = str.maketrans(
    {
        "ı": "i",
        "İ": "I",
        "ş": "s",
        "Ş": "S",
        "ğ": "g",
        "Ğ": "G",
        "ü": "u",
        "Ü": "U",
        "ö": "o",
        "Ö": "O",
        "ç": "c",
        "Ç": "C",
    }
)


def zabbix_technical_hostname(text, fallback_id=""):
    """
    Build a Zabbix-safe technical host string: ASCII [A-Za-z0-9._-], max length.

    :param text: Human-readable host label (may contain Turkish / Unicode).
    :param fallback_id: If slug is empty after normalization, use host-<id> or p<id>.
    """
    if text is None:
        raw = ""
    else:
        raw = str(text).strip()
    if not raw:
        fb = str(fallback_id).strip() if fallback_id else ""
        if fb:
            low = fb.lower()
            if low.startswith("host-") or low.startswith("p"):
                return _truncate_and_sanitize(fb)
            return _truncate_and_sanitize(f"host-{fb}")
        return "host"

    step1 = raw.translate(_TR_MAP)
    # Decompose and drop combining marks (accents on Latin letters)
    nfkd = unicodedata.normalize("NFKD", step1)
    ascii_buf = []
    for ch in nfkd:
        if unicodedata.category(ch) == "Mn":
            continue
        ascii_buf.append(ch)
    merged = "".join(ascii_buf)
    # Keep only Zabbix-typical safe set; map others to underscore
    safe = []
    for ch in merged:
        if ch.isalnum() or ch in "._-":
            safe.append(ch)
        elif ch.isspace():
            safe.append("_")
        else:
            safe.append("_")
    slug = "".join(safe)
    slug = re.sub(r"_+", "_", slug).strip("._-")
    slug = _truncate_and_sanitize(slug)
    if not slug:
        fb = str(fallback_id).strip() if fallback_id else ""
        if fb:
            low = fb.lower()
            if low.startswith("host-") or low.startswith("p"):
                slug = _truncate_and_sanitize(fb)
            else:
                slug = _truncate_and_sanitize(f"host-{fb}")
        else:
            slug = "host"
    return slug


def _truncate_and_sanitize(s: str) -> str:
    if not s:
        return ""
    s = s[:_MAX_HOST_LEN]
    s = re.sub(r"_+", "_", s).strip("._-")
    return s


class FilterModule:
    """Ansible filter plugin registration."""

    def filters(self):
        return {
            "zabbix_technical_hostname": self._filter_zabbix_technical_hostname,
        }

    def _filter_zabbix_technical_hostname(self, value, fallback_id=""):
        return zabbix_technical_hostname(value, fallback_id)
