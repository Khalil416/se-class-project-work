from datetime import date, datetime, timedelta
from fastapi import APIRouter, Query

from backend.db import INVENTORY_DB, connect, log, rows_to_dicts

router = APIRouter(tags=["analytics"])


def _load_inventory():
    conn = connect(INVENTORY_DB)
    cur = conn.cursor()
    cur.execute("SELECT id, item_name, sku, category, quantity, unit, storage, expiry_date, created_at FROM inventory ORDER BY id")
    rows = rows_to_dicts(cur.fetchall())
    conn.close()
    return rows


def _load_waste_logs():
    conn = connect(INVENTORY_DB)
    cur = conn.cursor()
    cur.execute(
        """
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
        ORDER BY wl.log_id DESC
        """
    )
    rows = rows_to_dicts(cur.fetchall())
    conn.close()
    return rows


def _period_start_date(period: str) -> date:
    """Return the start date for a given period filter."""
    today = date.today()
    if period == "monthly":
        return today - timedelta(days=365)
    elif period == "weekly":
        return today - timedelta(days=27)
    else:  # daily
        return today - timedelta(days=6)


@router.get("/dashboard/stats")
def dashboard_stats():
    log("GET /dashboard/stats")
    inventory_rows = _load_inventory()
    waste_rows = _load_waste_logs()

    total_items = len(inventory_rows)
    items_near_expiry = 0
    items_expired = 0
    today = date.today()
    for row in inventory_rows:
        try:
            exp = datetime.strptime(row.get("expiry_date", ""), "%Y-%m-%d").date()
        except Exception:
            continue
        days_left = (exp - today).days
        if days_left < 0:
            items_expired += 1
        elif days_left <= 7:
            items_near_expiry += 1

    cutoff = (today - timedelta(days=6)).isoformat()
    weekly_waste_cost = sum(float(row.get("cost_estimate") or 0) for row in waste_rows if (row.get("waste_date") or "") >= cutoff)

    return {
        "total_items": total_items,
        "items_near_expiry": items_near_expiry,
        "items_expired": items_expired,
        "weekly_waste_cost": weekly_waste_cost,
    }


@router.get("/dashboard/waste-summary")
def dashboard_waste_summary():
    log("GET /dashboard/waste-summary")
    waste_rows = _load_waste_logs()
    totals = {}
    for row in waste_rows:
        reason = (row.get("reason") or "other").lower()
        entry = totals.setdefault(reason, {"reason": reason, "count": 0, "cost_total": 0.0})
        entry["count"] += 1
        entry["cost_total"] += float(row.get("cost_estimate") or 0)
    return {"data": sorted(totals.values(), key=lambda item: item["cost_total"], reverse=True)}


@router.get("/reports/summary")
def reports_summary(period: str = Query(default="daily")):
    log("GET /reports/summary", {"period": period})
    waste_rows = _load_waste_logs()
    today = date.today()
    start_date = _period_start_date(period)

    if period == "monthly":
        bucket = "month"
    elif period == "weekly":
        bucket = "week"
    else:
        bucket = "day"

    groups = {}
    for row in waste_rows:
        waste_date = row.get("waste_date") or ""
        if waste_date < start_date.isoformat():
            continue
        try:
            dt = datetime.strptime(waste_date[:10], "%Y-%m-%d").date()
        except Exception:
            continue
        if bucket == "month":
            key = dt.strftime("%Y-%m")
            label = dt.strftime("%b")
        elif bucket == "week":
            week_start = dt - timedelta(days=dt.weekday())
            key = week_start.strftime("%Y-%m-%d")
            label = week_start.strftime("%b %d")
        else:
            key = dt.strftime("%Y-%m-%d")
            label = dt.strftime("%b %d")
        entry = groups.setdefault(key, {"label": label, "cost": 0.0})
        entry["cost"] += float(row.get("cost_estimate") or 0)

    ordered = [groups[key] for key in sorted(groups.keys())]
    return {"data": ordered}


@router.get("/reports/by-reason")
def reports_by_reason(period: str = Query(default="daily")):
    log("GET /reports/by-reason", {"period": period})
    waste_rows = _load_waste_logs()
    start_date = _period_start_date(period)

    totals = {}
    for row in waste_rows:
        # Filter by period — without this, all-time data was shown regardless of period
        waste_date = row.get("waste_date") or ""
        if waste_date < start_date.isoformat():
            continue

        reason = (row.get("reason") or "other").lower()
        entry = totals.setdefault(reason, {"reason": reason, "count": 0, "cost_total": 0.0})
        entry["count"] += 1
        entry["cost_total"] += float(row.get("cost_estimate") or 0)
    ordered = sorted(totals.values(), key=lambda item: item["cost_total"], reverse=True)
    return {"data": ordered[:5]}