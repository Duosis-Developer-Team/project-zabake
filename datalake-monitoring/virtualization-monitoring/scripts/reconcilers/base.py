from dataclasses import dataclass
from typing import Optional

from matchers.customer import customer_code_equal, parse_customer_code_from_name, resolve_customer_code
from matchers.environment import classify_from_source, classify_netbox_row


@dataclass
class MatchResult:
    key: str
    status: str
    source: str
    environment: str
    vm_uuid: str
    vm_name: str
    datalake_cluster: str
    loki_cluster: str
    cluster_match: str
    customer: str
    datalake: Optional[dict]
    netbox: Optional[dict]


class ReconcilerBase:
    target_name = "unknown"
    source_name = "unknown"

    def __init__(
        self,
        vmware_cluster_set: Optional[set[str]] = None,
        nutanix_cluster_set: Optional[set[str]] = None,
        ibm_lpar_name_set: Optional[set[str]] = None,
    ) -> None:
        self.vmware_cluster_set = vmware_cluster_set or set()
        self.nutanix_cluster_set = nutanix_cluster_set or set()
        self.ibm_lpar_name_set = ibm_lpar_name_set or set()

    def datalake_key(self, row: dict) -> str:
        raise NotImplementedError

    def netbox_key(self, row: dict) -> str:
        raise NotImplementedError

    def is_relevant_netbox_row(self, row: dict) -> bool:
        return True

    def cluster_matches(self, datalake: dict, netbox: dict) -> bool:
        dl_cluster = str(datalake.get("cluster") or datalake.get("cluster_name") or "").strip().lower()
        nb_cluster = str(netbox.get("cluster_name") or "").strip().lower()
        return dl_cluster == nb_cluster

    def customer_matches(self, datalake: dict, netbox: dict) -> bool:
        datalake_customer = resolve_customer_code(datalake)
        netbox_customer = (
            resolve_customer_code({"customer_code": netbox.get("custom_fields_musteri")})
            or parse_customer_code_from_name(netbox.get("name"))
        )
        if not datalake_customer or not netbox_customer:
            return True
        return customer_code_equal(datalake_customer, netbox_customer)

    def vm_uuid_from_rows(self, datalake: Optional[dict], netbox: Optional[dict]) -> str:
        if datalake:
            return str(
                datalake.get("uuid") or datalake.get("vm_uuid") or datalake.get("custom_fields_uuid") or ""
            ).strip()
        if netbox:
            return str(netbox.get("custom_fields_uuid") or "").strip()
        return ""

    def vm_name_from_rows(self, datalake: Optional[dict], netbox: Optional[dict]) -> str:
        if datalake:
            name = datalake.get("vmname") or datalake.get("vm_name") or datalake.get("lparname") or datalake.get("name")
            if name:
                return str(name).strip()
        if netbox:
            return str(netbox.get("name") or "").strip()
        return ""

    def _customer_for_row(self, datalake: Optional[dict], netbox: Optional[dict]) -> str:
        datalake_customer = resolve_customer_code(datalake)
        if datalake_customer:
            return datalake_customer
        if not netbox:
            return ""
        return resolve_customer_code({"customer_code": netbox.get("custom_fields_musteri")}) or parse_customer_code_from_name(
            netbox.get("name")
        )

    def _environment_for_row(self, datalake: Optional[dict], netbox: Optional[dict]) -> str:
        if datalake:
            return classify_from_source(self.source_name, str(datalake.get("cluster") or datalake.get("cluster_name") or ""))
        if not netbox:
            return "unknown"
        return classify_netbox_row(
            netbox,
            self.vmware_cluster_set,
            self.nutanix_cluster_set,
            self.ibm_lpar_name_set,
        )

    def _build_match_result(self, key: str, status: str, dl: Optional[dict], nb: Optional[dict]) -> MatchResult:
        datalake_cluster = str((dl or {}).get("cluster") or (dl or {}).get("cluster_name") or "").strip()
        loki_cluster = str((nb or {}).get("cluster_name") or "").strip()
        if status in {"in_both", "cluster_mismatch", "customer_mismatch"}:
            cluster_match = "Y" if status == "in_both" else "N"
        else:
            cluster_match = "N/A"
        return MatchResult(
            key=key,
            status=status,
            source=self.source_name,
            environment=self._environment_for_row(dl, nb),
            vm_uuid=self.vm_uuid_from_rows(dl, nb),
            vm_name=self.vm_name_from_rows(dl, nb),
            datalake_cluster=datalake_cluster,
            loki_cluster=loki_cluster,
            cluster_match=cluster_match,
            customer=self._customer_for_row(dl, nb),
            datalake=dl,
            netbox=nb,
        )

    def reconcile(self, datalake_rows: list[dict], netbox_rows: list[dict]) -> dict:
        datalake_map = {self.datalake_key(row): row for row in datalake_rows if self.datalake_key(row)}
        netbox_map = {
            self.netbox_key(row): row
            for row in netbox_rows
            if self.netbox_key(row) and self.is_relevant_netbox_row(row)
        }
        keys = sorted(set(datalake_map.keys()) | set(netbox_map.keys()))

        results = []
        for key in keys:
            dl = datalake_map.get(key)
            nb = netbox_map.get(key)
            if dl and nb:
                status = "in_both"
                if not self.cluster_matches(dl, nb):
                    status = "mismatch_cluster"
                elif not self.customer_matches(dl, nb):
                    status = "mismatch_customer"
                if status == "mismatch_cluster":
                    status = "cluster_mismatch"
                if status == "mismatch_customer":
                    status = "customer_mismatch"
                results.append(self._build_match_result(key, status, dl, nb))
            elif dl:
                results.append(self._build_match_result(key, "only_in_datalake", dl, None))
            else:
                results.append(self._build_match_result(key, "only_in_loki", None, nb))

        summary = {
            "datalake_count": len(datalake_map),
            "netbox_count": len(netbox_map),
            "in_both": sum(1 for item in results if item.status == "in_both"),
            "only_in_datalake": sum(1 for item in results if item.status == "only_in_datalake"),
            "only_in_loki": sum(1 for item in results if item.status == "only_in_loki"),
            "cluster_mismatch": sum(1 for item in results if item.status == "cluster_mismatch"),
            "customer_mismatch": sum(1 for item in results if item.status == "customer_mismatch"),
        }
        rows = [
            {
                "source": item.source,
                "environment": item.environment,
                "vm_uuid": item.vm_uuid,
                "vm_name": item.vm_name,
                "datalake_cluster": item.datalake_cluster,
                "loki_cluster": item.loki_cluster,
                "cluster_match": item.cluster_match,
                "customer": item.customer,
                "status": item.status,
            }
            for item in results
        ]
        return {
            "target": self.target_name,
            "summary": summary,
            "details": [item.__dict__ for item in results],
            "rows": rows,
        }
