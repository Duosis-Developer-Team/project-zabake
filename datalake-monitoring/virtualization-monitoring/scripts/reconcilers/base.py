from dataclasses import dataclass

from matchers.customer import customer_code_equal


@dataclass
class MatchResult:
    key: str
    status: str
    datalake: dict | None
    netbox: dict | None


class ReconcilerBase:
    target_name = "unknown"

    def datalake_key(self, row: dict) -> str:
        raise NotImplementedError

    def netbox_key(self, row: dict) -> str:
        raise NotImplementedError

    def cluster_matches(self, datalake: dict, netbox: dict) -> bool:
        dl_cluster = str(datalake.get("cluster") or datalake.get("cluster_name") or "").strip().lower()
        nb_cluster = str(netbox.get("cluster_name") or "").strip().lower()
        return dl_cluster == nb_cluster

    def customer_matches(self, datalake: dict, netbox: dict) -> bool:
        return customer_code_equal(datalake.get("customer_code"), netbox.get("custom_fields_musteri"))

    def reconcile(self, datalake_rows: list[dict], netbox_rows: list[dict]) -> dict:
        datalake_map = {self.datalake_key(row): row for row in datalake_rows if self.datalake_key(row)}
        netbox_map = {self.netbox_key(row): row for row in netbox_rows if self.netbox_key(row)}
        keys = sorted(set(datalake_map.keys()) | set(netbox_map.keys()))

        results = []
        for key in keys:
            dl = datalake_map.get(key)
            nb = netbox_map.get(key)
            if dl and nb:
                status = "in_both_strong"
                if not self.cluster_matches(dl, nb):
                    status = "mismatch_cluster"
                elif not self.customer_matches(dl, nb):
                    status = "mismatch_customer"
                results.append(MatchResult(key=key, status=status, datalake=dl, netbox=nb))
            elif dl:
                results.append(MatchResult(key=key, status="only_in_datalake", datalake=dl, netbox=None))
            else:
                results.append(MatchResult(key=key, status="only_in_netbox", datalake=None, netbox=nb))

        summary = {
            "datalake_count": len(datalake_map),
            "netbox_count": len(netbox_map),
            "in_both_strong": sum(1 for item in results if item.status == "in_both_strong"),
            "only_in_datalake": sum(1 for item in results if item.status == "only_in_datalake"),
            "only_in_netbox": sum(1 for item in results if item.status == "only_in_netbox"),
            "mismatch_cluster": sum(1 for item in results if item.status == "mismatch_cluster"),
            "mismatch_customer": sum(1 for item in results if item.status == "mismatch_customer"),
        }
        return {
            "target": self.target_name,
            "summary": summary,
            "details": [item.__dict__ for item in results],
        }
