#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import sys

from ansible.module_utils.basic import AnsibleModule

# Role library path: import sibling helper module.
sys.path.insert(0, os.path.dirname(__file__))
from zabbix_merge_helpers import merge_tags  # noqa: E402


DOCUMENTATION = r"""
---
module: zabbix_merge_tags
short_description: Merge Zabbix host tags preserving manual tags and replacing managed keys
description:
  - Preserves tags not listed in managed_keys (and not starting with Loki_Tag_).
  - Replaces managed tags from new_managed_tags with deduplication by tag name.
options:
  existing_tags:
    description: Current tags from Zabbix host.get (list of dicts with tag and value).
    type: list
    required: true
  new_managed_tags:
    description: Desired managed tags from NetBox sync (list of dicts with tag and value).
    type: list
    required: true
  managed_keys:
    description: Tag names owned by automation (replaced on update).
    type: list
    required: true
author:
  - Duosis Datalake Platform
"""

EXAMPLES = r"""
- name: Merge tags for host update
  zabbix_merge_tags:
    existing_tags: "{{ zbx_existing_host.tags | default([]) }}"
    new_managed_tags: "{{ zbx_tags | default([]) }}"
    managed_keys: "{{ _effective_managed_tag_keys }}"
  register: zbx_tag_merge
"""


def main() -> None:
    module = AnsibleModule(
        argument_spec=dict(
            existing_tags=dict(type="list", required=True),
            new_managed_tags=dict(type="list", required=True),
            managed_keys=dict(type="list", required=True),
        ),
    )

    merged, change_log = merge_tags(
        module.params["existing_tags"],
        module.params["new_managed_tags"],
        module.params["managed_keys"],
    )

    tags_needs_update = any(
        entry.get("action") in ("added", "updated") for entry in change_log
    )

    module.exit_json(
        merged_tags=merged,
        change_log=change_log,
        tags_needs_update=tags_needs_update,
    )


if __name__ == "__main__":
    main()
