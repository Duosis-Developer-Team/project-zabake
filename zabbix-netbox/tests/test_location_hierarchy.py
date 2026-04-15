"""Unit tests for NetBox location root resolution and BFS descendant collection."""

from __future__ import annotations

from unittest.mock import MagicMock

import sys
from pathlib import Path

# Import module under test from scripts/
_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import netbox_location_hierarchy as lh  # noqa: E402


def test_resolve_root_location_name_three_levels():
    """DC18 -> DH3 -> Rack: device on leaf resolves to DC18."""
    calls = []

    def fake_get(url, headers=None, verify=True, timeout=10):
        calls.append(url)
        mock = MagicMock()
        if url.endswith("/api/dcim/locations/30/"):
            mock.status_code = 200
            mock.json.return_value = {
                "id": 30,
                "name": "Rack-A1",
                "parent": {"id": 20, "name": "DH3"},
            }
        elif url.endswith("/api/dcim/locations/20/"):
            mock.status_code = 200
            mock.json.return_value = {
                "id": 20,
                "name": "DH3",
                "parent": {"id": 10, "name": "DC18"},
            }
        elif url.endswith("/api/dcim/locations/10/"):
            mock.status_code = 200
            mock.json.return_value = {
                "id": 10,
                "name": "DC18",
                "parent": None,
            }
        else:
            mock.status_code = 404
            mock.json.return_value = {}
        return mock

    session = MagicMock()
    session.get.side_effect = fake_get

    device = {"location": {"id": 30, "name": "Rack-A1"}, "site": {"name": "ISTANBUL"}}
    out = lh.resolve_root_location_name(
        device,
        "https://netbox.example",
        "token",
        True,
        session=session,
    )
    assert out == "DC18"
    assert session.get.call_count == 3


def test_resolve_root_location_name_no_parent_uses_self():
    """Device directly on root location returns that location name."""
    session = MagicMock()

    def fake_get(url, **kwargs):
        mock = MagicMock()
        mock.status_code = 200
        mock.json.return_value = {
            "id": 10,
            "name": "DC18",
            "parent": None,
        }
        return mock

    session.get.side_effect = fake_get
    device = {"location": {"id": 10, "name": "DC18"}}
    assert (
        lh.resolve_root_location_name(
            device, "https://n/", "t", True, session=session
        )
        == "DC18"
    )


def test_bfs_collect_descendant_location_ids():
    """Root plus two levels of children; pagination not used."""
    session = MagicMock()

    def fake_get(url, **kwargs):
        mock = MagicMock()
        mock.raise_for_status = MagicMock()
        if "parent_id=1" in url:
            mock.json.return_value = {
                "results": [{"id": 2, "name": "Child"}],
                "next": None,
            }
        elif "parent_id=2" in url:
            mock.json.return_value = {
                "results": [{"id": 3, "name": "Grandchild"}],
                "next": None,
            }
        elif "parent_id=3" in url:
            mock.json.return_value = {"results": [], "next": None}
        else:
            mock.json.return_value = {"results": [], "next": None}
        return mock

    session.get.side_effect = fake_get
    ids = lh.bfs_collect_descendant_location_ids(
        "https://n", "t", 1, True, session=session
    )
    assert ids == [1, 2, 3]
