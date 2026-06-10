"""Unit tests for Linux agent template filter."""

from __future__ import annotations

import unittest

from lib.template_filter import host_has_linux_agent_template


class TestTemplateFilterExtra(unittest.TestCase):
    def test_case_insensitive_match(self):
        host = {"parentTemplates": [{"name": "BLT - LINUX BY ZABBIX AGENT"}]}
        self.assertTrue(host_has_linux_agent_template(host))


if __name__ == "__main__":
    unittest.main()
