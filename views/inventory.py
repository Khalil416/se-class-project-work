import flet as ft
import sqlite3
import math
from datetime import datetime, timedelta

DB_PATH = "inventory.db"

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

CATEGORIES = ["Dairy", "Meat", "Produce", "Bakery", "Pantry", "Seafood", "Beverages", "Frozen", "Condiments", "Grains", "Snacks", "Spices"]
STORAGES = ["Walk-in Fridge", "Freezer A", "Freezer B", "Dry Storage", "Pantry Shelf", "Cold Room"]


def _init_inventory_db():
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
    # Add new columns if they don't exist (migration-safe)
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


def _get_items(search="", category="All Categories", status="All Status", storage="All Storage"):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    query = "SELECT id, item_name, sku, category, quantity, unit, storage, expiry_date FROM inventory WHERE 1=1"
    params = []

    if search:
        query += " AND (item_name LIKE ? OR sku LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    if category != "All Categories":
        query += " AND category = ?"
        params.append(category)
    if storage != "All Storage":
        query += " AND storage = ?"
        params.append(storage)

    query += " ORDER BY id ASC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()

    # Filter by status in Python (computed from expiry_date)
    today = datetime.now().date()
    filtered = []
    for r in rows:
        try:
            exp = datetime.strptime(r[7], "%Y-%m-%d").date()
        except ValueError:
            exp = today
        days_left = (exp - today).days
        if days_left < 0:
            item_status = "Expired"
        elif days_left <= 7:
            item_status = "Expiring Soon"
        else:
            item_status = "Fresh"

        if status == "All Status" or status == item_status:
            filtered.append(r + (item_status,))

    return filtered





def _delete_item(item_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM inventory WHERE id=?", (item_id,))
    conn.commit()
    conn.close()


def _get_stats():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(DISTINCT category) FROM inventory")
    total_categories = cur.fetchone()[0]
    cur.execute("SELECT expiry_date FROM inventory")
    rows = cur.fetchall()
    conn.close()

    today = datetime.now().date()
    near_expiry = 0
    expired = 0
    for (exp_str,) in rows:
        try:
            exp = datetime.strptime(exp_str, "%Y-%m-%d").date()
        except ValueError:
            continue
        days_left = (exp - today).days
        if days_left < 0:
            expired += 1
        elif days_left <= 7:
            near_expiry += 1

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT SUM(quantity * 10) FROM inventory")  # rough estimate $10/unit
    stock_val = cur.fetchone()[0] or 0
    conn.close()

    return total_categories, near_expiry, expired, int(stock_val)


def inventory_view(page: ft.Page) -> ft.View:
    _init_inventory_db()
    colors = LIGHT.copy() if page.theme_mode == ft.ThemeMode.LIGHT else DARK.copy()

    # State
    current_page = [1]
    items_per_page = 6

    def card_shadow():
        return ft.BoxShadow(
            blur_radius=12,
            spread_radius=0,
            color=colors["SHADOW"],
            offset=ft.Offset(0, 2),
        )

    # ───────────────────── SIDEBAR ─────────────────────

    logo_icon = ft.Image(
        src="assets/logo.png",
        width=36,
        height=36,
        fit=ft.BoxFit.CONTAIN,
    )

    logo_text = ft.Text(
        "Kitchen Food Waste",
        size=15,
        weight=ft.FontWeight.W_700,
        color=colors["TEXT"],
        overflow=ft.TextOverflow.ELLIPSIS,
        max_lines=1,
    )

    nav_items_data = [
        (ft.Icons.SPACE_DASHBOARD_OUTLINED, "Dashboard", False, "/dashboard"),
        (ft.Icons.INVENTORY_2_OUTLINED, "Inventory", True, "/inventory"),
        (ft.Icons.TIMER_OUTLINED, "Expiry Monitor", False, None),
        (ft.Icons.RECEIPT_LONG_OUTLINED, "Waste Logs", False, None),
        (ft.Icons.BAR_CHART, "Reports", False, None),
        (ft.Icons.CATEGORY_OUTLINED, "Categories", False, None),
        (ft.Icons.PEOPLE_OUTLINE, "Users & Staff", False, None),
        (ft.Icons.SETTINGS_OUTLINED, "Settings", False, None),
    ]

    def build_nav_item(icon, label, active=False, route=None):
        text_color = colors["ORANGE"] if active else colors["SIDEBAR_TEXT"]
        icon_color = colors["ORANGE"] if active else colors["SIDEBAR_ICON"]
        bg = colors["SIDEBAR_ACTIVE_BG"] if active else "transparent"
        weight = ft.FontWeight.W_600 if active else ft.FontWeight.W_400

        row_controls = [
            ft.Icon(icon, size=20, color=icon_color),
            ft.Text(
                label, size=14, color=text_color,
                weight=weight, expand=True,
            ),
        ]
        if active:
            row_controls.append(
                ft.Icon(ft.Icons.CHEVRON_RIGHT, size=18, color=icon_color)
            )

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

    nav_column = ft.Column(
        spacing=2,
        controls=[build_nav_item(i, l, a, r) for i, l, a, r in nav_items_data],
    )

    def on_sign_out(e):
        page.session.store.clear()
        page.go("/")

    sign_out = ft.Container(
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
    )

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
                sign_out,
            ],
        ),
    )

    # ───────────────────── TOP BAR ─────────────────────

    top_search = ft.TextField(
        hint_text="Search items, batches, or logs...",
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

    username = page.session.store.get("username") or "Chef Julian"
    initials = username[:2].upper()

    user_avatar = ft.Container(
        width=38,
        height=38,
        bgcolor=colors["AVATAR_BG"],
        border_radius=19,
        alignment=ft.Alignment(0, 0),
        content=ft.Text(
            initials, size=14,
            weight=ft.FontWeight.W_600,
            color=colors["ORANGE"],
        ),
    )

    top_bar = ft.Container(
        padding=ft.Padding.symmetric(horizontal=32, vertical=14),
        border=ft.Border(bottom=ft.BorderSide(1, colors["BORDER"])),
        bgcolor=colors["CARD_BG"],
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                top_search,
                ft.Row(
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.NOTIFICATIONS_NONE, size=22, color=colors["MUTED"]),
                        ft.Column(
                            spacing=0,
                            horizontal_alignment=ft.CrossAxisAlignment.END,
                            controls=[
                                ft.Text(
                                    username, size=14,
                                    weight=ft.FontWeight.W_600,
                                    color=colors["TEXT"],
                                ),
                                ft.Text(
                                    "Kitchen Manager", size=12,
                                    color=colors["MUTED"],
                                ),
                            ],
                        ),
                        user_avatar,
                    ],
                ),
            ],
        ),
    )

    # ───────────────────── CONTENT HEADER ─────────────────────

    def open_add_page(e):
        if page.session.store.contains_key("edit_item_id"):
            page.session.store.remove("edit_item_id")
        page.go("/add-item")

    content_header = ft.Container(
        padding=ft.Padding.only(left=32, right=32, top=24, bottom=8),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Column(
                    spacing=4,
                    controls=[
                        ft.Text(
                            "Inventory", size=26,
                            weight=ft.FontWeight.W_700,
                            color=colors["TEXT"],
                        ),
                        ft.Text(
                            "Manage your food stock levels and monitor expiry dates.",
                            size=14, color=colors["MUTED"],
                        ),
                    ],
                ),
                ft.Button(
                    "Add Food Item",
                    icon=ft.Icons.ADD,
                    on_click=open_add_page,
                    style=ft.ButtonStyle(
                        bgcolor=colors["ORANGE"],
                        color="#FFFFFF",
                        elevation=0,
                        shape=ft.RoundedRectangleBorder(radius=8),
                        padding=ft.Padding.symmetric(
                            horizontal=20, vertical=12,
                        ),
                    ),
                ),
            ],
        ),
    )

    # ───────────────────── FILTERS ─────────────────────

    filter_search = ft.TextField(
        hint_text="Search items by name, SKU...",
        width=280,
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
        on_change=lambda e: refresh_table(),
    )

    filter_category = ft.Dropdown(
        value="All Categories",
        width=170,
        height=42,
        border_radius=8,
        border_color=colors["BORDER"],
        focused_border_color=colors["ORANGE"],
        bgcolor=colors["CARD_BG"],
        text_size=14,
        color=colors["TEXT"],
        options=[ft.DropdownOption(key="All Categories", text="All Categories")]
        + [ft.DropdownOption(key=c, text=c) for c in CATEGORIES],
        on_select=lambda e: refresh_table(),
    )

    filter_status = ft.Dropdown(
        value="All Status",
        width=140,
        height=42,
        border_radius=8,
        border_color=colors["BORDER"],
        focused_border_color=colors["ORANGE"],
        bgcolor=colors["CARD_BG"],
        text_size=14,
        color=colors["TEXT"],
        options=[
            ft.DropdownOption(key="All Status", text="All Status"),
            ft.DropdownOption(key="Fresh", text="Fresh"),
            ft.DropdownOption(key="Expiring Soon", text="Expiring Soon"),
            ft.DropdownOption(key="Expired", text="Expired"),
        ],
        on_select=lambda e: refresh_table(),
    )

    filter_storage = ft.Dropdown(
        value="All Storage",
        width=160,
        height=42,
        border_radius=8,
        border_color=colors["BORDER"],
        focused_border_color=colors["ORANGE"],
        bgcolor=colors["CARD_BG"],
        text_size=14,
        color=colors["TEXT"],
        options=[ft.DropdownOption(key="All Storage", text="All Storage")]
        + [ft.DropdownOption(key=s, text=s) for s in STORAGES],
        on_select=lambda e: refresh_table(),
    )

    def on_refresh(e):
        filter_search.value = ""
        filter_category.value = "All Categories"
        filter_status.value = "All Status"
        filter_storage.value = "All Storage"
        current_page[0] = 1
        refresh_table()

    refresh_btn = ft.IconButton(
        icon=ft.Icons.REFRESH,
        icon_size=20,
        icon_color=colors["MUTED"],
        tooltip="Reset filters",
        on_click=on_refresh,
    )

    filters_row = ft.Container(
        padding=ft.Padding.symmetric(horizontal=32, vertical=10),
        content=ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[filter_search, filter_category, filter_status, filter_storage, refresh_btn],
        ),
    )

    # ───────────────────── TABLE ─────────────────────

    table_body = ft.Column(spacing=0)
    pagination_row = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    def get_status_info(expiry_str):
        today = datetime.now().date()
        try:
            exp = datetime.strptime(expiry_str, "%Y-%m-%d").date()
        except ValueError:
            return "Fresh", colors["GREEN"], colors["GREEN_BG"]
        days_left = (exp - today).days
        if days_left < 0:
            return "Expired", colors["RED"], colors["RED_BG"]
        elif days_left <= 7:
            return "Expiring Soon", colors["ORANGE"], colors["ORANGE_BG"]
        else:
            return "Fresh", colors["GREEN"], colors["GREEN_BG"]

    def build_table_header():
        headers = [
            ("Item Name", True, 2.5),
            ("Category", False, 1),
            ("Quantity", False, 1),
            ("Storage", False, 1.2),
            ("Soonest Expiry", False, 1.2),
            ("Status", False, 1.2),
            ("", False, 0.3),
        ]
        cells = []
        for label, bold, flex in headers:
            cells.append(
                ft.Container(
                    expand=int(flex * 10),
                    content=ft.Text(
                        label, size=12,
                        color=colors["MUTED"],
                        weight=ft.FontWeight.W_600,
                    ),
                )
            )
        return ft.Container(
            bgcolor=colors["TABLE_HEADER_BG"],
            padding=ft.Padding.symmetric(horizontal=20, vertical=12),
            border=ft.Border(bottom=ft.BorderSide(1, colors["DIVIDER"])),
            content=ft.Row(controls=cells, spacing=8),
        )

    def build_table_row(item):
        item_id, name, sku, category, qty, unit, storage, expiry, status_text = item
        status_label, status_color, status_bg = get_status_info(expiry)

        # Format quantity
        qty_display = f"{int(qty)}" if qty == int(qty) else f"{qty}"

        # Item name cell with icon and SKU
        name_cell = ft.Container(
            expand=25,
            content=ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=36,
                        height=36,
                        bgcolor=colors["ORANGE_BG"],
                        border_radius=18,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Icon(ft.Icons.RESTAURANT, size=16, color=colors["ORANGE"]),
                    ),
                    ft.Column(
                        spacing=0,
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.Text(
                                name, size=14,
                                weight=ft.FontWeight.W_500,
                                color=colors["TEXT"],
                            ),
                            ft.Text(
                                sku, size=11,
                                color=colors["MUTED"],
                            ),
                        ],
                    ),
                ],
            ),
        )

        category_cell = ft.Container(
            expand=10,
            content=ft.Text(category, size=13, color=colors["TEXT_SECONDARY"]),
        )

        quantity_cell = ft.Container(
            expand=10,
            content=ft.Text(
                f"{qty_display} {unit}", size=13,
                color=colors["TEXT"],
                weight=ft.FontWeight.W_500,
            ),
        )

        storage_cell = ft.Container(
            expand=12,
            content=ft.Text(storage, size=13, color=colors["TEXT_SECONDARY"]),
        )

        expiry_cell = ft.Container(
            expand=12,
            content=ft.Text(expiry, size=13, color=colors["TEXT_SECONDARY"]),
        )

        status_cell = ft.Container(
            expand=12,
            content=ft.Container(
                padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                bgcolor=status_bg,
                border_radius=4,
                content=ft.Text(
                    status_label, size=11,
                    color=status_color,
                    weight=ft.FontWeight.W_600,
                ),
                width=110,
                alignment=ft.Alignment(0, 0),
            ),
        )

        def on_edit(e, iid=item_id):
            page.session.store.set("edit_item_id", iid)
            page.go("/add-item")

        def on_delete(e, iid=item_id, iname=name):
            show_delete_dialog(iid, iname)

        actions_cell = ft.Container(
            expand=3,
            content=ft.PopupMenuButton(
                icon=ft.Icons.MORE_VERT,
                icon_size=18,
                icon_color=colors["MUTED"],
                items=[
                    ft.PopupMenuItem(
                        content=ft.Text("Edit"),
                        icon=ft.Icons.EDIT_OUTLINED,
                        on_click=on_edit,
                    ),
                    ft.PopupMenuItem(
                        content=ft.Text("Delete"),
                        icon=ft.Icons.DELETE_OUTLINE,
                        on_click=on_delete,
                    ),
                ],
            ),
        )

        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=20, vertical=10),
            border=ft.Border(bottom=ft.BorderSide(1, colors["DIVIDER"])),
            content=ft.Row(
                controls=[name_cell, category_cell, quantity_cell, storage_cell, expiry_cell, status_cell, actions_cell],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def build_pagination(total_items):
        total_pages = max(1, math.ceil(total_items / items_per_page))
        start = (current_page[0] - 1) * items_per_page + 1
        end = min(current_page[0] * items_per_page, total_items)

        def go_page(e, p):
            current_page[0] = p
            refresh_table()

        def go_prev(e):
            if current_page[0] > 1:
                current_page[0] -= 1
                refresh_table()

        def go_next(e):
            if current_page[0] < total_pages:
                current_page[0] += 1
                refresh_table()

        showing_text = ft.Text(
            f"Showing {start}-{end} of {total_items} items",
            size=13,
            color=colors["MUTED"],
        )

        page_btns = []
        page_btns.append(
            ft.TextButton(
                "Previous",
                disabled=current_page[0] <= 1,
                on_click=go_prev,
                style=ft.ButtonStyle(
                    color=colors["TEXT_SECONDARY"],
                    padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                ),
            )
        )

        # Show page numbers with ellipsis
        pages_to_show = []
        if total_pages <= 5:
            pages_to_show = list(range(1, total_pages + 1))
        else:
            pages_to_show = [1, 2, 3]
            if current_page[0] > 3:
                pages_to_show = [1, "...", current_page[0]]
            if current_page[0] < total_pages - 1:
                pages_to_show.append("...")
            pages_to_show.append(total_pages)
            # Deduplicate
            seen = set()
            unique = []
            for p in pages_to_show:
                if p not in seen:
                    seen.add(p)
                    unique.append(p)
            pages_to_show = unique

        for p in pages_to_show:
            if p == "...":
                page_btns.append(
                    ft.Text("...", size=13, color=colors["MUTED"])
                )
            else:
                is_current = p == current_page[0]
                page_btns.append(
                    ft.Container(
                        width=32,
                        height=32,
                        border_radius=16,
                        bgcolor=colors["ORANGE"] if is_current else "transparent",
                        alignment=ft.Alignment(0, 0),
                        ink=True,
                        on_click=lambda e, pg=p: go_page(e, pg),
                        content=ft.Text(
                            str(p), size=13,
                            color="#FFFFFF" if is_current else colors["TEXT_SECONDARY"],
                            weight=ft.FontWeight.W_600 if is_current else ft.FontWeight.W_400,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    )
                )

        page_btns.append(
            ft.TextButton(
                "Next",
                disabled=current_page[0] >= total_pages,
                on_click=go_next,
                style=ft.ButtonStyle(
                    color=colors["TEXT_SECONDARY"],
                    padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                ),
            )
        )

        pagination_row.controls = [
            showing_text,
            ft.Row(spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=page_btns),
        ]

    def refresh_table():
        search = filter_search.value or ""
        category = filter_category.value or "All Categories"
        status = filter_status.value or "All Status"
        storage = filter_storage.value or "All Storage"

        all_items = _get_items(search, category, status, storage)
        total = len(all_items)

        total_pages = max(1, math.ceil(total / items_per_page))
        if current_page[0] > total_pages:
            current_page[0] = total_pages

        start_idx = (current_page[0] - 1) * items_per_page
        page_items = all_items[start_idx : start_idx + items_per_page]

        table_body.controls = [build_table_header()]
        for item in page_items:
            table_body.controls.append(build_table_row(item))

        build_pagination(total)

        # Update stats
        update_stats()

        page.update()

    # ───────────────────── TABLE CARD ─────────────────────

    table_card = ft.Container(
        bgcolor=colors["CARD_BG"],
        border=ft.Border.all(1, colors["BORDER"]),
        border_radius=12,
        shadow=card_shadow(),
        content=ft.Column(
            spacing=0,
            controls=[
                table_body,
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=20, vertical=12),
                    content=pagination_row,
                ),
            ],
        ),
    )

    table_area = ft.Container(
        padding=ft.Padding.symmetric(horizontal=32, vertical=6),
        content=table_card,
    )

    # ───────────────────── BOTTOM STATS ─────────────────────

    stat_total_cat = ft.Text("0", size=28, weight=ft.FontWeight.W_700, color="#FFFFFF")
    stat_near_expiry = ft.Text("0", size=28, weight=ft.FontWeight.W_700, color=colors["TEXT"])
    stat_expired = ft.Text("0", size=28, weight=ft.FontWeight.W_700, color=colors["TEXT"])
    stat_stock_value = ft.Text("$0", size=28, weight=ft.FontWeight.W_700, color=colors["TEXT"])

    def build_stat_box(label, value_widget, bg_color, text_color):
        return ft.Container(
            expand=True,
            bgcolor=bg_color,
            border_radius=12,
            padding=ft.Padding.all(20),
            border=ft.Border.all(1, colors["BORDER"]) if bg_color == colors["CARD_BG"] else None,
            content=ft.Column(
                spacing=4,
                controls=[
                    ft.Text(
                        label, size=12,
                        weight=ft.FontWeight.W_600,
                        color=text_color,
                    ),
                    value_widget,
                ],
            ),
        )

    stats_bottom = ft.Container(
        padding=ft.Padding.only(left=32, right=32, top=14, bottom=10),
        content=ft.Row(
            spacing=16,
            controls=[
                build_stat_box("TOTAL CATEGORIES", stat_total_cat, colors["ORANGE"], "#FFFFFF"),
                build_stat_box("NEAR EXPIRY", stat_near_expiry, colors["CARD_BG"], colors["MUTED"]),
                build_stat_box("EXPIRED ITEMS", stat_expired, colors["CARD_BG"], colors["MUTED"]),
                build_stat_box("STOCK VALUE", stat_stock_value, colors["CARD_BG"], colors["MUTED"]),
            ],
        ),
    )

    def update_stats():
        total_cat, near_exp, expired, stock_val = _get_stats()
        stat_total_cat.value = str(total_cat)
        stat_near_expiry.value = str(near_exp)
        stat_expired.value = str(expired)
        stat_stock_value.value = f"${stock_val:,}"

    # ───────────────────── FOOTER ─────────────────────

    footer = ft.Container(
        padding=ft.Padding.symmetric(horizontal=32, vertical=14),
        border=ft.Border(top=ft.BorderSide(1, colors["DIVIDER"])),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text(
                    "© 2026 Kitchen Food Waste Tracker. All rights reserved.",
                    size=12,
                    color=colors["MUTED"],
                ),
                ft.Row(
                    spacing=20,
                    controls=[
                        ft.Text("Privacy Policy", size=12, color=colors["MUTED"]),
                        ft.Text("Terms of Service", size=12, color=colors["MUTED"]),
                        ft.Text("Help Center", size=12, color=colors["MUTED"]),
                    ],
                ),
            ],
        ),
    )

    def show_delete_dialog(item_id, item_name):
        def on_confirm(e):
            _delete_item(item_id)
            page.pop_dialog()
            refresh_table()

        def on_cancel(e):
            page.pop_dialog()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete Item", size=18, weight=ft.FontWeight.W_600, color=colors["RED"]),
            content=ft.Text(
                f'Are you sure you want to delete "{item_name}"?\nThis action cannot be undone.',
                size=14,
                color=colors["TEXT_SECONDARY"],
            ),
            actions=[
                ft.TextButton("Cancel", on_click=on_cancel, style=ft.ButtonStyle(color=colors["MUTED"])),
                ft.Button(
                    "Delete",
                    on_click=on_confirm,
                    style=ft.ButtonStyle(
                        bgcolor=colors["RED"],
                        color="#FFFFFF",
                        shape=ft.RoundedRectangleBorder(radius=8),
                        padding=ft.Padding.symmetric(horizontal=24, vertical=10),
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=colors["CARD_BG"],
            shape=ft.RoundedRectangleBorder(radius=12),
        )
        page.show_dialog(dlg)

    # ───────────────────── LAYOUT ASSEMBLY ─────────────────────

    # Initial load
    refresh_table()

    scrollable_content = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=0,
        controls=[
            content_header,
            filters_row,
            table_area,
            stats_bottom,
            ft.Container(expand=True),
            footer,
        ],
    )

    content_area = ft.Container(
        expand=True,
        bgcolor=colors["BG"],
        content=ft.Column(
            expand=True,
            spacing=0,
            controls=[top_bar, scrollable_content],
        ),
    )

    layout = ft.Row(
        expand=True,
        spacing=0,
        controls=[sidebar, content_area],
    )

    return ft.View(
        route="/inventory",
        padding=0,
        spacing=0,
        bgcolor=colors["BG"],
        controls=[layout],
    )
