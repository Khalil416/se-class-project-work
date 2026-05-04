# Kitchen Waste Tracker

A desktop-style inventory and waste management app built with [Flet](https://flet.dev/) and SQLite. It tracks inventory, expiry alerts, waste logs, reports, categories, and staff accounts with role-based access control.

## Features

- Dashboard with live inventory and waste summary cards
- Inventory management with item details and add/edit flows
- Waste recording and waste log history
- Expiry monitor for soon-to-expire items
- Reports with charts and CSV export
- Category management
- User management with roles:
  - `manager`
  - `inventory_staff`
  - `chef`
- Login, registration, and account pages

## Project Files

- `main.py` - application entry point and route handling
- `views/` - all UI pages
- `assets/` - app images and icons
- `inventory.db` - inventory and waste data
- `reg.db` - login and user data
- `reports/` - generated CSV exports

## Requirements

- Python 3.12+
- Flet
- SQLite (included with Python)

## Run

From the project root:

```bash
python main.py
```

If you are using the virtual environment in this project on Windows, you can also run:

```bash
.venv\Scripts\python.exe main.py
```

## Notes

- The app uses the local SQLite files in the project root.
- Some sample users and categories are seeded automatically if the database is missing data.
- CSV exports are saved inside the `reports/` folder.

## Default Roles

- `manager` - full access, including reports, categories, users, and waste logs
- `inventory_staff` - inventory and waste log access
- `chef` - inventory viewing and approved workflows
