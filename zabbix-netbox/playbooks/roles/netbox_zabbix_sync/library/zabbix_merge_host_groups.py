#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.zabbix_merge_helpers import merge_host_groups


DOCUMENTATION = r"""
---
module: zabbix_merge_host_groups
short_description: Merge Zabbix host groups for host.update (managed + optional manual)
description:
  - Uses full required_managed_names (template host_groups + DEVICE_TYPE + HOST_GROUPS).
  - When preserve_manual is false, only required groups are returned (opt-in only).
options:
  existing_group_names:
    description: Current Zabbix host group names from host.get.
    type: list
    required: true
  required_managed_names:
    description: Full managed group name list from mapping/templates.
    type: list
    required: true
  preserve_manual:
    description: If false, do not keep existing groups outside the managed set.
    type: bool
    default: true
author:
  - Duosis Datalake Platform
"""

EXAMPLES = r"""
- name: Merge host groups for update
  zabbix_merge_host_groups:
    existing_group_names: "{{ zbx_existing_host.groups | map(attribute='name') | list }}"
    required_managed_names: "{{ zbx_required_groups_for_record }}"
    preserve_manual: true
  register: zbx_group_merge
"""


def main() -> None:
    module = AnsibleModule(
        argument_spec=dict(
            existing_group_names=dict(type="list", required=True),
            required_managed_names=dict(type="list", required=True),
            preserve_manual=dict(type="bool", default=True),
        ),
    )

    merged, needs_update = merge_host_groups(
        module.params["existing_group_names"],
        module.params["required_managed_names"],
        preserve_manual=module.params["preserve_manual"],
    )

    module.exit_json(
        merged_group_names=merged,
        groups_needs_update=needs_update,
    )


if __name__ == "__main__":
    main()
