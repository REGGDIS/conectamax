"""Inicializa la base de datos SQLite ejecutando database/schema.sql.

Uso: python scripts/init_db.py [--db data/conectamax.db]
"""
from __future__ import annotations
import argparse
import os
import sqlite3

from _paths import default_db, schema_path


def init_db(db_path: str, schema: str | None = None) -> None:
    schema = schema or schema_path()
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    con = sqlite3.connect(db_path)
    try:
        con.execute("PRAGMA foreign_keys = ON")
        con.executescript(open(schema, encoding="utf-8").read())
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
    print(f"BD inicializada: {db_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=default_db())
    ap.add_argument("--schema", default=None)
    a = ap.parse_args()
    init_db(a.db, a.schema)
