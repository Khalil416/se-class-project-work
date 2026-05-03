# Kitchen Food Waste Tracker

A role-based restaurant kitchen management desktop app built with Flet (Python).
The system tracks food inventory, monitors expiry dates, logs waste, and produces reports — with different access levels for Chefs, Inventory Staff, and Managers.

> Repo: _<add GitHub link here>_
> University project — Software Engineering course, Semester 6.

---

## 1. Tech stack

- **UI framework:** Flet (`import flet as ft`)
- **Charts:** `flet_charts` (used in dashboard)
- **Language:** Python 3.x
- **Database:** SQLite (file-based, two files currently: `reg.db` for users, `inventory.db` for food items — these should eventually be unified into one DB, see Section 7)
- **Auth:** Plain-text passwords stored in DB (acceptable for this academic project; do NOT migrate to bcrypt unless explicitly asked)
- **Session:** `page.session.store` (in-memory, per-session key/value)
- **Routing:** `page.route` + `route_change()` middleware in `main.py`
- **Theme:** Custom orange-based scheme (`#E68A17`), supports light + dark mode

This is a **desktop** Flet app, not a web app. Window size is 1440x900, min 1100x760.

---

## 2. Project structure

```
ProjectWork/
├── main.py                  # App entry point + routing + auth middleware
├── reg.db                   # Users table (auth)
├── inventory.db             # Inventory + related tables
├── assets/                  # Logo and static assets
├── .gitignore
└── views/
    ├── __init__.py
    ├── login.py             # → login_view(page)        route: "/"
    ├── registration.py      # → registration_view(page) route: "/register"
    ├── dashboard.py         # → dashboard_view(page)    route: "/dashboard"
    ├── inventory.py         # → inventory_view(page)    route: "/inventory"
    └── add_item.py          # → add_item_view(page)     route: "/add-item"
```

Each view module exposes a single function returning an `ft.View`. The function builds the entire screen and returns it — `main.py` then appends the returned View to `page.views`.

---

## 3. Routing & auth pattern

Routing logic lives in `main.py` inside `route_change()`:

1. Read `is_logged_in` from `page.session.store`.
2. If route is protected (`/dashboard`, `/inventory`, `/add-item`, etc.) and user is NOT logged in → redirect to `/`.
3. `page.views.clear()`.
4. Always append `login_view(page)` as the base.
5. Append the matching view on top (registration / dashboard / inventory / add-item).
6. `page.update()`.

**Conventions when adding a new protected route:**
- Add the route to the auth check at the top of `route_change()`.
- Add an `if page.route == "/your-route":` block that appends the new view.
- Use `page.go("/your-route")` to navigate.
- Use `page.session.store.set(...)` to pass small payloads between views (e.g., `edit_item_id`).
- Use `page.session.store.remove(...)` to clean up after consuming.

**Auth keys in session:**
- `is_logged_in` (bool)
- `username` (str)
- `role` (str — to be added; see Section 6)
- `edit_item_id` (int, optional — used to pass which item is being edited to `add_item_view`)

---

## 4. UI conventions

### Colors

Each view defines its own `LIGHT` and `DARK` dictionaries at the top. Common keys:

| Key | Purpose |
|---|---|
| `ORANGE` | `#E68A17` — primary accent (buttons, active nav, badges) |
| `BG` | Page background |
| `CARD_BG` | Card background |
| `TEXT`, `TEXT_SECONDARY`, `MUTED` | Text hierarchy |
| `BORDER`, `DIVIDER` | Lines and separators |
| `GREEN`, `GREEN_BG` | Fresh / success status |
| `RED`, `RED_BG` | Expired / error status |
| `ORANGE_BG` | Near expiry / warning highlight |
| `SIDEBAR_BG`, `SIDEBAR_ACTIVE_BG` | Left nav |
| `SHADOW` | Subtle card shadow (low alpha) |

> **Tech debt note:** these dicts are duplicated across every view. When refactoring, consider moving them to a shared `views/theme.py` module. Do NOT refactor unless explicitly asked.

### Typography & spacing
- Page titles: `size=26, weight=W_700`
- Section/card titles: `size=16, weight=W_600`
- Body: `size=13–14`
- Muted/helper text: `size=12, color=MUTED`
- Card padding: `20–28px`
- Card border radius: `12`
- Input border radius: `8–10`
- Button border radius: `8`

### Layout pattern (full app pages)
```
[Sidebar 240px] [Top bar with search + user avatar]
                [Page title + subtitle + primary CTA]
                [Filters / tabs]
                [Main content (table / cards / form)]
                [Bottom stats row (optional)]
                [Footer]
```

### Components
- Sidebar nav: orange background tint + chevron when active.
- Status badges: small rounded rect, colored bg + matching text color (Fresh = green, Expiring Soon = orange, Expired = red).
- Forms: section headers with circular orange icon, asterisk-marked required fields, helper italic text below.
- Tables: light gray header bg (`TABLE_HEADER_BG`), divider lines between rows, status badge column on the right, popup menu (`MORE_VERT`) for row actions.

---

## 5. Database schema (target — based on ERD)

Currently only two tables exist: `users` (in `reg.db`) and `inventory` (in `inventory.db`). The full target schema below is what the project is moving toward — implement tables as features are built.

### Users & roles
- **`users`** — `user_id PK`, `username UNIQUE`, `password`, `email UNIQUE`, `role ENUM('chef','inventory_staff','manager')`, `created_at`, `is_active`
- **`chefs`** — `chef_id PK`, `user_id FK`, `full_name`, `phone`, `section`, `hired_date`
- **`inventory_staff`** — `staff_id PK`, `user_id FK`, `full_name`, `phone`, `shift`, `hired_date`
- **`managers`** — `manager_id PK`, `user_id FK`, `full_name`, `phone`, `department`, `hired_date`

### Inventory & catalog
- **`categories`** — `category_id PK`, `category_name`, `description`, `shelf_life_days` (used to auto-suggest expiry dates)
- **`food_items`** — `item_id PK`, `category_id FK`, `added_by FK→user_id`, `item_name`, `quantity DECIMAL(10,2)`, `unit`, `purchase_date`, `storage_loc`
- **`expiry_dates`** — `expiry_id PK`, `item_id FK`, `expiry_date`, `batch_no`, `alert_threshold INT`, `status ENUM`

> **Note:** Current `inventory` table mixes food item + expiry data into one row. Target schema separates batches into `expiry_dates` so a single item (e.g., Organic Whole Milk) can have multiple batches (LOT-2024-001, LOT-2024-002…) each with its own expiry date. Item detail page in mock-up shows this multi-batch view.

### Operations
- **`waste_logs`** — `log_id PK`, `item_id FK`, `recorded_by FK→user_id`, `qty_wasted`, `unit`, `reason ENUM('expired','spoiled','prep_waste','overproduction','damaged','other')`, `waste_date`, `notes`, `cost_estimate`

### Out of scope for this project
- **`notifications`** table is in the ERD but **not implemented**. No SMS, email, or push integrations. The "Send Expiry Alert" use case in the UCD is intentionally skipped — this is a third-party concern outside the academic scope.

### Migration approach
- Use `PRAGMA table_info(table_name)` and `ALTER TABLE ... ADD COLUMN` for non-destructive migrations (already done in `add_item.py` and `inventory.py`).
- Wrap migration logic in a `_init_*_db()` or `_ensure_columns()` helper called at the top of each view function. This is the established pattern.

---

## 6. Role-based access (planned)

Per the use case diagram, three roles with these capabilities:

| Action | Chef | Inventory Staff | Manager |
|---|:---:|:---:|:---:|
| Record Waste | ✅ | | |
| Add Food Item | ✅ | ✅ | |
| Update Stock (Quantity) | ✅ | ✅ | |
| Monitor Expiry (view near-expiry) | | ✅ | ✅ |
| Generate Waste Report | | | ✅ |
| Manage Categories | | | ✅ |
| Manage Users & Staff | | | ✅ |

**Implementation pattern when role gating is added:**
- Store `role` in `page.session.store` after login.
- Build sidebar nav items conditionally based on role.
- At the top of each view's function, check role and redirect to `/dashboard` if not authorized.
- Helper to add later: `views/auth.py` with `require_role(page, allowed_roles)`.

**Demo accounts to seed (suggested):**
- `chef_julian` / Chef
- `staff_sarah` / Inventory Staff
- `manager_mike` / Manager

---

## 7. Build status — pages

The mock UI defines 12+ screens. Current state:

### ✅ Built
- **Login** (`/`) — username/email + password, persona chips, light/dark toggle.
- **Registration** (`/register`) — username + email + password + confirm.
- **Dashboard** (`/dashboard`) — 4 stat cards, waste distribution bars, daily waste line chart, expiring soon table, recent waste logs table.
- **Inventory list** (`/inventory`) — search + 3 filters, paginated table (6/page), 4-card stats row at the bottom, edit/delete actions per row.
- **Add / Edit Food Item** (`/add-item`) — three-section form (Basic / Inventory & Units / Expiry Monitoring), reused for both add and edit via `edit_item_id` session key.

### ❌ To build (priority order)
1. **Item Detail page** — `/item/{id}` — header card with item summary, tabs (Expiry Batches / Waste History / Activity Timeline), supplier info, last handled by, usage policy. Shows multiple batches per item.
2. **Update Stock modal** — Restock (Add) / Withdraw (Subtract) toggle, adjustment amount, projected new total preview, optional note. Triggered from item detail and inventory row.
3. **Record Food Waste** (`/waste/new`) — item picker, qty wasted, unit, primary reason dropdown, date/time, cost adjustment (auto-calc), disposal notes. Sidebar shows projected loss.
4. **Expiry Monitor** (`/expiry`) — tabs (Near Expiry / Expired / All Items), batch-level table, threshold slider (default 3 days), info cards at the bottom.
5. **Waste Logs** (`/waste-logs`) — audit trail with date range, reason filter, search; top-row summary metrics (Waste Cost Today, Volume MTD, Avoidable Waste %); optimization insight card.
6. **Reports / Analytics** (`/reports`) — Manager-only. Daily/Weekly/Monthly toggle, financial loss / wasted weight / efficiency cards, waste cost trend line, waste-by-reason donut, top wasted items by cost bar chart, manager insight card.
7. **Categories Management** (`/categories`) — Manager-only. CRUD for categories with `shelf_life_days` defaults driving expiry-date suggestions in Add Food Item.
8. **Users & Staff** (`/users`) — Manager-only. Tabs: Staff Profiles + System Users. Add Profile / New User modal with role linking.

### Skipped intentionally
- Notification inbox / SMS / email alerts (third-party out of scope).
- "Forgot password" flow (placeholder button only).

---

## 8. Code patterns to follow

### View function shape
```python
def some_view(page: ft.Page) -> ft.View:
    _init_db()                                  # if this view owns a table
    colors = LIGHT.copy() if page.theme_mode == ft.ThemeMode.LIGHT else DARK.copy()

    # 1. helpers (card_shadow, build_nav_item, status_badge…)
    # 2. controls (top_bar, sidebar, content_header, table_body…)
    # 3. event handlers (on_save, on_delete, refresh_table…)
    # 4. initial load
    # 5. assemble layout (Row → Column → Containers)

    return ft.View(route="/...", padding=0, spacing=0, bgcolor=colors["BG"], controls=[layout])
```

### DB helpers
- Always parameterize SQL: `cur.execute("... WHERE id=?", (item_id,))`. Never f-string user input into SQL.
- Open connection, do work, close. No connection pooling.
- Use `conn.row_factory = sqlite3.Row` when you want dict-like access.
- Status fields like "Fresh / Expiring Soon / Expired" are computed in Python from `expiry_date`, NOT stored in DB.

### Filtering tables
Pattern from `inventory.py`:
```python
def _get_items(search="", category="All Categories", status="All Status", storage="All Storage"):
    query = "SELECT ... FROM inventory WHERE 1=1"
    params = []
    if search:
        query += " AND (item_name LIKE ? OR sku LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    # ...
```
Status filter is applied in Python after fetch (since status is computed).

### Pagination
Pure-Python slicing with a page index. See `inventory.py`'s `current_page` + `items_per_page = 6`.

---

## 9. What NOT to do

- ❌ Do not call `page.views.clear()` outside `route_change()` — it breaks the back-stack.
- ❌ Do not navigate by mutating `page.views` directly — always use `page.go(route)`.
- ❌ Do not access protected views without checking `is_logged_in` first.
- ❌ Do not add hashing / bcrypt to passwords unless explicitly requested (academic scope).
- ❌ Do not introduce third-party services (SendGrid, Twilio, Firebase, etc.) — notifications are out of scope.
- ❌ Do not switch from SQLite to Postgres / MySQL — keep it file-based.
- ❌ Do not refactor the duplicated `LIGHT` / `DARK` dicts unless explicitly asked. They are tech debt but they work.
- ❌ Do not change the orange brand color (`#E68A17`) — it's tied to the logo and the entire design system.
- ❌ Do not use f-strings inside SQL — always parameterize.
- ❌ Do not generate emojis in the UI — the design uses Material icons only (`ft.Icons.*`).
- ❌ Do not add a notifications inbox / mock alerts page — it's intentionally skipped.

---

## 10. Glossary (domain terms)

- **Batch / LOT** — a specific shipment of an item with its own expiry date. One item can have many batches.
- **Near Expiry** — within `alert_threshold` days of `expiry_date` (default threshold = 3 days).
- **Avoidable waste** — waste from `prep_waste` or `overproduction` reasons (not `expired` or `spoiled`).
- **Stock value** — rough estimate of inventory monetary value (currently `quantity × $10` placeholder).
- **Storage location** — physical place in the kitchen (Walk-in Fridge, Freezer A, Dry Storage, etc.).
- **Personas** — synonym for roles (Chef = Kitchen Staff; Inventory Mgr; General Mgr).

---

## 11. When in doubt

- Match the visual style of the mock UI PDF (orange accents, white cards, generous whitespace, status pill badges).
- Match the code style of `inventory.py` and `add_item.py` — they are the most recent and reflect the intended pattern.
- Keep changes minimal and scoped. This is an academic project; a working partial feature beats an over-engineered one.
- Before adding a new dependency, check whether stdlib or Flet built-ins can do the job.
