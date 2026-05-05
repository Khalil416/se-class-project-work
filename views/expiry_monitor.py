import flet as ft
import sqlite3
import requests
from datetime import datetime

DB_PATH = "inventory.db"
API_URL = "http://127.0.0.1:8000"

LIGHT = {
    "ORANGE": "#E68A17",
    "BG": "#F8F9FA",
    "CARD_BG": "#FFFFFF",
    "TEXT": "#1A1A2E",
    "TEXT_SECONDARY": "#555555",
    "MUTED": "#888888",
    "BORDER": "#E8E8E8",
    "SIDEBAR_BG": "#FFFFFF",
    "SIDEBAR_ACTIVE_BG": "#FEF3E2",
    "SIDEBAR_TEXT": "#666666",
    "SIDEBAR_ICON": "#999999",
    "GREEN": "#16A34A",
    "GREEN_BG": "#F0FDF4",
    "RED": "#DC2626",
    "RED_BG": "#FEF2F2",
    "ORANGE_BG": "#FFF7ED",
    "SEARCH_BG": "#F5F5F5",
    "SEARCH_BORDER": "#EEEEEE",
    "DIVIDER": "#F0F0F0",
    "SHADOW": "#08000000",
    "TABLE_HEADER_BG": "#FAFAFA",
    "AVATAR_BG": "#FFE0B2",
}

DARK = {
    "ORANGE": "#E68A17",
    "BG": "#0F0F0F",
    "CARD_BG": "#1A1A1A",
    "TEXT": "#F0F0F0",
    "TEXT_SECONDARY": "#CCCCCC",
    "MUTED": "#999999",
    "BORDER": "#2C2C2C",
    "SIDEBAR_BG": "#151515",
    "SIDEBAR_ACTIVE_BG": "#2D2010",
    "SIDEBAR_TEXT": "#AAAAAA",
    "SIDEBAR_ICON": "#888888",
    "GREEN": "#22C55E",
    "GREEN_BG": "#14532D",
    "RED": "#EF4444",
    "RED_BG": "#450A0A",
    "ORANGE_BG": "#3D2810",
    "SEARCH_BG": "#222222",
    "SEARCH_BORDER": "#333333",
    "DIVIDER": "#252525",
    "SHADOW": "#30000000",
    "TABLE_HEADER_BG": "#202020",
    "AVATAR_BG": "#5D4037",
}


def _init_expiry_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            sku TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit TEXT NOT NULL,
            storage TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute("PRAGMA table_info(inventory)")
    existing = {row[1] for row in cur.fetchall()}
    migrations = [
        ("purchase_date", "TEXT DEFAULT ''"),
        ("internal_notes", "TEXT DEFAULT ''"),
        ("batch_number", "TEXT DEFAULT ''"),
        ("alert_threshold", "INTEGER DEFAULT 3"),
    ]
    for col, typedef in migrations:
        if col not in existing:
            cur.execute(f"ALTER TABLE inventory ADD COLUMN {col} {typedef}")
    conn.commit()
    conn.close()


def _get_items(search_text=""):
    try:
        response = requests.get(f"{API_URL}/inventory", params={"search": search_text}, timeout=5)
        if response.status_code == 200:
            rows = response.json().get("data", [])
            return [
                {
                    "id": r.get("id"),
                    "item_name": r.get("item_name"),
                    "sku": r.get("sku"),
                    "category": r.get("category"),
                    "quantity": r.get("quantity"),
                    "unit": r.get("unit"),
                    "expiry_date": r.get("expiry_date"),
                    "batch_number": r.get("batch_number", ""),
                }
                for r in rows
            ]
    except requests.exceptions.RequestException:
        pass
    return []


def expiry_monitor_view(page: ft.Page) -> ft.View:
    _init_expiry_db()
    colors = LIGHT.copy() if page.theme_mode == ft.ThemeMode.LIGHT else DARK.copy()
    role = page.session.store.get("role") or "chef"

    current_tab = [0]
    threshold_days = [3]

    def card_shadow():
        return ft.BoxShadow(
            blur_radius=12,
            spread_radius=0,
            color=colors["SHADOW"],
            offset=ft.Offset(0, 2),
        )

    logo_icon = ft.Image(src="assets/logo.png", width=36, height=36, fit=ft.BoxFit.CONTAIN)
    logo_text = ft.Text("Kitchen Food Waste", size=15, weight=ft.FontWeight.W_700, color=colors["TEXT"], overflow=ft.TextOverflow.ELLIPSIS, max_lines=1)

    nav_items_data = [
        (ft.Icons.SPACE_DASHBOARD_OUTLINED, "Dashboard", page.route == "/dashboard", "/dashboard"),
        (ft.Icons.INVENTORY_2_OUTLINED, "Inventory", page.route == "/inventory", "/inventory"),
    ]
    if role in ("inventory_staff", "manager"):
        nav_items_data.extend([
            (ft.Icons.TIMER_OUTLINED, "Expiry Monitor", page.route == "/expiry", "/expiry"),
            (ft.Icons.RECEIPT_LONG_OUTLINED, "Waste Logs", page.route == "/waste-logs", "/waste-logs"),
        ])
    if role == "manager":
        nav_items_data.extend([
            (ft.Icons.BAR_CHART, "Reports", page.route == "/reports", "/reports"),
            (ft.Icons.CATEGORY_OUTLINED, "Categories", page.route == "/categories", "/categories"),
            (ft.Icons.PEOPLE_OUTLINE, "Users", page.route == "/users", "/users"),
        ])
    # Settings removed (not implemented)

    def build_nav_item(icon, label, active=False, route=None):
        text_color = colors["ORANGE"] if active else colors["SIDEBAR_TEXT"]
        icon_color = colors["ORANGE"] if active else colors["SIDEBAR_ICON"]
        bg = colors["SIDEBAR_ACTIVE_BG"] if active else "transparent"
        weight = ft.FontWeight.W_600 if active else ft.FontWeight.W_400

        row_controls = [
            ft.Icon(icon, size=20, color=icon_color),
            ft.Text(label, size=14, color=text_color, weight=weight, expand=True),
        ]
        if active:
            row_controls.append(ft.Icon(ft.Icons.CHEVRON_RIGHT, size=18, color=icon_color))

        def nav_click(e, r=route):
            if r:
                page.go(r)

        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=14, vertical=10),
            bgcolor=bg,
            border_radius=8,
            content=ft.Row(spacing=12, controls=row_controls),
            ink=True,
            on_click=nav_click if route else None,
        )

    nav_column = ft.Column(spacing=2, controls=[build_nav_item(i, l, a, r) for i, l, a, r in nav_items_data])

    def on_sign_out(e):
        page.session.store.clear()
        page.go("/")

    sidebar = ft.Container(
        width=240,
        bgcolor=colors["SIDEBAR_BG"],
        border=ft.Border(right=ft.BorderSide(1, colors["BORDER"])),
        padding=ft.Padding.only(top=20, bottom=12, left=12, right=12),
        content=ft.Column(
            expand=True,
            spacing=0,
            controls=[
                ft.Container(
                    padding=ft.Padding.only(left=6, bottom=24),
                    content=ft.Row(spacing=10, controls=[logo_icon, logo_text]),
                ),
                nav_column,
                ft.Container(expand=True),
                ft.Divider(height=1, color=colors["DIVIDER"]),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=14, vertical=10),
                    ink=True,
                    on_click=on_sign_out,
                    content=ft.Row(
                        spacing=12,
                        controls=[
                            ft.Icon(ft.Icons.LOGOUT, size=20, color=colors["SIDEBAR_TEXT"]),
                            ft.Text("Sign Out", size=14, color=colors["SIDEBAR_TEXT"]),
                        ],
                    ),
                ),
            ],
        ),
    )

    username = page.session.store.get("username") or "User"
    role = page.session.store.get("role") or "Kitchen Staff"
    initials = username[:2].upper()

    topbar_search = ft.TextField(
        hint_text="Search items, batches, or expiry dates...",
        width=400,
        height=42,
        border_radius=10,
        border_color=colors["SEARCH_BORDER"],
        focused_border_color=colors["ORANGE"],
        bgcolor=colors["SEARCH_BG"],
        prefix_icon=ft.Icons.SEARCH,
        content_padding=ft.Padding.symmetric(horizontal=14, vertical=8),
        text_size=14,
        color=colors["TEXT"],
        cursor_color=colors["ORANGE"],
    )

    def on_topbar_search_submit(e):
        val = (topbar_search.value or "").strip()
        if val:
            page.session.store.set("global_search", val)
            page.go("/inventory")

    topbar_search.on_submit = on_topbar_search_submit

    top_bar = ft.Container(
        padding=ft.Padding.symmetric(horizontal=32, vertical=14),
        border=ft.Border(bottom=ft.BorderSide(1, colors["BORDER"])),
        bgcolor=colors["CARD_BG"],
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                topbar_search,
                ft.Container(
                    ink=True,
                    on_click=lambda e: page.go("/account"),
                    border_radius=10,
                    padding=ft.Padding.symmetric(horizontal=4, vertical=4),
                    content=ft.Row(
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Column(
                                spacing=0,
                                horizontal_alignment=ft.CrossAxisAlignment.END,
                                controls=[
                                    ft.Text(username, size=14, weight=ft.FontWeight.W_600, color=colors["TEXT"]),
                                    ft.Text(role, size=12, color=colors["MUTED"]),
                                ],
                            ),
                            ft.Container(width=38, height=38, bgcolor=colors["AVATAR_BG"], border_radius=19, alignment=ft.Alignment(0, 0), content=ft.Text(initials, size=14, weight=ft.FontWeight.W_600, color=colors["ORANGE"])),
                        ],
                    ),
                ),
            ],
        ),
    )

    table_body = ft.Column(spacing=0)
    empty_state = ft.Container(
        padding=ft.Padding.symmetric(vertical=40),
        alignment=ft.Alignment(0, 0),
        content=ft.Text("No items match the current filters.", size=14, color=colors["MUTED"]),
    )

    search_field = ft.TextField(
        hint_text="Search by item, category, or batch...",
        width=300,
        height=42,
        border_radius=8,
        border_color=colors["BORDER"],
        focused_border_color=colors["ORANGE"],
        bgcolor=colors["CARD_BG"],
        prefix_icon=ft.Icons.SEARCH,
        content_padding=ft.Padding.symmetric(horizontal=14, vertical=8),
        text_size=14,
        color=colors["TEXT"],
        cursor_color=colors["ORANGE"],
    )

    threshold_label = ft.Text(f"Threshold: {threshold_days[0]} days", size=13, color=colors["TEXT_SECONDARY"], weight=ft.FontWeight.W_500)
    threshold_slider = ft.Slider(min=1, max=14, divisions=13, value=3, label="{value} days", active_color=colors["ORANGE"], thumb_color=colors["ORANGE"])

    def get_status_info(days_left):
        if days_left < 0:
            return "Expired", colors["RED"], colors["RED_BG"]
        if days_left <= threshold_days[0]:
            return "Expiring Soon", colors["ORANGE"], colors["ORANGE_BG"]
        return "Fresh", colors["GREEN"], colors["GREEN_BG"]

    def get_time_text(days_left):
        if days_left < 0:
            return f"Expired ({abs(days_left)}d ago)"
        if days_left == 0:
            return "Expiring Soon (0d left)"
        return f"Expiring Soon ({days_left}d left)"

    def build_status_pill(label, color, bg):
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            bgcolor=bg,
            border_radius=4,
            alignment=ft.Alignment(0, 0),
            content=ft.Text(label, size=11, color=color, weight=ft.FontWeight.W_600),
        )

    def build_tab_chip(label, idx):
        active = current_tab[0] == idx
        return ft.Container(
            padding=ft.Padding.only(left=20, right=20, top=14, bottom=10),
            border=ft.Border(bottom=ft.BorderSide(2, colors["ORANGE"] if active else "transparent")),
            ink=True,
            on_click=lambda e, i=idx: switch_tab(i),
            content=ft.Text(
                label,
                size=14,
                color=colors["ORANGE"] if active else colors["MUTED"],
                weight=ft.FontWeight.W_600 if active else ft.FontWeight.W_400,
            ),
        )

    tab_headers = ft.Row(spacing=0, controls=[build_tab_chip("Near Expiry", 0), build_tab_chip("Expired", 1), build_tab_chip("All Items", 2)])

    def filter_rows():
        search_text = (search_field.value or "").strip().lower()
        rows = _get_items(search_text)
        filtered = []
        today = datetime.now().date()
        for row in rows:
            try:
                expiry_date = datetime.strptime(row["expiry_date"], "%Y-%m-%d").date()
            except Exception:
                expiry_date = today
            days_left = (expiry_date - today).days
            if current_tab[0] == 0 and not (0 <= days_left <= threshold_days[0]):
                continue
            if current_tab[0] == 1 and not (days_left < 0):
                continue
            filtered.append((row, days_left))
        return filtered

    def on_search_change(e):
        refresh_table()

    def on_threshold_change(e):
        threshold_days[0] = int(round(threshold_slider.value or 3))
        threshold_label.value = f"Threshold: {threshold_days[0]} days"
        refresh_table()

    def switch_tab(idx):
        current_tab[0] = idx
        tab_headers.controls = [build_tab_chip("Near Expiry", 0), build_tab_chip("Expired", 1), build_tab_chip("All Items", 2)]
        refresh_table()

    def on_item_click(item_id):
        page.go(f"/item/{item_id}")

    def build_table_header():
        headers = [
            ("Item Name + Category", 2.5),
            ("Batch ID", 1.2),
            ("Expiry Date", 1.1),
            ("Quantity", 1.0),
            ("Status", 1.6),
            ("Actions", 0.8),
        ]
        return ft.Container(
            bgcolor=colors["TABLE_HEADER_BG"],
            padding=ft.Padding.symmetric(horizontal=20, vertical=12),
            border=ft.Border(bottom=ft.BorderSide(1, colors["DIVIDER"])),
            content=ft.Row(
                spacing=8,
                controls=[
                    ft.Container(expand=25, content=ft.Text(headers[0][0], size=12, color=colors["MUTED"], weight=ft.FontWeight.W_600)),
                    ft.Container(expand=12, content=ft.Text(headers[1][0], size=12, color=colors["MUTED"], weight=ft.FontWeight.W_600)),
                    ft.Container(expand=11, content=ft.Text(headers[2][0], size=12, color=colors["MUTED"], weight=ft.FontWeight.W_600)),
                    ft.Container(expand=10, content=ft.Text(headers[3][0], size=12, color=colors["MUTED"], weight=ft.FontWeight.W_600)),
                    ft.Container(expand=16, content=ft.Text(headers[4][0], size=12, color=colors["MUTED"], weight=ft.FontWeight.W_600)),
                    ft.Container(expand=8, content=ft.Text(headers[5][0], size=12, color=colors["MUTED"], weight=ft.FontWeight.W_600)),
                ],
            ),
        )

    def build_table_row(row, days_left):
        item_id = row["id"]
        name = row["item_name"]
        category = row["category"]
        batch_id = row.get("batch_number") or "—"
        expiry_date = row["expiry_date"]
        qty = row["quantity"]
        unit = row["unit"]
        status_label, status_color, status_bg = get_status_info(days_left)
        status_text = get_time_text(days_left) if status_label != "Fresh" else "Fresh"

        qty_display = f"{int(qty)}" if qty == int(qty) else f"{qty}"

        def on_open_item(e, iid=item_id):
            on_item_click(iid)

        def on_record(e):
            page.session.store.set("waste_item_id", item_id)
            page.go("/waste/new")

        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=20, vertical=10),
            border=ft.Border(bottom=ft.BorderSide(1, colors["DIVIDER"])),
            ink=True,
            on_click=on_open_item,
            content=ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        expand=25,
                        content=ft.Column(
                            spacing=0,
                            controls=[
                                ft.Text(name, size=14, color=colors["TEXT"], weight=ft.FontWeight.W_500),
                                ft.Text(category, size=11, color=colors["MUTED"]),
                            ],
                        ),
                    ),
                    ft.Container(expand=12, content=ft.Text(batch_id, size=13, color=colors["TEXT_SECONDARY"])),
                    ft.Container(expand=11, content=ft.Text(expiry_date, size=13, color=colors["TEXT_SECONDARY"])),
                    ft.Container(expand=10, content=ft.Text(f"{qty_display} {unit}", size=13, color=colors["TEXT"], weight=ft.FontWeight.W_500)),
                    ft.Container(
                        expand=16,
                        content=ft.Column(
                            spacing=4,
                            controls=[
                                build_status_pill(status_label, status_color, status_bg),
                                ft.Text(status_text, size=11, color=colors["TEXT_SECONDARY"]),
                            ],
                        ),
                    ),
                    ft.Container(
                        expand=8,
                        content=ft.PopupMenuButton(
                            icon=ft.Icons.MORE_VERT,
                            icon_size=18,
                            icon_color=colors["MUTED"],
                            items=[
                                ft.PopupMenuItem(content=ft.Text("Open Item"), icon=ft.Icons.OPEN_IN_NEW, on_click=lambda e, iid=item_id: on_item_click(iid)),
                                ft.PopupMenuItem(content=ft.Text("Record Waste"), icon=ft.Icons.DELETE_OUTLINE, on_click=on_record),
                            ],
                        ),
                    ),
                ],
            ),
        )

    def refresh_table():
        items = filter_rows()
        table_body.controls = [build_table_header()]
        if not items:
            table_body.controls.append(empty_state)
        else:
            for row, days_left in items:
                table_body.controls.append(build_table_row(row, days_left))
        page.update()

    search_field.on_change = on_search_change
    threshold_slider.on_change = on_threshold_change

    filters_row = ft.Container(
        padding=ft.Padding.symmetric(horizontal=32, vertical=10),
        content=ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                search_field,
                ft.Container(width=260, content=ft.Column(spacing=4, controls=[threshold_label, threshold_slider])),
            ],
        ),
    )

    title_block = ft.Container(
        padding=ft.Padding.only(left=32, right=32, top=24, bottom=8),
        content=ft.Column(
            spacing=4,
            controls=[
                ft.Text("Expiry Monitoring", size=26, weight=ft.FontWeight.W_700, color=colors["TEXT"]),
                ft.Text("Track and manage items nearing expiration", size=14, color=colors["MUTED"]),
            ],
        ),
    )

    content_header = ft.Container(
        padding=ft.Padding.only(left=32, right=32, top=8, bottom=8),
        content=tab_headers,
    )

    table_card = ft.Container(
        margin=ft.Margin(32, 8, 32, 0),
        bgcolor=colors["CARD_BG"],
        border=ft.Border.all(1, colors["BORDER"]),
        border_radius=12,
        shadow=card_shadow(),
        content=table_body,
    )

    footer = ft.Container(
        padding=ft.Padding.symmetric(horizontal=32, vertical=14),
        border=ft.Border(top=ft.BorderSide(1, colors["DIVIDER"])),
        content=ft.Text("© 2026 Kitchen Food Waste Tracker. All rights reserved.", size=12, color=colors["MUTED"]),
    )

    content_area = ft.Container(
        expand=True,
        bgcolor=colors["BG"],
        content=ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
            controls=[
                top_bar,
                title_block,
                content_header,
                filters_row,
                table_card,
                footer,
            ],
        ),
    )

    layout = ft.Row(expand=True, spacing=0, controls=[sidebar, content_area])

    refresh_table()

    return ft.View(route="/expiry", padding=0, spacing=0, bgcolor=colors["BG"], controls=[layout])
