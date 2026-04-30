import importlib.util
from pathlib import Path


def _import_module(module_path: Path):
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_gui_sql_strings(gui_repo_path: str) -> dict:
    base = Path(gui_repo_path)
    vmware_file = base / "services/datacenter-api/app/db/queries/vmware.py"
    customer_file = base / "src/queries/customer.py"

    vmware_module = _import_module(vmware_file)
    customer_module = _import_module(customer_file)
    return {
        "CLASSIC_METRICS": getattr(vmware_module, "CLASSIC_METRICS", ""),
        "HYPERCONV_METRICS": getattr(vmware_module, "HYPERCONV_METRICS", ""),
        "IBM_LPAR_TOTALS": getattr(customer_module, "IBM_LPAR_TOTALS", ""),
        "CUSTOMER_VM_DEDUP": getattr(customer_module, "CUSTOMER_VM_DEDUP", ""),
    }
