"""
Host metadata for reports: Zabbix host tags, linked templates, main interface IP, proxy group name.
"""

from typing import Any, Dict, List, Tuple

# Standard report tag names (case-insensitive match on tag name)
STANDARD_TAG_NAMES: Tuple[str, ...] = ("Location", "Contact", "Tenant")

# monitored_by: 0 = server, 1 = proxy, 2 = proxy group (Zabbix 7)
MONITORED_BY_PROXY_GROUP = "2"


def extract_standard_host_tags(host_tags: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Read Location, Contact, Tenant from Zabbix host tags.
    Tag name matching is case-insensitive; output keys are lowercase.
    """
    out = {"location": "", "contact": "", "tenant": ""}
    if not host_tags:
        return out
    
    wanted = {n.lower(): n for n in STANDARD_TAG_NAMES}
    for entry in host_tags:
        tag_name = (entry.get("tag") or "").strip()
        if not tag_name:
            continue
        key = wanted.get(tag_name.lower())
        if key:
            out[key.lower()] = (entry.get("value") or "").strip()
    return out


def extract_host_template_names(host: Dict[str, Any]) -> str:
    """
    Comma-separated names of all templates linked to the host (parentTemplates).
    Sorted alphabetically for stable output.
    """
    parents = host.get("parentTemplates") or []
    names: List[str] = []
    for entry in parents:
        name = (entry.get("name") or "").strip()
        if name and name not in names:
            names.append(name)
    names.sort()
    return ", ".join(names)


def extract_main_interface_ip(interfaces: List[Dict[str, Any]]) -> str:
    """
    Prefer the default interface (main == '1'); otherwise first non-empty ip.
    """
    if not interfaces:
        return ""
    
    for iface in interfaces:
        if str(iface.get("main", "")) == "1":
            ip = (iface.get("ip") or "").strip()
            if ip:
                return ip
    
    for iface in interfaces:
        ip = (iface.get("ip") or "").strip()
        if ip:
            return ip
    
    return ""


def _proxy_group_name_for_host(
    host: Dict[str, Any],
    proxy_id_to_name: Dict[str, str],
) -> str:
    monitored = str(host.get("monitored_by", "")).strip()
    if monitored != MONITORED_BY_PROXY_GROUP:
        return ""
    
    pgid = host.get("proxy_groupid")
    if pgid is None:
        return ""
    sid = str(pgid).strip()
    if not sid or sid == "0":
        return ""
    
    return proxy_id_to_name.get(sid, "")


def build_host_metadata_map(
    hosts: List[Dict[str, Any]],
    proxy_id_to_name: Dict[str, str],
) -> Dict[str, Dict[str, str]]:
    """
    Build hostid -> metadata for report rows.
    Keys: location, contact, tenant, interface_ip, proxy_group_name, host_templates.
    """
    result: Dict[str, Dict[str, str]] = {}
    
    for host in hosts:
        host_id = host.get("hostid")
        if not host_id:
            continue
        
        tags = host.get("tags") or []
        tag_fields = extract_standard_host_tags(tags)
        interfaces = host.get("interfaces") or []
        interface_ip = extract_main_interface_ip(interfaces)
        proxy_group_name = _proxy_group_name_for_host(host, proxy_id_to_name)
        host_templates = extract_host_template_names(host)
        
        result[str(host_id)] = {
            "location": tag_fields["location"],
            "contact": tag_fields["contact"],
            "tenant": tag_fields["tenant"],
            "interface_ip": interface_ip,
            "proxy_group_name": proxy_group_name,
            "host_templates": host_templates,
        }
    
    return result


def collect_unique_proxy_group_ids(hosts: List[Dict[str, Any]]) -> List[str]:
    """Collect non-zero proxy_groupid values for hosts monitored by proxy group."""
    ids: List[str] = []
    for host in hosts:
        if str(host.get("monitored_by", "")).strip() != MONITORED_BY_PROXY_GROUP:
            continue
        pgid = host.get("proxy_groupid")
        if pgid is None:
            continue
        sid = str(pgid).strip()
        if not sid or sid == "0":
            continue
        if sid not in ids:
            ids.append(sid)
    return ids
