import os
from dataclasses import dataclass

from utils.db import DbConfig


@dataclass
class Settings:
    datalake_db: DbConfig
    netbox_db: DbConfig
    reconciliation_db: DbConfig
    log_level: str


def _read_db(prefix: str) -> DbConfig:
    return DbConfig(
        host=os.getenv(f"{prefix}_HOST", ""),
        port=int(os.getenv(f"{prefix}_PORT", "5432")),
        name=os.getenv(f"{prefix}_NAME", ""),
        user=os.getenv(f"{prefix}_USER", ""),
        password=os.getenv(f"{prefix}_PASSWORD", ""),
    )


def load_settings() -> Settings:
    return Settings(
        datalake_db=_read_db("DATALAKE_DB"),
        netbox_db=_read_db("NETBOX_DB"),
        reconciliation_db=_read_db("RECONCILIATION_DB"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
