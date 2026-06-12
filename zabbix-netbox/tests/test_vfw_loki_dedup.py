"""Unit tests for Loki virtual firewall fetch composite dedup logic."""


def parse_vfw_ip(ip_port):
    s = str(ip_port or "").strip()
    if not s:
        return ""
    if ":" in s:
        return s.rsplit(":", 1)[0].strip()
    return s


def composite_dedup_key(fw):
    ip = parse_vfw_ip(fw.get("ip_port"))
    host = str(fw.get("hostname") or "").strip().lower()
    if not ip or not host:
        return None
    return (ip, host)


def dedupe_vfw_by_ip_hostname(records):
    by_composite = {}
    no_composite = []
    skipped = []
    for fw in records:
        key = composite_dedup_key(fw)
        if key is None:
            no_composite.append(fw)
            continue
        fid = fw.get("id")
        if key not in by_composite:
            by_composite[key] = fw
            continue
        existing = by_composite[key]
        existing_id = existing.get("id")
        keep_current = False
        if fid is not None and existing_id is not None:
            keep_current = int(fid) < int(existing_id)
        if keep_current:
            skipped.append({"id": existing_id, "kept_id": fid})
            by_composite[key] = fw
        else:
            skipped.append({"id": fid, "kept_id": existing_id})
    return list(by_composite.values()) + no_composite, skipped


def test_composite_dedup_keeps_lowest_id():
    records = [
        {"id": 1884, "hostname": "ADILE SULTAN_EV_YEMEKLERI", "ip_port": "91.108.216.173:443"},
        {"id": 727, "hostname": "ADILE SULTAN_EV_YEMEKLERI", "ip_port": "91.108.216.173:443"},
    ]
    kept, skipped = dedupe_vfw_by_ip_hostname(records)
    assert len(kept) == 1
    assert kept[0]["id"] == 727
    assert len(skipped) == 1
    assert skipped[0]["id"] == 1884
    assert skipped[0]["kept_id"] == 727


def test_composite_dedup_allows_different_ip_or_hostname():
    records = [
        {"id": 1, "hostname": "FW-A", "ip_port": "10.0.0.1:443"},
        {"id": 2, "hostname": "FW-B", "ip_port": "10.0.0.1:443"},
        {"id": 3, "hostname": "FW-A", "ip_port": "10.0.0.2:443"},
    ]
    kept, skipped = dedupe_vfw_by_ip_hostname(records)
    assert len(kept) == 3
    assert skipped == []
