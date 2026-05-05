from datetime import datetime

from backend.db import INVENTORY_DB, connect


def get_next_sku() -> str:
    try:
        conn = connect(INVENTORY_DB)
        cur = conn.cursor()
        cur.execute("SELECT sku FROM inventory WHERE sku LIKE 'SKU-%' ORDER BY CAST(SUBSTR(sku, 5) AS INTEGER) DESC LIMIT 1")
        row = cur.fetchone()
        conn.close()

        if row:
            last_sku = row[0]
            last_num = int(last_sku.split("-")[1])
            next_num = last_num + 1
        else:
            next_num = 1

        return f"SKU-{next_num:05d}"
    except Exception:
        return "SKU-00001"


def inventory_status(expiry_date: str) -> str:
    try:
        exp = datetime.strptime(expiry_date, "%Y-%m-%d").date()
    except Exception:
        return "Fresh"

    today = datetime.now().date()
    days_left = (exp - today).days
    if days_left < 0:
        return "Expired"
    if days_left <= 7:
        return "Expiring Soon"
    return "Fresh"
