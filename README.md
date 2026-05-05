# Kitchen Waste Tracker

A desktop app for restaurants and commercial kitchens to track inventory, monitor expiry dates, and log food waste — built with [Flet](https://flet.dev/) (Python) and SQLite.

I built this as a university project to explore how a small, focused tool can help real kitchens cut down on food waste by making expiry dates visible and turning waste into structured data instead of guesswork.

## What the app does

The app is built around three roles, and each one sees a different version of the interface:

- **Kitchen Staff** (`chef`) — view inventory, see what's expiring, record waste against items they're using.
- **Inventory Manager** (`inventory_staff`) — everything the kitchen staff sees, plus the expiry monitor and full waste log history.
- **General Manager** (`manager`) — full access, including reports with charts, category management, user management, and the only role allowed to register new users or record waste on behalf of someone else.

Pages are wired through Flet's routing in `main.py`, with route guards that redirect unauthorized roles back to the dashboard.

## Features

**Dashboard** — At-a-glance summary cards (total items, items near expiry, expired items, weekly waste cost), a category-by-category waste distribution chart, a 7-day waste trend line chart, and shortcuts to expiring items and recent waste logs.

**Inventory** — Add, edit, and delete food items with quantity, unit, storage location, expiry date, batch number, and alert threshold. Filter by category, status (Fresh / Expiring Soon / Expired), and storage location. Click any row to open a detail page with stock adjustment dialog and waste history for that item.

**Expiry Monitor** — Tabs for "Near Expiry," "Expired," and "All Items," plus an adjustable threshold slider (1–14 days) so you can tune how aggressive the alerts are.

**Waste Logs** — Searchable, paginated audit trail of every waste event with date filters, reason badges, and per-event cost estimates. Recording waste also decrements inventory in the same transaction, so stock counts stay honest.

**Reports** *(manager only)* — Daily / weekly / monthly views of waste cost trends, breakdown by reason (expired, spoiled, prep waste, overproduction, damaged), top 5 most-wasted items, and one-click CSV export to a local `reports/` folder.

**Categories** *(manager only)* — Manage the food category list with descriptions and default shelf life. Categories drive the dropdowns in the inventory form.

**Users** *(manager only)* — Grid view of all accounts with edit, deactivate, and delete actions. Includes a "head manager" account (`manager`) that can't be modified or deleted by anyone — even other managers — to prevent accidental lockout.

**Account** — Each user can view their own profile and credentials.

**Light + dark mode** — Toggle on the login screen.

## Tech stack

- **Flet** for the UI (single Python codebase, native desktop window via Flutter under the hood)
- **flet_charts** for the line charts on the dashboard and reports page
- **SQLite** for local storage — two databases:
  - `inventory.db` — items, categories, waste logs
  - `reg.db` — user accounts and authentication
- **Python 3.12+**

No external services, no cloud, no API keys. Everything runs locally.

## Project structure

```
kitchen-waste-tracker/
├── main.py                   # Entry point, routing, auth guards
├── views/
│   ├── login.py              # Login screen + auth DB seeding
│   ├── registration.py       # Manager-only user creation
│   ├── dashboard.py          # Summary cards + charts + tables
│   ├── inventory.py          # Inventory list with filters
│   ├── add_item.py           # Add/edit item form (shared)
│   ├── item_detail.py        # Per-item view with stock adjust
│   ├── expiry_monitor.py     # Tabs + threshold slider
│   ├── waste_new.py          # Record waste form
│   ├── waste_logs.py         # Audit trail with pagination
│   ├── reports.py            # Charts + CSV export
│   ├── categories.py         # Manage food categories
│   ├── users_staff.py        # User management grid
│   └── account.py            # Personal account page
├── tools/
│   └── check_users.py        # CLI helper to inspect reg.db
├── assets/                   # Logo and icons
├── reports/                  # Generated CSV exports
├── inventory.db              # Auto-created on first run
├── reg.db                    # Auto-created on first run
└── README.md
```

## Getting started

You need Python 3.12 or newer.

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd kitchen-waste-tracker

# 2. (Recommended) create a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install flet flet-charts

# 4. Run
python main.py
```

The first time you launch, both databases are created automatically and a few seed accounts are inserted for testing.

## Default login credentials

These accounts are seeded automatically on first run. **Change them in production.**

| Username     | Password | Role             |
|--------------|----------|------------------|
| `manager`    | `1234`   | General Manager  |
| `manager2`   | `1234`   | General Manager  |
| `inventory1` | `1234`   | Inventory Manager|
| `chef1`      | `1234`   | Kitchen Staff    |

The `manager` account is the protected "head manager" — it can't be deleted, deactivated, or have its role changed, even by other managers.

## Notes on the data model

The schema migrates itself. Each view that touches a table runs `CREATE TABLE IF NOT EXISTS` and `ALTER TABLE ADD COLUMN` on startup, so existing databases pick up new columns without a manual migration step. This keeps the project simple to run on a fresh machine but also means the code lives close to the schema — read the `_init_*_db()` helpers at the top of each view file if you want the canonical column list.

Waste recording is transactional: inserting a waste log and decrementing the inventory quantity happen in the same `sqlite3` connection, with a rollback if either fails. That was the most important thing to get right — losing track of how much is actually on the shelf would defeat the whole point of the app.

## Things that aren't built yet

Being honest about scope: the password input field on login doesn't hash anything, there's no "forgot password" flow, no remote backups, no multi-tenancy. This is a coursework project and a portfolio piece, not production software. If you want to extend it, the cleanest next steps would be password hashing (`bcrypt`), a proper migration tool (Alembic), and switching the routing guards to a decorator pattern.

## License

MIT — do whatever you want with it, just don't blame me if it eats your inventory.

---

Built by Khalil Allahverdiyev as part of the BBA in Computer Information Systems program at ASOIU.