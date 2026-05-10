from matchers.environment import (
    CLASSIC_VMWARE,
    HYPERCONV_NUTANIX,
    HYPERCONV_VMWARE,
    POWER_IBM,
    UNKNOWN,
    classify_from_source,
    classify_netbox_row,
    classify_vmware_cluster,
)


def test_classify_vmware_cluster_km_and_non_km():
    assert classify_vmware_cluster("KM-Cluster-01") == CLASSIC_VMWARE
    assert classify_vmware_cluster("prod-hyperconv-01") == HYPERCONV_VMWARE
    assert classify_vmware_cluster("") == UNKNOWN


def test_classify_from_source():
    assert classify_from_source("vmware", "km-cluster-02") == CLASSIC_VMWARE
    assert classify_from_source("nutanix", "ahv-01") == HYPERCONV_NUTANIX
    assert classify_from_source("ibm_lpar", "srv-01") == POWER_IBM
    assert classify_from_source("other", "x") == UNKNOWN


def test_classify_netbox_row_with_cluster_sets():
    row_vmware = {"name": "vm-1", "cluster_name": "km-cluster-a"}
    row_nutanix = {"name": "vm-2", "cluster_name": "ahv-cluster-a"}
    row_ibm = {"name": "lpar-a", "cluster_name": ""}
    row_unknown = {"name": "mystery-vm", "cluster_name": "unknown-cluster"}

    vmware_clusters = {"km-cluster-a", "vcf-cluster-b"}
    nutanix_clusters = {"ahv-cluster-a"}
    ibm_names = {"lpar-a"}

    assert classify_netbox_row(row_vmware, vmware_clusters, nutanix_clusters, ibm_names) == CLASSIC_VMWARE
    assert classify_netbox_row(row_nutanix, vmware_clusters, nutanix_clusters, ibm_names) == HYPERCONV_NUTANIX
    assert classify_netbox_row(row_ibm, vmware_clusters, nutanix_clusters, ibm_names) == POWER_IBM
    assert classify_netbox_row(row_unknown, vmware_clusters, nutanix_clusters, ibm_names) == UNKNOWN
