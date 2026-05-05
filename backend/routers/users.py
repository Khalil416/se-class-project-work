import sqlite3

from fastapi import APIRouter, HTTPException, Query

from backend.db import REG_DB, connect, log, rows_to_dicts
from backend.schemas.core import UserCreate, UserUpdate

router = APIRouter(tags=["users"])


def _table_columns() -> set:
    conn = connect(REG_DB)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(users)")
    cols = {row[1] for row in cur.fetchall()}
    conn.close()
    return cols


def _base_select_clause() -> str:
    cols = _table_columns()
    select_cols = ["id", "username", "email", "role"]
    if "is_active" in cols:
        select_cols.append("is_active")
    if "created_at" in cols:
        select_cols.append("created_at")
    if "password" in cols:
        select_cols.append("password")
    return ", ".join(select_cols)


def _fetch_one_dict(query: str, params: tuple = ()):
    conn = connect(REG_DB)
    cur = conn.cursor()
    cur.execute(query, params)
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def _fetch_all_dicts(query: str, params: tuple = ()):
    conn = connect(REG_DB)
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows_to_dicts(rows)


@router.get("/users")
def get_users(search: str = Query(default=""), role: str = Query(default="")):
    try:
        log("GET /users", {"search": search, "role": role})
        query = f"SELECT {_base_select_clause()} FROM users WHERE 1=1"
        params = []

        if search:
            query += " AND (username LIKE ? OR email LIKE ?)"
            like = f"%{search}%"
            params.extend([like, like])
        if role:
            query += " AND role = ?"
            params.append(role)

        query += " ORDER BY id"
        rows = _fetch_all_dicts(query, tuple(params))
        return {"data": rows, "count": len(rows)}
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {str(exc)}")


@router.post("/users")
def create_user(user: UserCreate):
    try:
        log("POST /users", user.model_dump())
        conn = connect(REG_DB)
        cur = conn.cursor()

        cur.execute("SELECT id FROM users WHERE username = ?", (user.username,))
        if cur.fetchone():
            conn.close()
            return {"error": "Username already exists"}

        cur.execute("SELECT id FROM users WHERE email = ?", (user.email,))
        if cur.fetchone():
            conn.close()
            return {"error": "Email already exists"}

        cur.execute(
            "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
            (user.username, user.email, user.password, user.role),
        )
        conn.commit()
        user_id = cur.lastrowid
        conn.close()

        return {
            "success": True,
            "message": "User created successfully",
            "id": user_id,
            "username": user.username,
        }
    except sqlite3.IntegrityError as exc:
        return {"error": f"Integrity error: {str(exc)}"}
    except sqlite3.Error as exc:
        return {"error": f"Failed to create user: {str(exc)}"}


@router.get("/users/{user_id}")
def get_user(user_id: int):
    log(f"GET /users/{user_id}")
    row = _fetch_one_dict(
        f"SELECT {_base_select_clause()} FROM users WHERE id = ?",
        (user_id,),
    )
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return row


@router.put("/users/{user_id}")
def update_user(user_id: int, user: UserUpdate):
    log(f"PUT /users/{user_id}", user.model_dump())
    cols = _table_columns()
    fields = []
    params = []

    if user.email is not None:
        fields.append("email = ?")
        params.append(user.email)
    if user.password is not None:
        fields.append("password = ?")
        params.append(user.password)
    if user.role is not None:
        fields.append("role = ?")
        params.append(user.role)
    if user.is_active is not None and "is_active" in cols:
        fields.append("is_active = ?")
        params.append(1 if user.is_active else 0)

    if not fields:
        return {"error": "No fields to update"}

    params.append(user_id)
    try:
        conn = connect(REG_DB)
        cur = conn.cursor()
        cur.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", tuple(params))
        conn.commit()
        updated = cur.rowcount
        conn.close()

        if not updated:
            raise HTTPException(status_code=404, detail="User not found")

        return {"success": True, "message": "User updated successfully"}
    except HTTPException:
        raise
    except sqlite3.IntegrityError as exc:
        return {"error": f"Integrity error: {str(exc)}"}
    except sqlite3.Error as exc:
        return {"error": f"Failed to update user: {str(exc)}"}


@router.patch("/users/{user_id}/active")
def toggle_user_active(user_id: int, is_active: bool):
    log(f"PATCH /users/{user_id}/active", {"is_active": is_active})
    if "is_active" not in _table_columns():
        return {"error": "is_active column is not available in users table"}
    try:
        conn = connect(REG_DB)
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_active = ? WHERE id = ?", (1 if is_active else 0, user_id))
        conn.commit()
        updated = cur.rowcount
        conn.close()

        if not updated:
            raise HTTPException(status_code=404, detail="User not found")

        return {"success": True, "message": "User status updated successfully"}
    except HTTPException:
        raise
    except sqlite3.Error as exc:
        return {"error": f"Failed to update status: {str(exc)}"}


@router.delete("/users/{user_id}")
def delete_user(user_id: int):
    log(f"DELETE /users/{user_id}")
    try:
        conn = connect(REG_DB)
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        deleted = cur.rowcount
        conn.close()

        if not deleted:
            raise HTTPException(status_code=404, detail="User not found")

        return {"success": True, "message": "User deleted successfully"}
    except HTTPException:
        raise
    except sqlite3.Error as exc:
        return {"error": f"Failed to delete user: {str(exc)}"}
