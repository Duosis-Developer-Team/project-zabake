from .customer import customer_code_equal, parse_customer_code_from_name, resolve_customer_code
from .environment import (
    CLASSIC_VMWARE,
    HYPERCONV_NUTANIX,
    HYPERCONV_VMWARE,
    POWER_IBM,
    UNKNOWN,
    classify_from_source,
    classify_netbox_row,
    classify_vmware_cluster,
)
from .keys import normalize_name, normalize_uuid

__all__ = [
    "normalize_name",
    "normalize_uuid",
    "customer_code_equal",
    "parse_customer_code_from_name",
    "resolve_customer_code",
    "CLASSIC_VMWARE",
    "HYPERCONV_VMWARE",
    "HYPERCONV_NUTANIX",
    "POWER_IBM",
    "UNKNOWN",
    "classify_vmware_cluster",
    "classify_from_source",
    "classify_netbox_row",
]
