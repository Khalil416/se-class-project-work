from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException

from backend.db import INVENTORY_DB, connect, log, rows_to_dicts
from backend.schemas.core import WasteLog

router = APIRouter(tags=["waste"])


def _fetch_all_dicts(query: str, params: tuple = ()):
    conn = connect(INVENTORY_DB)
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows_to_dicts(rows)


@router.get("/waste-logs")
def get_waste_logs(item_id: Optional[int] = None):
    try:
        log("GET /waste-logs", {"item_id": item_id})
        query = """
            SELECT
                wl.log_id AS id,
                wl.log_id,
                wl.item_id,
                wl.qty_wasted,
                wl.unit,
                wl.reason,
                wl.waste_date,
                wl.notes,
                wl.cost_estimate,
                i.item_name,
                i.category
            FROM waste_logs wl
            LEFT JOIN inventory i ON i.id = wl.item_id
        """
        params = []

        if item_id is not None:
            query += " WHERE wl.item_id = ?"
            params.append(item_id)

        query += " ORDER BY wl.log_id DESC"
        rows = _fetch_all_dicts(query, tuple(params))
        return {"data": rows, "count": len(rows)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {str(exc)}")


@router.post("/waste-logs")
def create_waste_log(log_item: WasteLog):
    try:
        log("POST /waste-logs", log_item.model_dump())
        conn = connect(INVENTORY_DB)
        cur = conn.cursor()

        waste_date = log_item.waste_date or datetime.now().strftime("%Y-%m-%d")
        cur.execute("SELECT quantity, unit FROM inventory WHERE id = ?", (log_item.item_id,))
        item_row = cur.fetchone()
        if not item_row:
            conn.close()
            return {"error": "Inventory item not found"}

        current_qty = float(item_row[0] or 0)
        if float(log_item.qty_wasted) < 0:
            conn.close()
            return {"error": "qty_wasted must be positive"}
        if float(log_item.qty_wasted) > current_qty + 1e-9:
            conn.close()
            return {"error": f"Cannot waste more than available stock ({current_qty})"}

        new_qty = max(0.0, current_qty - float(log_item.qty_wasted))

        cur.execute(
            """
            INSERT INTO waste_logs (item_id, qty_wasted, unit, reason, waste_date, notes, cost_estimate)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                log_item.item_id,
                log_item.qty_wasted,
                log_item.unit,
                log_item.reason,
                waste_date,
                log_item.notes,
                log_item.cost_estimate,
            ),
        )
        cur.execute("UPDATE inventory SET quantity = ? WHERE id = ?", (new_qty, log_item.item_id))
        conn.commit()
        waste_id = cur.lastrowid
        conn.close()

        return {
            "success": True,
            "message": "Waste log created successfully",
            "id": waste_id,
            "waste_date": waste_date,
            "inventory_quantity": new_qty,
        }
    except Exception as exc:
        return {"error": f"Failed to create waste log: {str(exc)}"}


@router.get("/inventory/{item_id}/waste-logs")
def get_inventory_waste_logs(item_id: int):
    log(f"GET /inventory/{item_id}/waste-logs")
    return get_waste_logs(item_id=item_id)
