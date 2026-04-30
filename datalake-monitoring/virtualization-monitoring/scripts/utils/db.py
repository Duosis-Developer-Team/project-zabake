from dataclasses import dataclass
from typing import Any

import psycopg2
import psycopg2.extras


@dataclass
class DbConfig:
    host: str
    port: int
    name: str
    user: str
    password: str


def connect(config: DbConfig):
    return psycopg2.connect(
        host=config.host,
        port=config.port,
        dbname=config.name,
        user=config.user,
        password=config.password,
    )


def fetch_all(connection, query: str, params: tuple[Any, ...] = ()) -> list[dict]:
    with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
