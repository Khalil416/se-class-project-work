import flet as ft
import sqlite3
import requests

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

DEFAULT_CATEGORIES = [
    ("Dairy & Eggs", "Milk, cheese, eggs, and similar chilled products.", 7),
    ("Produce/Fruits", "Fresh produce, fruit, herbs, and vegetables.", 5),
    ("Meats & Seafood", "Raw meat, poultry, fish, and seafood items.", 3),
    ("Bakery", "Bread, rolls, pastries, and baked goods.", 2),
    ("Dry Goods", "Shelf-stable pantry goods and long-life items.", 365),
]


def _init_categories_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT NOT NULL UNIQUE,
            description TEXT,
            shelf_life_days INTEGER DEFAULT 7
        )
        """
    )
    cur.execute("PRAGMA table_info(categories)")
    existing = {row[1] for row in cur.fetchall()}
    migrations = [
        ("description", "TEXT DEFAULT ''"),
        ("shelf_life_days", "INTEGER DEFAULT 7"),
    ]
    for col, typedef in migrations:
        if col not in existing:
            cur.execute(f"ALTER TABLE categories ADD COLUMN {col} {typedef}")

    cur.execute("SELECT COUNT(*) FROM categories")
    if (cur.fetchone()[0] or 0) == 0:
        cur.executemany(
            "INSERT INTO categories (category_name, description, shelf_life_days) VALUES (?, ?, ?)",
            DEFAULT_CATEGORIES,
        )
    conn.commit()
    conn.close()


def _get_categories(search_text=""):
    try:
        response = requests.get(f"{API_URL}/categories", params={"search_text": search_text}, timeout=5)
        if response.status_code == 200:
            return response.json().get("data", [])
    except requests.exceptions.RequestException:
        pass
    return []


def _get_metrics():
    try:
        categories = requests.get(f"{API_URL}/categories", timeout=5).json().get("data", [])
        inventory = requests.get(f"{API_URL}/inventory", timeout=5).json().get("data", [])
        total_categories = len(categories)
        tracked_items = len(inventory)
        avg_shelf_life = sum(float(c.get("shelf_life_days") or 0) for c in categories) / total_categories if total_categories else 0
        return total_categories, tracked_items, avg_shelf_life
    except requests.exceptions.RequestException:
        return 0, 0, 0


def _get_total_items(category_name):
    try:
        response = requests.get(f"{API_URL}/inventory", params={"category": category_name}, timeout=5)
        if response.status_code == 200:
            return response.json().get("count", 0)
    except requests.exceptions.RequestException:
        pass
    return 0


def categories_view(page: ft.Page) -> ft.View:
    _init_categories_db()
    colors = LIGHT.copy() if page.theme_mode == ft.ThemeMode.LIGHT else DARK.copy()
    role = page.session.store.get("role") or "chef"

    current_page = [1]
    items_per_page = 6
    editing_id = [None]

    def card_shadow():
        return ft.BoxShadow(blur_radius=12, spread_radius=0, color=colors["SHADOW"], offset=ft.Offset(0, 2))

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

    def color_for_initial(name):
        palette = [colors["ORANGE"], colors["GREEN"], "#1D4ED8", colors["RED"], "#0F766E", "#B45309"]
        return palette[sum(ord(ch) for ch in name) % len(palette)] if name else colors["ORANGE"]

    def metric_card(icon, title, value_control, helper_text):
        return ft.Container(
            expand=True,
            bgcolor=colors["CARD_BG"],
            border=ft.Border.all(1, colors["BORDER"]),
            border_radius=12,
            padding=20,
            shadow=card_shadow(),
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        spacing=8,
                        controls=[
                            ft.Icon(icon, size=16, color=colors["MUTED"]),
                            ft.Text(title, size=14, weight=ft.FontWeight.W_600, color=colors["TEXT"]),
                        ],
                    ),
                    value_control,
                    ft.Text(helper_text, size=12, color=colors["MUTED"]),
                ],
            ),
        )

    def shelf_pill(days):
        is_warning = days <= 3
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            bgcolor=colors["ORANGE_BG"] if is_warning else colors["GREEN_BG"],
            border_radius=4,
            content=ft.Text(
                f"{days} Days",
                size=11,
                color=colors["ORANGE"] if is_warning else colors["GREEN"],
                weight=ft.FontWeight.W_600,
            ),
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
                ft.Container(padding=ft.Padding.only(left=6, bottom=24), content=ft.Row(spacing=10, controls=[logo_icon, logo_text])),
                nav_column,
                ft.Container(expand=True),
                ft.Divider(height=1, color=colors["DIVIDER"]),
                ft.Container(padding=ft.Padding.symmetric(horizontal=14, vertical=10), ink=True, on_click=on_sign_out, content=ft.Row(spacing=12, controls=[ft.Icon(ft.Icons.LOGOUT, size=20, color=colors["SIDEBAR_TEXT"]), ft.Text("Sign Out", size=14, color=colors["SIDEBAR_TEXT"]) ])),
            ],
        ),
    )

    username = page.session.store.get("username") or "User"
    initials = username[:2].upper()

    topbar_search = ft.TextField(
        hint_text="Search categories...",
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
                            ft.Column(spacing=0, horizontal_alignment=ft.CrossAxisAlignment.END, controls=[ft.Text(username, size=14, weight=ft.FontWeight.W_600, color=colors["TEXT"]), ft.Text(page.session.store.get("role") or "Kitchen Staff", size=12, color=colors["MUTED"])]),
                            ft.Container(width=38, height=38, bgcolor=colors["AVATAR_BG"], border_radius=19, alignment=ft.Alignment(0, 0), content=ft.Text(initials, size=14, weight=ft.FontWeight.W_600, color=colors["ORANGE"])),
                        ],
                    ),
                ),
            ],
        ),
    )

    title_block = ft.Container(padding=ft.Padding.only(left=32, right=32, top=24, bottom=8), content=ft.Column(spacing=4, controls=[ft.Text("Categories Management", size=26, weight=ft.FontWeight.W_700, color=colors["TEXT"]), ft.Text("Configure food categories and set default shelf life", size=14, color=colors["MUTED"])]))

    search_field = ft.TextField(
        hint_text="Search categories by name or description...",
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
    )

    add_button = ft.Button(
        "+ Add Category",
        icon=ft.Icons.ADD,
        on_click=lambda e: open_category_dialog(),
        style=ft.ButtonStyle(bgcolor=colors["ORANGE"], color="#FFFFFF", elevation=0, shape=ft.RoundedRectangleBorder(radius=8), padding=ft.Padding.symmetric(horizontal=18, vertical=12)),
    )

    metrics_total = ft.Text("0", size=28, weight=ft.FontWeight.W_700, color=colors["TEXT"])
    metrics_tracked = ft.Text("0", size=28, weight=ft.FontWeight.W_700, color=colors["TEXT"])
    metrics_avg = ft.Text("0 Days", size=28, weight=ft.FontWeight.W_700, color=colors["TEXT"])

    def metric_card(icon, title, value_control, helper_text):
        return ft.Container(
            expand=True,
            bgcolor=colors["CARD_BG"],
            border=ft.Border.all(1, colors["BORDER"]),
            border_radius=12,
            padding=20,
            shadow=card_shadow(),
            content=ft.Column(spacing=8, controls=[ft.Row(spacing=8, controls=[ft.Icon(icon, size=16, color=colors["MUTED"]), ft.Text(title, size=14, weight=ft.FontWeight.W_600, color=colors["TEXT"])]), value_control, ft.Text(helper_text, size=12, color=colors["MUTED"])]),
        )

    table_body = ft.Column(spacing=0)
    pagination_row = ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
    status_text = ft.Text("", size=12, color=colors["RED"], visible=False)

    def get_summary_text():
        total_categories, tracked_items, avg_shelf_life = _get_metrics()
        metrics_total.value = str(total_categories)
        metrics_tracked.value = str(tracked_items)
        metrics_avg.value = f"{avg_shelf_life:.0f} Days"

    def build_table_header():
        headers = [("Category Name", 2.6), ("Shelf Life", 1.2), ("Description", 3.0), ("Total Items", 1.0), ("Actions", 1.0)]
        return ft.Container(bgcolor=colors["TABLE_HEADER_BG"], padding=ft.Padding.symmetric(horizontal=20, vertical=12), border=ft.Border(bottom=ft.BorderSide(1, colors["DIVIDER"])), content=ft.Row(spacing=8, controls=[ft.Container(expand=26, content=ft.Text(headers[0][0], size=12, color=colors["MUTED"], weight=ft.FontWeight.W_600)), ft.Container(expand=12, content=ft.Text(headers[1][0], size=12, color=colors["MUTED"], weight=ft.FontWeight.W_600)), ft.Container(expand=30, content=ft.Text(headers[2][0], size=12, color=colors["MUTED"], weight=ft.FontWeight.W_600)), ft.Container(expand=10, content=ft.Text(headers[3][0], size=12, color=colors["MUTED"], weight=ft.FontWeight.W_600)), ft.Container(expand=10, content=ft.Text(headers[4][0], size=12, color=colors["MUTED"], weight=ft.FontWeight.W_600))]))

    def open_category_dialog(category=None):
        editing_id[0] = category["category_id"] if category else None
        f_name.value = category["category_name"] if category else ""
        f_description.value = category["description"] if category else ""
        f_shelf.value = str(category["shelf_life_days"] if category else 7)
        error_text.visible = False
        page.show_dialog(category_dialog)

    def validate_category():
        name_val = (f_name.value or "").strip()
        shelf_val = (f_shelf.value or "").strip()
        if not name_val:
            error_text.value = "Category name is required."
            error_text.visible = True
            page.update()
            return None
        try:
            shelf_int = int(shelf_val)
        except ValueError:
            error_text.value = "Shelf life must be a whole number."
            error_text.visible = True
            page.update()
            return None
        if shelf_int <= 0:
            error_text.value = "Shelf life must be greater than zero."
            error_text.visible = True
            page.update()
            return None
        return {"category_name": name_val, "description": (f_description.value or "").strip(), "shelf_life_days": shelf_int}

    def refresh_table():
        rows = _get_categories((search_field.value or "").strip())
        total_pages = max(1, (len(rows) + items_per_page - 1) // items_per_page)
        if current_page[0] > total_pages:
            current_page[0] = total_pages
        start_idx = (current_page[0] - 1) * items_per_page
        page_rows = rows[start_idx:start_idx + items_per_page]

        table_body.controls = [build_table_header()]
        if not page_rows:
            table_body.controls.append(ft.Container(padding=ft.Padding.symmetric(vertical=40), alignment=ft.Alignment(0, 0), content=ft.Text("No categories match the current search.", size=14, color=colors["MUTED"])))
        else:
            for row in page_rows:
                table_body.controls.append(build_table_row(row))

        build_pagination(len(rows))
        get_summary_text()
        page.update()

    def on_search_change(e):
        current_page[0] = 1
        refresh_table()

    def build_pagination(total_items):
        total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
        start = (current_page[0] - 1) * items_per_page + 1 if total_items else 0
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

        page_btns = [ft.TextButton("Previous", disabled=current_page[0] <= 1, on_click=go_prev, style=ft.ButtonStyle(color=colors["TEXT_SECONDARY"], padding=ft.Padding.symmetric(horizontal=10, vertical=6)))]
        pages_to_show = list(range(1, total_pages + 1)) if total_pages <= 5 else [1, 2, 3, "...", total_pages]
        for p in pages_to_show:
            if p == "...":
                page_btns.append(ft.Text("...", size=13, color=colors["MUTED"]))
            else:
                is_current = p == current_page[0]
                page_btns.append(ft.Container(width=32, height=32, border_radius=16, bgcolor=colors["ORANGE"] if is_current else "transparent", alignment=ft.Alignment(0, 0), ink=True, on_click=lambda e, pg=p: go_page(e, pg), content=ft.Text(str(p), size=13, color="#FFFFFF" if is_current else colors["TEXT_SECONDARY"], weight=ft.FontWeight.W_600 if is_current else ft.FontWeight.W_400, text_align=ft.TextAlign.CENTER)))
        page_btns.append(ft.TextButton("Next", disabled=current_page[0] >= total_pages, on_click=go_next, style=ft.ButtonStyle(color=colors["TEXT_SECONDARY"], padding=ft.Padding.symmetric(horizontal=10, vertical=6))))
        pagination_row.controls = [ft.Text(f"Showing {start}-{end} of {total_items} categories", size=13, color=colors["MUTED"]), ft.Row(spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=page_btns)]

    def build_table_row(row):
        category_id = row["category_id"]
        category_name = row["category_name"]
        description = row.get("description") or "—"
        shelf_life = int(row.get("shelf_life_days") or 0)
        total_items = _get_total_items(category_name)

        def on_edit(e, cat=row):
            open_category_dialog(cat)

        def on_delete(e, cat_id=category_id, cat_name=category_name):
            show_delete_dialog(cat_id, cat_name)

        initial_bg = color_for_initial(category_name)

        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=20, vertical=10),
            border=ft.Border(bottom=ft.BorderSide(1, colors["DIVIDER"])),
            content=ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        expand=26,
                        content=ft.Row(
                            spacing=12,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Container(width=36, height=36, bgcolor=initial_bg, border_radius=18, alignment=ft.Alignment(0, 0), content=ft.Text(category_name[:1].upper(), size=14, weight=ft.FontWeight.W_700, color="#FFFFFF")),
                                ft.Column(spacing=0, controls=[ft.Text(category_name, size=14, color=colors["TEXT"], weight=ft.FontWeight.W_500), ft.Text(f"ID: {category_id}", size=11, color=colors["MUTED"])]),
                            ],
                        ),
                    ),
                    ft.Container(expand=12, content=shelf_pill(shelf_life)),
                    ft.Container(expand=30, content=ft.Text(description, size=13, color=colors["TEXT_SECONDARY"])),
                    ft.Container(expand=10, content=ft.Text(str(total_items), size=13, color=colors["TEXT"], weight=ft.FontWeight.W_500)),
                    ft.Container(expand=10, content=ft.Row(spacing=4, controls=[ft.IconButton(icon=ft.Icons.EDIT_OUTLINED, icon_color=colors["ORANGE"], tooltip="Edit", on_click=on_edit), ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color=colors["RED"], tooltip="Delete", on_click=on_delete), ft.PopupMenuButton(icon=ft.Icons.MORE_VERT, icon_size=18, icon_color=colors["MUTED"], items=[ft.PopupMenuItem(content=ft.Text("Edit"), icon=ft.Icons.EDIT_OUTLINED, on_click=on_edit), ft.PopupMenuItem(content=ft.Text("Delete"), icon=ft.Icons.DELETE_OUTLINE, on_click=on_delete)])])),
                ],
            ),
        )

    def show_delete_dialog(category_id, category_name):
        delete_target[0] = (category_id, category_name)
        delete_text.value = f"Delete category '{category_name}'? This will remove it from the categories table."
        page.show_dialog(delete_dialog)

    def save_category(e):
        data = validate_category()
        if data is None:
            return
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        try:
            if editing_id[0] is None:
                cur.execute("INSERT INTO categories (category_name, description, shelf_life_days) VALUES (?, ?, ?)", (data["category_name"], data["description"], data["shelf_life_days"]))
            else:
                cur.execute("UPDATE categories SET category_name = ?, description = ?, shelf_life_days = ? WHERE category_id = ?", (data["category_name"], data["description"], data["shelf_life_days"], editing_id[0]))
            conn.commit()
        except sqlite3.IntegrityError:
            error_text.value = "Category name must be unique."
            error_text.visible = True
            page.update()
            conn.close()
            return
        conn.close()
        page.pop_dialog()
        current_page[0] = 1
        refresh_table()

    def cancel_category(e):
        page.pop_dialog()

    def confirm_delete(e):
        category_id, _category_name = delete_target[0]
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("DELETE FROM categories WHERE category_id = ?", (category_id,))
        conn.commit()
        conn.close()
        page.pop_dialog()
        current_page[0] = 1
        refresh_table()

    f_name = ft.TextField(hint_text="Category Name", width=360, border_radius=8, border_color=colors["BORDER"], focused_border_color=colors["ORANGE"], bgcolor=colors["CARD_BG"], color=colors["TEXT"], cursor_color=colors["ORANGE"])
    f_description = ft.TextField(hint_text="Description", width=360, multiline=True, min_lines=2, max_lines=4, border_radius=8, border_color=colors["BORDER"], focused_border_color=colors["ORANGE"], bgcolor=colors["CARD_BG"], color=colors["TEXT"], cursor_color=colors["ORANGE"])
    f_shelf = ft.TextField(hint_text="Shelf Life (Days)", width=180, keyboard_type=ft.KeyboardType.NUMBER, border_radius=8, border_color=colors["BORDER"], focused_border_color=colors["ORANGE"], bgcolor=colors["CARD_BG"], color=colors["TEXT"], cursor_color=colors["ORANGE"])
    error_text = ft.Text("", color=colors["RED"], visible=False)
    delete_target = [None]
    delete_text = ft.Text("", color=colors["TEXT"], size=13)

    category_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Row(spacing=10, controls=[ft.Icon(ft.Icons.CATEGORY_OUTLINED, color=colors["ORANGE"], size=22), ft.Column(spacing=2, controls=[ft.Text("Category Details", size=18, weight=ft.FontWeight.W_600, color=colors["TEXT"]), ft.Text("Add or edit a category", size=12, color=colors["MUTED"])])]),
        content=ft.Container(width=440, content=ft.Column(spacing=12, controls=[f_name, f_description, f_shelf, error_text])),
        actions=[ft.TextButton("Cancel", on_click=cancel_category, style=ft.ButtonStyle(color=colors["MUTED"])), ft.Button("Save Category", icon=ft.Icons.SAVE_OUTLINED, on_click=save_category, style=ft.ButtonStyle(bgcolor=colors["ORANGE"], color="#FFFFFF", elevation=0, shape=ft.RoundedRectangleBorder(radius=8), padding=ft.Padding.symmetric(horizontal=20, vertical=10)))],
        actions_alignment=ft.MainAxisAlignment.END,
        bgcolor=colors["CARD_BG"],
        shape=ft.RoundedRectangleBorder(radius=12),
    )

    delete_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Delete Category", size=18, weight=ft.FontWeight.W_600, color=colors["TEXT"]),
        content=ft.Container(width=380, content=delete_text),
        actions=[ft.TextButton("Cancel", on_click=cancel_category, style=ft.ButtonStyle(color=colors["MUTED"])), ft.Button("Delete", icon=ft.Icons.DELETE_OUTLINE, on_click=confirm_delete, style=ft.ButtonStyle(bgcolor=colors["RED"], color="#FFFFFF", elevation=0, shape=ft.RoundedRectangleBorder(radius=8), padding=ft.Padding.symmetric(horizontal=20, vertical=10)))],
        actions_alignment=ft.MainAxisAlignment.END,
        bgcolor=colors["CARD_BG"],
        shape=ft.RoundedRectangleBorder(radius=12),
    )

    metrics_row = ft.Container(padding=ft.Padding.symmetric(horizontal=32, vertical=10), content=ft.Row(spacing=16, controls=[metric_card(ft.Icons.CATEGORY_OUTLINED, "Total Categories", metrics_total, "Total category records"), metric_card(ft.Icons.INVENTORY_2_OUTLINED, "Tracked Items", metrics_tracked, "Rows currently in inventory"), metric_card(ft.Icons.TIMER_OUTLINED, "Avg Shelf Life", metrics_avg, "Average shelf life across categories")]))

    controls_row = ft.Container(
        padding=ft.Padding.symmetric(horizontal=32, vertical=10),
        content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[search_field, add_button]),
    )

    table_card = ft.Container(
        margin=ft.Margin(32, 8, 32, 0),
        bgcolor=colors["CARD_BG"],
        border=ft.Border.all(1, colors["BORDER"]),
        border_radius=12,
        shadow=card_shadow(),
        content=ft.Column(spacing=0, controls=[table_body, ft.Container(padding=ft.Padding.symmetric(horizontal=20, vertical=12), content=pagination_row)]),
    )

    footer = ft.Container(padding=ft.Padding.symmetric(horizontal=32, vertical=14), border=ft.Border(top=ft.BorderSide(1, colors["DIVIDER"])), content=ft.Text("© 2026 Kitchen Food Waste Tracker. All rights reserved.", size=12, color=colors["MUTED"]))

    content_area = ft.Container(
        expand=True,
        bgcolor=colors["BG"],
        content=ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
            controls=[top_bar, title_block, controls_row, metrics_row, table_card, footer],
        ),
    )

    layout = ft.Row(expand=True, spacing=0, controls=[sidebar, content_area])

    search_field.on_change = on_search_change
    refresh_table()

    return ft.View(route="/categories", padding=0, spacing=0, bgcolor=colors["BG"], controls=[layout])
