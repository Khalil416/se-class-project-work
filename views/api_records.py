import flet as ft
import requests
from datetime import datetime

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
UNITS = ["kg", "g", "L", "ml", "pieces", "dozen", "box", "pkt"]

API_URL = "http://127.0.0.1:8000"


def api_records_view(page: ft.Page) -> ft.View:
    colors = LIGHT.copy() if page.theme_mode == ft.ThemeMode.LIGHT else DARK.copy()
    role = page.session.store.get("role") or "manager"

    # ───────────────────── Helpers ─────────────────────

    def card_shadow():
        return ft.BoxShadow(
            blur_radius=12,
            spread_radius=0,
            color=colors["SHADOW"],
            offset=ft.Offset(0, 2),
        )

    def show_snackbar(message: str, is_error: bool = False):
        snack = ft.SnackBar(
            ft.Text(message, size=14, color="#FFFFFF"),
            duration=3000,
            bgcolor=colors["RED"] if is_error else colors["GREEN"],
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def get_role_label(r):
        return {"chef": "Kitchen Staff", "inventory_staff": "Inventory Manager", "manager": "General Manager"}.get(r, "Kitchen Staff")

    # ───────────────────── SIDEBAR ─────────────────────

    logo_icon = ft.Image(
        src="assets/logo.png",
        width=36,
        height=36,
        fit=ft.BoxFit.CONTAIN,
    )

    logo_text = ft.Text(
        "Kitchen Waste Tracker",
        size=15,
        weight=ft.FontWeight.W_700,
        color=colors["TEXT"],
        overflow=ft.TextOverflow.ELLIPSIS,
        max_lines=1,
    )

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
            (ft.Icons.API, "API Records", page.route == "/api-records", "/api-records"),
        ])

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
            on_click=nav_click if route and not active else None,
        )

    nav_column = ft.Column(spacing=2, controls=[build_nav_item(i, l, a, r) for i, l, a, r in nav_items_data])

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

    search_field = ft.TextField(
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

    username = page.session.store.get("username") or "User"
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
                search_field,
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
                                    ft.Text(get_role_label(role), size=12, color=colors["MUTED"]),
                                ],
                            ),
                            user_avatar,
                        ],
                    ),
                ),
            ],
        ),
    )

    # ───────────────────── CONTENT AREA ─────────────────────

    # Table columns
    table_body = ft.Column(spacing=0)

    def build_table_header():
        headers = [
            ("Item Name", 2.5),
            ("SKU", 1.2),
            ("Category", 1),
            ("Quantity", 1.2),
            ("Unit", 0.8),
            ("Storage", 1.2),
            ("Expiry Date", 1.2),
        ]
        cells = []
        for label, flex in headers:
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
        item_id = item.get("id", "N/A")
        name = item.get("item_name", "N/A")
        sku = item.get("sku", "N/A")
        category = item.get("category", "N/A")
        qty = item.get("quantity", 0)
        unit = item.get("unit", "")
        storage = item.get("storage", "N/A")
        expiry = item.get("expiry_date", "N/A")

        qty_val = round(float(qty), 3) if qty else 0
        qty_display = f"{qty_val:.3f}".rstrip("0").rstrip(".")

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
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ],
                    ),
                ],
            ),
        )

        sku_cell = ft.Container(
            expand=12,
            content=ft.Text(sku, size=13, color=colors["MUTED"]),
        )

        category_cell = ft.Container(
            expand=10,
            content=ft.Text(category, size=13, color=colors["TEXT_SECONDARY"]),
        )

        quantity_cell = ft.Container(
            expand=12,
            content=ft.Text(
                f"{qty_display} {unit}", size=13,
                color=colors["TEXT"],
                weight=ft.FontWeight.W_500,
            ),
        )

        unit_cell = ft.Container(
            expand=8,
            content=ft.Text(unit, size=13, color=colors["TEXT_SECONDARY"]),
        )

        storage_cell = ft.Container(
            expand=12,
            content=ft.Text(storage, size=13, color=colors["TEXT_SECONDARY"]),
        )

        expiry_cell = ft.Container(
            expand=12,
            content=ft.Text(expiry, size=13, color=colors["TEXT_SECONDARY"]),
        )

        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=20, vertical=10),
            border=ft.Border(bottom=ft.BorderSide(1, colors["DIVIDER"])),
            content=ft.Row(
                controls=[name_cell, sku_cell, category_cell, quantity_cell, unit_cell, storage_cell, expiry_cell],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def load_table():
        """Load inventory data from API."""
        table_body.controls = [build_table_header()]
        try:
            response = requests.get(f"{API_URL}/inventory", timeout=5)
            if response.status_code == 200:
                data = response.json()
                items = data.get("data", [])
                if not items:
                    table_body.controls.append(
                        ft.Container(
                            padding=ft.Padding.symmetric(horizontal=20, vertical=20),
                            content=ft.Text(
                                "No inventory records found",
                                size=14,
                                color=colors["MUTED"],
                                text_align=ft.TextAlign.CENTER,
                            ),
                        )
                    )
                else:
                    for item in items:
                        table_body.controls.append(build_table_row(item))
            else:
                show_snackbar("Failed to load records", is_error=True)
        except requests.exceptions.RequestException as e:
            show_snackbar(f"API unreachable: {str(e)}", is_error=True)
        page.update()

    # Records View (Tab 1)
    refresh_btn = ft.IconButton(
        icon=ft.Icons.REFRESH,
        icon_size=20,
        icon_color=colors["MUTED"],
        tooltip="Refresh records",
        on_click=lambda e: load_table(),
    )

    records_header = ft.Container(
        padding=ft.Padding.only(left=32, right=32, top=24, bottom=8),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(
                    "Inventory Records (API)", size=26,
                    weight=ft.FontWeight.W_700,
                    color=colors["TEXT"],
                ),
                refresh_btn,
            ],
        ),
    )

    table_card = ft.Container(
        bgcolor=colors["CARD_BG"],
        border=ft.Border.all(1, colors["BORDER"]),
        border_radius=12,
        shadow=card_shadow(),
        content=table_body,
    )

    table_area = ft.Container(
        padding=ft.Padding.symmetric(horizontal=32, vertical=12),
        content=table_card,
    )

    records_view = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=0,
        controls=[
            records_header,
            table_area,
            ft.Container(expand=True),
        ],
    )

    # Add View (Tab 2)
    add_header = ft.Container(
        padding=ft.Padding.only(left=32, right=32, top=24, bottom=8),
        content=ft.Text(
            "Add New Item via API", size=26,
            weight=ft.FontWeight.W_700,
            color=colors["TEXT"],
        ),
    )

    item_name_field = ft.TextField(
        label="Item Name",
        width=400,
        height=50,
        border_radius=8,
        border_color=colors["BORDER"],
        focused_border_color=colors["ORANGE"],
        bgcolor=colors["CARD_BG"],
        text_size=14,
        color=colors["TEXT"],
        label_style=ft.TextStyle(size=13, color=colors["MUTED"]),
    )

    category_field = ft.Dropdown(
        label="Category",
        width=400,
        height=50,
        border_radius=8,
        border_color=colors["BORDER"],
        focused_border_color=colors["ORANGE"],
        bgcolor=colors["CARD_BG"],
        text_size=14,
        color=colors["TEXT"],
        options=[ft.DropdownOption(text=c) for c in CATEGORIES],
        label_style=ft.TextStyle(size=13, color=colors["MUTED"]),
    )

    quantity_field = ft.TextField(
        label="Quantity",
        width=400,
        height=50,
        border_radius=8,
        border_color=colors["BORDER"],
        focused_border_color=colors["ORANGE"],
        bgcolor=colors["CARD_BG"],
        text_size=14,
        color=colors["TEXT"],
        label_style=ft.TextStyle(size=13, color=colors["MUTED"]),
    )

    unit_field = ft.Dropdown(
        label="Unit",
        width=400,
        height=50,
        border_radius=8,
        border_color=colors["BORDER"],
        focused_border_color=colors["ORANGE"],
        bgcolor=colors["CARD_BG"],
        text_size=14,
        color=colors["TEXT"],
        options=[ft.DropdownOption(text=u) for u in UNITS],
        label_style=ft.TextStyle(size=13, color=colors["MUTED"]),
    )

    storage_field = ft.Dropdown(
        label="Storage Location",
        width=400,
        height=50,
        border_radius=8,
        border_color=colors["BORDER"],
        focused_border_color=colors["ORANGE"],
        bgcolor=colors["CARD_BG"],
        text_size=14,
        color=colors["TEXT"],
        options=[ft.DropdownOption(text=s) for s in STORAGES],
        label_style=ft.TextStyle(size=13, color=colors["MUTED"]),
    )

    expiry_date_field = ft.TextField(
        label="Expiry Date (YYYY-MM-DD)",
        width=400,
        height=50,
        border_radius=8,
        border_color=colors["BORDER"],
        focused_border_color=colors["ORANGE"],
        bgcolor=colors["CARD_BG"],
        text_size=14,
        color=colors["TEXT"],
        label_style=ft.TextStyle(size=13, color=colors["MUTED"]),
    )

    def on_submit_click(e):
        """Submit new item to API."""
        # Validate all fields
        if not item_name_field.value or not item_name_field.value.strip():
            show_snackbar("Item name is required", is_error=True)
            return
        if not category_field.value:
            show_snackbar("Category is required", is_error=True)
            return
        if not quantity_field.value:
            show_snackbar("Quantity is required", is_error=True)
            return
        if not unit_field.value:
            show_snackbar("Unit is required", is_error=True)
            return
        if not storage_field.value:
            show_snackbar("Storage location is required", is_error=True)
            return
        if not expiry_date_field.value:
            show_snackbar("Expiry date is required", is_error=True)
            return

        try:
            qty = float(quantity_field.value)
        except ValueError:
            show_snackbar("Quantity must be a valid number", is_error=True)
            return

        payload = {
            "item_name": item_name_field.value.strip(),
            "category": category_field.value,
            "quantity": qty,
            "unit": unit_field.value,
            "storage": storage_field.value,
            "expiry_date": expiry_date_field.value,
        }

        try:
            response = requests.post(f"{API_URL}/inventory", json=payload, timeout=5)
            if response.status_code == 200:
                result = response.json()
                if "error" in result:
                    show_snackbar(result["error"], is_error=True)
                else:
                    # Success
                    show_snackbar("Record added successfully!")
                    # Clear fields
                    item_name_field.value = ""
                    category_field.value = None
                    quantity_field.value = ""
                    unit_field.value = None
                    storage_field.value = None
                    expiry_date_field.value = ""
                    # Switch to records tab
                    nav_bar.selected_index = 0
                    records_view_container.visible = True
                    add_view_container.visible = False
                    load_table()
            else:
                show_snackbar("Failed to add record", is_error=True)
        except requests.exceptions.RequestException as e:
            show_snackbar(f"API error: {str(e)}", is_error=True)

    submit_btn = ft.Button(
        "Submit Record",
        icon=ft.Icons.ADD,
        on_click=on_submit_click,
        style=ft.ButtonStyle(
            bgcolor=colors["ORANGE"],
            color="#FFFFFF",
            elevation=0,
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.Padding.symmetric(horizontal=20, vertical=12),
        ),
    )

    add_form = ft.Container(
        padding=ft.Padding.only(left=32, right=32, top=24, bottom=24),
        content=ft.Column(
            spacing=16,
            controls=[
                item_name_field,
                category_field,
                quantity_field,
                unit_field,
                storage_field,
                expiry_date_field,
                submit_btn,
            ],
        ),
    )

    add_view = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=0,
        controls=[
            add_header,
            add_form,
            ft.Container(expand=True),
        ],
    )

    # Records and Add View Containers
    records_view_container = ft.Container(
        expand=True,
        visible=True,
        content=records_view,
    )

    add_view_container = ft.Container(
        expand=True,
        visible=False,
        content=add_view,
    )

    # Navigation Bar
    def on_nav_change(e):
        records_view_container.visible = e.control.selected_index == 0
        add_view_container.visible = e.control.selected_index == 1
        if e.control.selected_index == 0:
            load_table()
        page.update()

    nav_bar = ft.NavigationBar(
        on_change=on_nav_change,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.LIST_ALT, label="Inventory Records"),
            ft.NavigationBarDestination(icon=ft.Icons.ADD_BOX, label="Add New Item"),
        ],
    )

    # Content Area
    content_area = ft.Container(
        expand=True,
        bgcolor=colors["BG"],
        content=ft.Column(
            expand=True,
            spacing=0,
            controls=[
                top_bar,
                ft.Row(
                    expand=True,
                    spacing=0,
                    controls=[
                        records_view_container,
                        add_view_container,
                    ],
                ),
                nav_bar,
            ],
        ),
    )

    # Layout Assembly
    layout = ft.Row(
        expand=True,
        spacing=0,
        controls=[sidebar, content_area],
    )

    # Load initial data
    load_table()

    return ft.View(
        route="/api-records",
        padding=0,
        spacing=0,
        bgcolor=colors["BG"],
        controls=[layout],
    )
