from fastapi import APIRouter, HTTPException

from backend.db import INVENTORY_DB, REG_DB, connect, rows_to_dicts

router = APIRouter(tags=["system"])


@router.get("/")
def read_root():
    return {
        "message": "Welcome to Kitchen Waste Tracker API",
        "version": "1.0.0",
        "endpoints": {
            "inventory": "GET/POST /inventory",
            "waste_logs": "GET/POST /waste-logs",
            "users": "GET/POST /users",
            "database": "GET /database",
        },
    }


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/database")
def get_database():
    result = {"inventory_db": {}, "reg_db": {}}

    try:
        conn = connect(INVENTORY_DB)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cur.fetchall()

        for (table_name,) in tables:
            cur.execute(f"SELECT * FROM {table_name}")
            rows = cur.fetchall()
            result["inventory_db"][table_name] = rows_to_dicts(rows)

        conn.close()

        conn = connect(REG_DB)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cur.fetchall()

        for (table_name,) in tables:
            cur.execute(f"SELECT * FROM {table_name}")
            rows = cur.fetchall()
            result["reg_db"][table_name] = rows_to_dicts(rows)

        conn.close()
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {str(exc)}")
