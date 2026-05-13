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


def parse_virtual_fw_ip_port(value):
    """
    Split NetBox virtual_fw ip_port string into IP and port.

    Expected form for management access is ``IPv4:port`` (single colon). If the part
    after the first colon is all digits, it is returned as ``port``; otherwise the
    whole string is treated as ``ip`` and ``port`` is empty (e.g. IPv6 literals).
    """
    s = (value or "").strip()
    if not s:
        return {"ip": "", "port": ""}
    if ":" not in s:
        return {"ip": s, "port": ""}
    host_part, rest = s.split(":", 1)
    rest = rest.strip()
    if rest.isdigit() and host_part.strip() != "":
        return {"ip": host_part.strip(), "port": rest}
    return {"ip": s, "port": ""}


def virtual_fw_mapping_match(entries, vendor_name="", model_name=""):
    """
    Return first mapping dict from entries that matches vendor (required, case-insensitive)
    and optional model_prefix / model_suffix against model_name (case-insensitive).
    """
    if not entries:
        return {}
    vn = (vendor_name or "").strip().lower()
    ml = (model_name or "").strip().lower()
    for e in entries:
        if not isinstance(e, dict):
            continue
        v = str(e.get("vendor", "")).strip().lower()
        if v != vn:
            continue
        prefix = e.get("model_prefix")
        suffix = e.get("model_suffix")
        ok = True
        if prefix is not None and str(prefix).strip() != "":
            if not ml.startswith(str(prefix).strip().lower()):
                ok = False
        if ok and suffix is not None and str(suffix).strip() != "":
            if not ml.endswith(str(suffix).strip().lower()):
                ok = False
        if ok:
            return e
    return {}


def zabbix_vfw_technical_hostname(text, vfw_id=""):
    """
    Zabbix technical host for NetBox virtual firewalls: ASCII slug plus _VFW_<id> suffix.
    """
    sid = str(vfw_id).strip() if vfw_id is not None else ""
    suffix = f"_VFW_{sid}" if sid else ""
    base_slug = zabbix_technical_hostname(text, "")
    if not suffix:
        return base_slug or "host"
    if not base_slug:
        return zabbix_technical_hostname("", f"VFW_{sid}")
    suf_low = suffix.lower()
    if base_slug.lower().endswith(suf_low):
        out = _truncate_and_sanitize(base_slug)
        return out[:_MAX_HOST_LEN]
    max_base = _MAX_HOST_LEN - len(suffix)
    if max_base < 1:
        return _truncate_and_sanitize(suffix)[:_MAX_HOST_LEN]
    truncated = base_slug[:max_base].rstrip("._-")
    if not truncated:
        return zabbix_technical_hostname("", f"VFW_{sid}")
    merged = truncated + suffix
    return _truncate_and_sanitize(merged)[:_MAX_HOST_LEN]


def zabbix_platform_technical_hostname(text, platform_id=""):
    """
    Zabbix technical host for NetBox platforms: ASCII slug from name plus _P_<id> suffix
    within max length so each platform id maps to a unique host key.
    """
    sid = str(platform_id).strip() if platform_id is not None else ""
    suffix = f"_P_{sid}" if sid else ""
    base_slug = zabbix_technical_hostname(text, "")
    if not suffix:
        return base_slug or "host"
    if not base_slug:
        return zabbix_technical_hostname("", f"P_{sid}")
    suf_low = suffix.lower()
    if base_slug.lower().endswith(suf_low):
        out = _truncate_and_sanitize(base_slug)
        return out[:_MAX_HOST_LEN]
    max_base = _MAX_HOST_LEN - len(suffix)
    if max_base < 1:
        return _truncate_and_sanitize(suffix)[:_MAX_HOST_LEN]
    truncated = base_slug[:max_base].rstrip("._-")
    if not truncated:
        return zabbix_technical_hostname("", f"P_{sid}")
    merged = truncated + suffix
    return _truncate_and_sanitize(merged)[:_MAX_HOST_LEN]


class FilterModule:
    """Ansible filter plugin registration."""

    def filters(self):
        return {
            "zabbix_technical_hostname": self._filter_zabbix_technical_hostname,
            "zabbix_platform_technical_hostname": self._filter_zabbix_platform_technical_hostname,
            "zabbix_vfw_technical_hostname": self._filter_zabbix_vfw_technical_hostname,
            "parse_virtual_fw_ip_port": self._filter_parse_virtual_fw_ip_port,
            "virtual_fw_mapping_match": self._filter_virtual_fw_mapping_match,
        }

    def _filter_zabbix_technical_hostname(self, value, fallback_id=""):
        return zabbix_technical_hostname(value, fallback_id)

    def _filter_zabbix_platform_technical_hostname(self, value, platform_id=""):
        return zabbix_platform_technical_hostname(value, platform_id)

    def _filter_zabbix_vfw_technical_hostname(self, value, vfw_id=""):
        return zabbix_vfw_technical_hostname(value, vfw_id)

    def _filter_parse_virtual_fw_ip_port(self, value):
        return parse_virtual_fw_ip_port(value)

    def _filter_virtual_fw_mapping_match(self, entries, vendor_name="", model_name=""):
        return virtual_fw_mapping_match(entries, vendor_name, model_name)
