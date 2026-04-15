"""
Unit tests for host_metadata utilities
"""

import sys
from pathlib import Path

scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from utils.host_metadata import (
    build_host_metadata_map,
    collect_unique_proxy_group_ids,
    extract_host_template_names,
    extract_main_interface_ip,
    extract_standard_host_tags,
)


class TestExtractStandardHostTags:
    def test_case_insensitive(self):
        tags = [
            {"tag": "location", "value": "DC1"},
            {"tag": "CONTACT", "value": "ops@example.com"},
            {"tag": "Tenant", "value": "Acme"},
        ]
        out = extract_standard_host_tags(tags)
        assert out["location"] == "DC1"
        assert out["contact"] == "ops@example.com"
        assert out["tenant"] == "Acme"

    def test_empty(self):
        assert extract_standard_host_tags([]) == {"location": "", "contact": "", "tenant": ""}


class TestExtractHostTemplateNames:
    def test_sorted_comma_separated(self):
        host = {
            "parentTemplates": [
                {"templateid": "2", "name": "Z Template"},
                {"templateid": "1", "name": "A Template"},
            ]
        }
        assert extract_host_template_names(host) == "A Template, Z Template"

    def test_empty(self):
        assert extract_host_template_names({}) == ""


class TestExtractMainInterfaceIp:
    def test_prefers_main(self):
        interfaces = [
            {"main": "0", "ip": "192.168.1.1"},
            {"main": "1", "ip": "10.0.0.5"},
        ]
        assert extract_main_interface_ip(interfaces) == "10.0.0.5"

    def test_fallback_first_ip(self):
        interfaces = [
            {"main": "0", "ip": "172.16.0.1"},
        ]
        assert extract_main_interface_ip(interfaces) == "172.16.0.1"

    def test_empty(self):
        assert extract_main_interface_ip([]) == ""


class TestCollectUniqueProxyGroupIds:
    def test_filters_monitored_by(self):
        hosts = [
            {"hostid": "1", "monitored_by": "2", "proxy_groupid": "5"},
            {"hostid": "2", "monitored_by": "0", "proxy_groupid": "5"},
            {"hostid": "3", "monitored_by": "2", "proxy_groupid": "5"},
        ]
        assert collect_unique_proxy_group_ids(hosts) == ["5"]


class TestBuildHostMetadataMap:
    def test_full_host(self):
        hosts = [
            {
                "hostid": "10",
                "monitored_by": "2",
                "proxy_groupid": "3",
                "tags": [
                    {"tag": "Location", "value": "L1"},
                    {"tag": "Contact", "value": "C1"},
                    {"tag": "Tenant", "value": "T1"},
                ],
                "interfaces": [{"main": "1", "ip": "10.1.1.1"}],
                "parentTemplates": [{"templateid": "99", "name": "Tmpl B"}, {"templateid": "98", "name": "Tmpl A"}],
            }
        ]
        proxy_map = {"3": "PG-Name"}
        m = build_host_metadata_map(hosts, proxy_map)
        assert m["10"]["location"] == "L1"
        assert m["10"]["contact"] == "C1"
        assert m["10"]["tenant"] == "T1"
        assert m["10"]["interface_ip"] == "10.1.1.1"
        assert m["10"]["proxy_group_name"] == "PG-Name"
        assert m["10"]["host_templates"] == "Tmpl A, Tmpl B"

    def test_no_proxy_group_when_not_monitored_by_group(self):
        hosts = [
            {
                "hostid": "1",
                "monitored_by": "0",
                "proxy_groupid": "3",
                "tags": [],
                "interfaces": [],
            }
        ]
        m = build_host_metadata_map(hosts, {"3": "X"})
        assert m["1"]["proxy_group_name"] == ""
        assert m["1"]["host_templates"] == ""
