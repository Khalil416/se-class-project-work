import sqlite3
from datetime import datetime

INVENTORY_DB = "inventory.db"
REG_DB = "reg.db"


def connect(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def rows_to_dicts(rows):
    return [dict(row) for row in rows] if rows else []


def log(message: str, payload=None):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if payload is None:
        print(f"[API] {stamp} {message}")
    else:
        print(f"[API] {stamp} {message}: {payload}")
