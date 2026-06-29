"""Inicializa la base de datos SQLite ejecutando database/schema.sql.

Uso: python scripts/init_db.py [--db data/conectamax.db]
"""
from __future__ import annotations
import argparse
import os
import sqlite3

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def init_db(db_path: str, schema_path: str | None = None) -> None:
    if schema_path is None:
        schema_path = os.path.join(RAIZ, "database", "schema.sql")
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys = ON")
    with open(schema_path, encoding="utf-8") as fh:
        con.executescript(fh.read())
    con.commit()
    con.close()
    print(f"BD inicializada: {db_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/conectamax.db")
    ap.add_argument("--schema", default=None)
    a = ap.parse_args()
    init_db(a.db, a.schema)
