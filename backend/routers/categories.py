import sqlite3

from fastapi import APIRouter, HTTPException, Query

from backend.db import INVENTORY_DB, connect, log, rows_to_dicts
from backend.schemas.core import CategoryCreate, CategoryUpdate

router = APIRouter(tags=["categories"])


def _fetch_all_dicts(query: str, params: tuple = ()):
    conn = connect(INVENTORY_DB)
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows_to_dicts(rows)


@router.get("/categories")
def get_categories(search_text: str = Query(default="")):
    log("GET /categories", {"search_text": search_text})
    try:
        query = "SELECT category_id, category_name, description, shelf_life_days FROM categories WHERE 1=1"
        params = []
        if search_text:
            query += " AND (category_name LIKE ? OR description LIKE ?)"
            like = f"%{search_text}%"
            params.extend([like, like])
        query += " ORDER BY category_name COLLATE NOCASE"

        rows = _fetch_all_dicts(query, tuple(params))
        return {"data": rows, "count": len(rows)}
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {str(exc)}")


@router.post("/categories")
def create_category(category: CategoryCreate):
    log("POST /categories", category.model_dump())
    try:
        conn = connect(INVENTORY_DB)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO categories (category_name, description, shelf_life_days) VALUES (?, ?, ?)",
            (category.category_name, category.description or "", category.shelf_life_days),
        )
        conn.commit()
        category_id = cur.lastrowid
        conn.close()
        return {"success": True, "id": category_id}
    except sqlite3.IntegrityError as exc:
        return {"error": f"Integrity error: {str(exc)}"}
    except sqlite3.Error as exc:
        return {"error": f"Failed to create category: {str(exc)}"}


@router.put("/categories/{category_id}")
def update_category(category_id: int, category: CategoryUpdate):
    log(f"PUT /categories/{category_id}", category.model_dump())
    fields = []
    params = []

    if category.category_name is not None:
        fields.append("category_name = ?")
        params.append(category.category_name)
    if category.description is not None:
        fields.append("description = ?")
        params.append(category.description)
    if category.shelf_life_days is not None:
        fields.append("shelf_life_days = ?")
        params.append(category.shelf_life_days)

    if not fields:
        return {"error": "No fields to update"}

    params.append(category_id)
    try:
        conn = connect(INVENTORY_DB)
        cur = conn.cursor()
        cur.execute(f"UPDATE categories SET {', '.join(fields)} WHERE category_id = ?", tuple(params))
        conn.commit()
        updated = cur.rowcount
        conn.close()

        if not updated:
            raise HTTPException(status_code=404, detail="Category not found")

        return {"success": True, "message": "Category updated successfully"}
    except HTTPException:
        raise
    except sqlite3.IntegrityError as exc:
        return {"error": f"Integrity error: {str(exc)}"}
    except sqlite3.Error as exc:
        return {"error": f"Failed to update category: {str(exc)}"}


@router.delete("/categories/{category_id}")
def delete_category(category_id: int):
    log(f"DELETE /categories/{category_id}")
    try:
        conn = connect(INVENTORY_DB)
        cur = conn.cursor()
        cur.execute("DELETE FROM categories WHERE category_id = ?", (category_id,))
        conn.commit()
        deleted = cur.rowcount
        conn.close()

        if not deleted:
            raise HTTPException(status_code=404, detail="Category not found")

        return {"success": True, "message": "Category deleted successfully"}
    except HTTPException:
        raise
    except sqlite3.Error as exc:
        return {"error": f"Failed to delete category: {str(exc)}"}
