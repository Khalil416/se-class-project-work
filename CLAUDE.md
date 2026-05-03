# Kitchen Food Waste Tracker

A role-based restaurant kitchen management desktop app built with Flet (Python).
Tracks food inventory, monitors expiry dates, logs waste, and produces analytics —
with role-gated access for Chefs, Inventory Staff, and Managers.

> Repo: https://github.com/Khalil416/se-class-project-work
> University project — Software Engineering course, Semester 6.

---

## 1. Tech Stack

- **UI framework:** Flet (`import flet as ft`)
- **Charts:** `flet_charts` (used in dashboard and reports)
- **Language:** Python 3.x
- **Databases:** SQLite (file-based)
  - `reg.db` — users table (auth, roles)
  - `inventory.db` — inventory, waste_logs, categories tables
- **Auth:** Plain-text passwords (academic project — do NOT add bcrypt)
- **Session:** `page.session.store` (in-memory key/value)
- **Routing:** `page.route` + `route_change()` middleware in `main.py`
- **Theme:** Orange-based (`#E68A17`), light + dark mode supported

Desktop app only. Window: 1440x900, min 1100x760.

---

## 2. Project Structure

```
ProjectWork/
├── main.py
├── CLAUDE.md
├── reg.db                     # users table
├── inventory.db               # inventory, waste_logs, categories
├── assets/logo.png
├── .gitignore
└── views/
    ├── login.py               # route: "/"
    ├── dashboard.py           # route: "/dashboard"
    ├── inventory.py           # route: "/inventory"
    ├── add_item.py            # route: "/add-item"
    ├── item_detail.py         # route: "/item/{id}"
    ├── waste_new.py           # route: "/waste/new"
    ├── expiry_monitor.py      # route: "/expiry"
    ├── waste_logs.py          # route: "/waste-logs"
    ├── reports.py             # route: "/reports"
    ├── categories.py          # route: "/categories"
    └── users_staff.py         # route: "/users"
```

---

## 3. Routing & Auth

`route_change()` in `main.py`:
1. Read `is_logged_in` and `role` from `page.session.store`.
2. Unauthenticated → redirect to `/`.
3. Role-based redirects to `/dashboard` if unauthorized:
   - Manager-only: `/reports`, `/categories`, `/users`
   - Manager + Inventory Staff: `/expiry`, `/waste-logs`
   - Chef + Manager: `/waste/new`
4. `page.views.clear()` → append `login_view(page)` → append matched view.
5. `page.update()`.

**Session keys:**
- `is_logged_in` (bool)
- `username` (str)
- `role` (str: `'chef'` | `'inventory_staff'` | `'manager'`)
- `edit_item_id` (int, optional)

---

## 4. Database Schema

### reg.db — users
```sql
CREATE TABLE users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT NOT NULL UNIQUE,
    email       TEXT NOT NULL UNIQUE,
    password    TEXT NOT NULL,
    role        TEXT DEFAULT 'chef',
    is_active   INTEGER DEFAULT 1,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
)
```
**Seeded on startup:** `username='manager', password='1234', role='manager'` (head manager).

**Head manager rules:**
- Only `username='manager'` can edit/deactivate other manager accounts.
- Regular managers can only edit chef and inventory_staff users.
- The `username='manager'` account cannot be edited or deactivated by anyone.

**Login rules:**
- `is_active=0` → blocked: "Account deactivated. Contact your manager."

### inventory.db — inventory
```sql
CREATE TABLE inventory (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name       TEXT NOT NULL,
    sku             TEXT NOT NULL UNIQUE,
    category        TEXT NOT NULL,
    quantity        REAL NOT NULL,
    unit            TEXT NOT NULL,
    storage         TEXT NOT NULL,
    expiry_date     TEXT NOT NULL,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
    purchase_date   TEXT DEFAULT '',
    internal_notes  TEXT DEFAULT '',
    batch_number    TEXT DEFAULT '',
    alert_threshold INTEGER DEFAULT 3
)
```
Status (Fresh / Expiring Soon / Expired) is computed in Python, never stored.

### inventory.db — waste_logs
```sql
CREATE TABLE waste_logs (
    log_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id       INTEGER,
    qty_wasted    REAL NOT NULL,
    unit          TEXT NOT NULL,
    reason        TEXT NOT NULL,
    waste_date    TEXT NOT NULL,
    notes         TEXT,
    cost_estimate REAL
)
```
Valid reasons: `expired`, `spoiled`, `prep_waste`, `overproduction`, `damaged`, `other`.
Cost estimate = `qty_wasted x 10` (placeholder rate).

### inventory.db — categories
```sql
CREATE TABLE categories (
    category_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name   TEXT NOT NULL UNIQUE,
    description     TEXT,
    shelf_life_days INTEGER DEFAULT 7
)
```
Seeded with 5 defaults on first run.

### Migration pattern
All views use `PRAGMA table_info` + `ALTER TABLE ADD COLUMN` — never drop/recreate tables.

---

## 5. Role-Based Access

| Feature | Chef | Inventory Staff | Manager |
|---|:---:|:---:|:---:|
| Dashboard | ✅ | ✅ | ✅ |
| Inventory (view + add) | ✅ | ✅ | ✅ |
| Record Waste `/waste/new` | ✅ | | ✅ |
| Expiry Monitor `/expiry` | | ✅ | ✅ |
| Waste Logs `/waste-logs` | | ✅ | ✅ |
| Reports `/reports` | | | ✅ |
| Categories `/categories` | | | ✅ |
| Users & Staff `/users` | | | ✅ |

Sidebar nav built conditionally in every view:
```python
role = page.session.store.get("role") or "chef"
nav_items_data = [Dashboard, Inventory]  # always visible
if role in ("inventory_staff", "manager"):
    nav_items_data += [Expiry Monitor, Waste Logs]
if role == "manager":
    nav_items_data += [Reports, Categories, Users & Staff]
# Settings is intentionally NOT in sidebar — removed
```

Role label mapping:
```python
{"chef": "Kitchen Staff", "inventory_staff": "Inventory Manager", "manager": "General Manager"}
```

---

## 6. UI Conventions

Each view has its own `LIGHT` and `DARK` color dicts at the top.
Do NOT refactor into shared module unless explicitly asked.

Key colors: `ORANGE=#E68A17`, `BG`, `CARD_BG`, `TEXT`, `MUTED`, `BORDER`,
`GREEN/GREEN_BG` (Fresh), `RED/RED_BG` (Expired), `ORANGE_BG` (Near Expiry).

Layout pattern:
```
[Sidebar 240px] | [Top bar: search + user info]
                  [Page title + CTA]
                  [Filters / tabs]
                  [Main content]
                  [Footer]
```

Standard components:
- Sidebar nav: orange bg + chevron when active
- Status pill: colored rounded rect (Fresh=green, Expiring=orange, Expired=red)
- Card: `border_radius=12, shadow=card_shadow()`
- Table: `TABLE_HEADER_BG` header, `DIVIDER` between rows, `MORE_VERT` popup

---

## 7. Build Status

### ✅ All Pages Built
| Page | Route |
|---|---|
| Login | `/` |
| Dashboard | `/dashboard` — real data fix in progress |
| Inventory | `/inventory` |
| Add/Edit Item | `/add-item` |
| Item Detail | `/item/{id}` |
| Record Food Waste | `/waste/new` |
| Expiry Monitor | `/expiry` |
| Waste Logs | `/waste-logs` |
| Reports | `/reports` |
| Categories | `/categories` |
| Users & Staff | `/users` |

### ❌ Intentionally Skipped
- Public registration (managers create users via `/users`)
- Notifications / SMS / email alerts
- Settings page
- Forgot password

---

## 8. Current Issues To Fix

### Dashboard (top priority)
All data is hardcoded — must be replaced with real DB queries:
- Stat cards: Total Items, Near Expiry, Expired Today, Waste Cost (Wk)
- Waste Distribution bars → waste_logs GROUP BY category JOIN inventory
- Daily Waste Trend chart → waste_logs last 7 days SUM cost per day
- Expiring Soon table → inventory WHERE expiry_date <= today+7, LIMIT 5
- Recent Waste Logs → waste_logs JOIN inventory ORDER BY waste_date DESC LIMIT 5
- "View Monitor" button → wire to page.go("/expiry")
- "All Logs" button → wire to page.go("/waste-logs")

### Other views — minor
- `item_detail.py` Waste History tab: shows placeholder even when real data exists
- `waste_new.py`: after save redirects to `/inventory` — should go to `/waste-logs`
- `reports.py` Download CSV: no-op — show SnackBar "Export coming soon"
- `waste_logs.py`: missing "+ Record Waste" button in header

---

## 9. Code Patterns

```python
def some_view(page: ft.Page) -> ft.View:
    _init_db()
    colors = LIGHT.copy() if page.theme_mode == ft.ThemeMode.LIGHT else DARK.copy()
    role = page.session.store.get("role") or "chef"
    # 1. helpers → 2. sidebar + top_bar → 3. content → 4. handlers → 5. load → 6. layout
    return ft.View(route="/...", padding=0, spacing=0, bgcolor=colors["BG"], controls=[layout])
```

SQL rules:
```python
# Always parameterize — NEVER f-string SQL
cur.execute("SELECT * FROM inventory WHERE id=?", (item_id,))

# Status always computed in Python
days_left = (expiry_date - today).days
status = "Expired" if days_left < 0 else "Expiring Soon" if days_left <= 7 else "Fresh"
```

Empty state pattern:
```python
if not rows:
    col.controls.append(ft.Container(
        padding=ft.Padding.symmetric(vertical=40),
        alignment=ft.Alignment(0, 0),
        content=ft.Text("No data yet.", size=14, color=colors["MUTED"]),
    ))
```

---

## 10. What NOT To Do

- ❌ Do not add bcrypt or password hashing
- ❌ Do not add third-party services (email, SMS, Firebase)
- ❌ Do not switch to Postgres/MySQL
- ❌ Do not refactor LIGHT/DARK color dicts into shared module
- ❌ Do not change brand color `#E68A17`
- ❌ Do not use f-strings inside SQL
- ❌ Do not add Settings page or sidebar link
- ❌ Do not add notifications/inbox page
- ❌ Do not call `page.views.clear()` outside `route_change()`
- ❌ Do not allow `username='manager'` account to be edited or deactivated

---

## 11. Glossary

- **Near Expiry** — `0 <= days_left <= alert_threshold` (default 3)
- **Expiring Soon** (inventory list) — `days_left <= 7`
- **Expired** — `days_left < 0`
- **Avoidable waste** — reason is `prep_waste` or `overproduction`
- **Stock value** — `SUM(quantity x 10)` placeholder
- **Head manager** — seeded account `username='manager'`
- **Batch** — one inventory row = one batch of a food item