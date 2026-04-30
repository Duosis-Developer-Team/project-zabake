import json

from psycopg2.extras import Json

from utils.db import fetch_all


def upsert_reconciliation_results(connection, table: str, payload: dict, window_days: int) -> None:
    run_id = payload["run_id"]
    for target_payload in payload["targets"]:
        target = target_payload["target"]
        summary = Json(target_payload["summary"])
        details = Json(target_payload["details"])
        query = f"""
            INSERT INTO {table} (run_id, target, window_days, summary, details)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (run_id, target)
            DO UPDATE SET
                window_days = EXCLUDED.window_days,
                summary = EXCLUDED.summary,
                details = EXCLUDED.details
        """
        with connection.cursor() as cursor:
            cursor.execute(query, (run_id, target, window_days, summary, details))
    connection.commit()
