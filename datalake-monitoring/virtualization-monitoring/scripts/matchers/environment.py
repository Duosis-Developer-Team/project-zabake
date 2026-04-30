from typing import Iterable

from .keys import normalize_name

CLASSIC_VMWARE = "classic_vmware"
HYPERCONV_VMWARE = "hyperconv_vmware"
HYPERCONV_NUTANIX = "hyperconv_nutanix"
POWER_IBM = "power_ibm"
UNKNOWN = "unknown"


def classify_vmware_cluster(cluster: str) -> str:
    normalized = normalize_name(cluster)
    if not normalized:
        return UNKNOWN
    return CLASSIC_VMWARE if "km" in normalized else HYPERCONV_VMWARE


def classify_from_source(source: str, cluster_name: str) -> str:
    normalized_source = normalize_name(source)
    if normalized_source == "vmware":
        return classify_vmware_cluster(cluster_name)
    if normalized_source == "nutanix":
        return HYPERCONV_NUTANIX
    if normalized_source == "ibm_lpar":
        return POWER_IBM
    return UNKNOWN


def classify_netbox_row(
    row: dict,
    vmware_cluster_set: Iterable[str],
    nutanix_cluster_set: Iterable[str],
    ibm_lpar_name_set: Iterable[str],
) -> str:
    vm_name = normalize_name(row.get("name"))
    cluster_name = normalize_name(row.get("cluster_name"))
    vmware_clusters = {normalize_name(item) for item in vmware_cluster_set if normalize_name(item)}
    nutanix_clusters = {normalize_name(item) for item in nutanix_cluster_set if normalize_name(item)}
    ibm_names = {normalize_name(item) for item in ibm_lpar_name_set if normalize_name(item)}

    if vm_name and vm_name in ibm_names:
        return POWER_IBM
    if cluster_name and cluster_name in vmware_clusters:
        return classify_vmware_cluster(cluster_name)
    if cluster_name and cluster_name in nutanix_clusters:
        return HYPERCONV_NUTANIX
    return UNKNOWN
