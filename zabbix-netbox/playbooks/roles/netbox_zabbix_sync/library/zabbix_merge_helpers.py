#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Compatibility shim for unit tests and docs referencing library/zabbix_merge_helpers.py.

Canonical implementation: module_utils/zabbix_merge_helpers.py (Ansible bundles this path).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_MODULE_PATH = (
    Path(__file__).resolve().parent.parent / "module_utils" / "zabbix_merge_helpers.py"
)
_spec = importlib.util.spec_from_file_location("zabbix_merge_helpers_impl", _MODULE_PATH)
_impl = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_impl)

load_managed_tag_keys = _impl.load_managed_tag_keys
is_managed_tag = _impl.is_managed_tag
merge_tags = _impl.merge_tags
merge_host_groups = _impl.merge_host_groups
merge_macros = _impl.merge_macros
should_preserve_visible_name = _impl.should_preserve_visible_name
resolve_proxy_group_update = _impl.resolve_proxy_group_update

__all__ = [
    "load_managed_tag_keys",
    "is_managed_tag",
    "merge_tags",
    "merge_host_groups",
    "merge_macros",
    "should_preserve_visible_name",
    "resolve_proxy_group_update",
]
