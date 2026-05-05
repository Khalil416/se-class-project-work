from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from backend.db import INVENTORY_DB, connect, log, rows_to_dicts
from backend.common.helpers import get_next_sku, inventory_status
from backend.schemas.core import InventoryItem

router = APIRouter(tags=["inventory"])


def _fetch_one_dict(query: str, params: tuple = ()):
    conn = connect(INVENTORY_DB)
    cur = conn.cursor()
    cur.execute(query, params)
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def _fetch_all_dicts(query: str, params: tuple = ()):
    conn = connect(INVENTORY_DB)
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows_to_dicts(rows)


@router.get("/inventory")
def get_inventory(
    search: str = Query(default=""),
    category: str = Query(default=""),
    status: str = Query(default=""),
    storage: str = Query(default=""),
):
    try:
        log("GET /inventory", {"search": search, "category": category, "status": status, "storage": storage})
        query = "SELECT id, item_name, sku, category, quantity, unit, storage, expiry_date, created_at FROM inventory WHERE 1=1"
        params = []

        if search:
            query += " AND (item_name LIKE ? OR sku LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        if category:
            query += " AND category = ?"
            params.append(category)
        if storage:
            query += " AND storage = ?"
            params.append(storage)

        query += " ORDER BY id"
        rows = _fetch_all_dicts(query, tuple(params))

        if status:
            rows = [row for row in rows if inventory_status(row.get("expiry_date", "")) == status]

        return {"data": rows, "count": len(rows)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {str(exc)}")


@router.post("/inventory")
def create_inventory_item(item: InventoryItem):
    if not item.item_name or not item.item_name.strip():
        return {"error": "item_name is required and cannot be empty"}

    try:
        log("POST /inventory", item.model_dump())
        conn = connect(INVENTORY_DB)
        cur = conn.cursor()

        sku = get_next_sku()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cur.execute(
            """
            INSERT INTO inventory (item_name, sku, category, quantity, unit, storage, expiry_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (item.item_name, sku, item.category, item.quantity, item.unit, item.storage, item.expiry_date, created_at),
        )
        conn.commit()
        item_id = cur.lastrowid
        conn.close()

        return {
            "success": True,
            "message": "Item added successfully",
            "id": item_id,
            "sku": sku,
            "created_at": created_at,
        }
    except Exception as exc:
        return {"error": f"Failed to create item: {str(exc)}"}


@router.get("/inventory/{item_id}")
def get_inventory_item(item_id: int):
    log(f"GET /inventory/{item_id}")
    row = _fetch_one_dict("SELECT * FROM inventory WHERE id = ?", (item_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return row


@router.put("/inventory/{item_id}")
def update_inventory_item(item_id: int, item: InventoryItem):
    log(f"PUT /inventory/{item_id}", item.model_dump())
    try:
        conn = connect(INVENTORY_DB)
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE inventory
            SET item_name = ?, category = ?, quantity = ?, unit = ?, storage = ?, expiry_date = ?
            WHERE id = ?
            """,
            (item.item_name, item.category, item.quantity, item.unit, item.storage, item.expiry_date, item_id),
        )
        conn.commit()
        updated = cur.rowcount
        conn.close()

        if not updated:
            raise HTTPException(status_code=404, detail="Inventory item not found")

        return {"success": True, "message": "Inventory item updated successfully"}
    except HTTPException:
        raise
    except Exception as exc:
        return {"error": f"Failed to update item: {str(exc)}"}


@router.delete("/inventory/{item_id}")
def delete_inventory_item(item_id: int):
    log(f"DELETE /inventory/{item_id}")
    try:
        conn = connect(INVENTORY_DB)
        cur = conn.cursor()
        cur.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
        conn.commit()
        deleted = cur.rowcount
        conn.close()

        if not deleted:
            raise HTTPException(status_code=404, detail="Inventory item not found")

        return {"success": True, "message": "Inventory item deleted successfully"}
    except HTTPException:
        raise
    except Exception as exc:
        return {"error": f"Failed to delete item: {str(exc)}"}
