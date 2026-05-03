import flet as ft
import sqlite3
from datetime import datetime

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


def _get_item(item_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT id, item_name, sku, category, quantity, unit, storage, expiry_date, "
        "purchase_date, internal_notes, batch_number, alert_threshold FROM inventory WHERE id=?",
        (item_id,),
    )
    row = cur.fetchone()
    conn.close()
    return row


def _update_quantity(item_id, new_qty):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE inventory SET quantity=? WHERE id=?", (new_qty, item_id))
    conn.commit()
    conn.close()


def _get_status_info(expiry_str, colors):
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


def _get_time_remaining(expiry_str):
    today = datetime.now().date()
    try:
        exp = datetime.strptime(expiry_str, "%Y-%m-%d").date()
    except ValueError:
        return "Unknown"
    days = (exp - today).days
    if days > 1:
        return f"{days} days left"
    elif days == 1:
        return "1 day left"
    elif days == 0:
        return "Expires today"
    else:
        return f"{abs(days)} days overdue"


def item_detail_view(page: ft.Page, item_id: int) -> ft.View:
    colors = LIGHT.copy() if page.theme_mode == ft.ThemeMode.LIGHT else DARK.copy()
    role = page.session.store.get("role") or "chef"

    def get_role_label(r):
        """Map role string to display label."""
        role_map = {"chef": "Kitchen Staff", "inventory_staff": "Inventory Manager", "manager": "General Manager"}
        return role_map.get(r, "Kitchen Staff")

    item = _get_item(item_id)
    if item is None:
        page.go("/inventory")
        return ft.View(route=f"/item/{item_id}", controls=[])

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
            (ft.Icons.PEOPLE_OUTLINE, "Users & Staff", page.route == "/users", "/users"),
        ])
    nav_items_data.append((ft.Icons.SETTINGS_OUTLINED, "Settings", False, None))

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
                                ft.Text(username, size=14, weight=ft.FontWeight.W_600, color=colors["TEXT"]),
                                ft.Text(get_role_label(role), size=12, color=colors["MUTED"]),
                            ],
                        ),
                        user_avatar,
                    ],
                ),
            ],
        ),
    )

    # ───────────────────── ITEM DATA ─────────────────────

    item_name = item["item_name"]
    category = item["category"]
    storage = item["storage"]
    purchase_date = item["purchase_date"] or "—"
    quantity = item["quantity"]
    unit = item["unit"]
    expiry_date = item["expiry_date"]
    batch_number = item["batch_number"] or "—"

    qty_display = f"{int(quantity)}" if quantity == int(quantity) else f"{quantity}"
    current_qty = [quantity]  # mutable ref so dialog closure can update it
    stock_value_text = ft.Text(
        f"{qty_display} {unit}",
        size=14,
        color=colors["TEXT"],
        weight=ft.FontWeight.W_600,
    )
    status_label, status_color, status_bg = _get_status_info(expiry_date, colors)
    time_remaining = _get_time_remaining(expiry_date)

    # ───────────────────── PAGE HEADER ─────────────────────

    def on_back(e):
        page.go("/inventory")

    back_link = ft.Container(
        padding=ft.Padding.only(left=32, top=20, bottom=4),
        content=ft.TextButton(
            content=ft.Row(
                spacing=4,
                controls=[
                    ft.Icon(ft.Icons.ARROW_BACK, size=16, color=colors["ORANGE"]),
                    ft.Text("Back to Inventory", size=13, color=colors["ORANGE"]),
                ],
            ),
            on_click=on_back,
            style=ft.ButtonStyle(padding=ft.Padding.all(0)),
        ),
    )

    def on_record_waste(e):
        page.go("/waste/new")

    def show_update_stock_dialog():
        action_type = ["restock"]

        # ── toggle controls with named icon/label refs ──
        restock_icon = ft.Icon(ft.Icons.ADD, size=16, color=colors["ORANGE"])
        restock_label = ft.Text("Restock (Add)", size=13, color=colors["ORANGE"], weight=ft.FontWeight.W_600)
        restock_btn = ft.Container(
            expand=True,
            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            border_radius=8,
            border=ft.Border.all(2, colors["ORANGE"]),
            bgcolor=colors["ORANGE_BG"],
            ink=True,
            content=ft.Row(
                spacing=6,
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[restock_icon, restock_label],
            ),
        )

        withdraw_icon = ft.Icon(ft.Icons.REMOVE, size=16, color=colors["MUTED"])
        withdraw_label = ft.Text("Withdraw (Subtract)", size=13, color=colors["MUTED"], weight=ft.FontWeight.W_400)
        withdraw_btn = ft.Container(
            expand=True,
            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            border_radius=8,
            border=ft.Border.all(1, colors["BORDER"]),
            bgcolor="transparent",
            ink=True,
            content=ft.Row(
                spacing=6,
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[withdraw_icon, withdraw_label],
            ),
        )

        amount_field = ft.TextField(
            value="",
            hint_text="0",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=8,
            border_color=colors["BORDER"],
            focused_border_color=colors["ORANGE"],
            bgcolor=colors["CARD_BG"],
            color=colors["TEXT"],
            cursor_color=colors["ORANGE"],
            text_size=14,
            suffix=ft.Text(unit, color=colors["MUTED"], size=13),
            content_padding=ft.Padding.symmetric(horizontal=14, vertical=12),
            expand=True,
        )

        projected_text = ft.Text(
            f"{qty_display} {unit}",
            size=16,
            weight=ft.FontWeight.W_700,
            color=colors["ORANGE"],
        )

        note_field = ft.TextField(
            hint_text="e.g., Weekly delivery received, Correction after cycle count...",
            multiline=True,
            min_lines=3,
            max_lines=4,
            border_radius=8,
            border_color=colors["BORDER"],
            focused_border_color=colors["ORANGE"],
            bgcolor=colors["CARD_BG"],
            color=colors["TEXT"],
            cursor_color=colors["ORANGE"],
            text_size=13,
            content_padding=ft.Padding.symmetric(horizontal=14, vertical=12),
        )

        def recompute_projected(e=None):
            try:
                amt = float(amount_field.value or 0)
            except ValueError:
                amt = 0.0
            if action_type[0] == "restock":
                new_qty = current_qty[0] + amt
            else:
                new_qty = max(0.0, current_qty[0] - amt)
            disp = f"{int(new_qty)}" if new_qty == int(new_qty) else f"{new_qty:.2f}"
            projected_text.value = f"{disp} {unit}"
            page.update()

        amount_field.on_change = recompute_projected

        def set_action(action):
            action_type[0] = action
            if action == "restock":
                restock_btn.border = ft.Border.all(2, colors["ORANGE"])
                restock_btn.bgcolor = colors["ORANGE_BG"]
                restock_icon.color = colors["ORANGE"]
                restock_label.color = colors["ORANGE"]
                restock_label.weight = ft.FontWeight.W_600
                withdraw_btn.border = ft.Border.all(1, colors["BORDER"])
                withdraw_btn.bgcolor = "transparent"
                withdraw_icon.color = colors["MUTED"]
                withdraw_label.color = colors["MUTED"]
                withdraw_label.weight = ft.FontWeight.W_400
            else:
                withdraw_btn.border = ft.Border.all(2, colors["ORANGE"])
                withdraw_btn.bgcolor = colors["ORANGE_BG"]
                withdraw_icon.color = colors["ORANGE"]
                withdraw_label.color = colors["ORANGE"]
                withdraw_label.weight = ft.FontWeight.W_600
                restock_btn.border = ft.Border.all(1, colors["BORDER"])
                restock_btn.bgcolor = "transparent"
                restock_icon.color = colors["MUTED"]
                restock_label.color = colors["MUTED"]
                restock_label.weight = ft.FontWeight.W_400
            recompute_projected()

        restock_btn.on_click = lambda e: set_action("restock")
        withdraw_btn.on_click = lambda e: set_action("withdraw")

        def on_cancel(e):
            page.pop_dialog()

        def on_save(e):
            try:
                amt = float(amount_field.value or 0)
            except ValueError:
                amt = 0.0
            if amt <= 0:
                amount_field.error_text = "Enter a positive amount"
                page.update()
                return
            amount_field.error_text = None
            if action_type[0] == "restock":
                new_qty = current_qty[0] + amt
            else:
                new_qty = max(0.0, current_qty[0] - amt)
            _update_quantity(item_id, new_qty)
            current_qty[0] = new_qty
            disp = f"{int(new_qty)}" if new_qty == int(new_qty) else f"{new_qty:.2f}"
            stock_value_text.value = f"{disp} {unit}"
            page.pop_dialog()
            page.update()

        qty_disp = f"{int(current_qty[0])}" if current_qty[0] == int(current_qty[0]) else f"{current_qty[0]:.2f}"

        info_row = ft.Container(
            padding=ft.Padding.all(16),
            bgcolor=colors["TABLE_HEADER_BG"],
            border_radius=8,
            border=ft.Border.all(1, colors["BORDER"]),
            content=ft.Row(
                controls=[
                    ft.Column(
                        spacing=4,
                        expand=True,
                        controls=[
                            ft.Text("CURRENT INVENTORY", size=11, color=colors["MUTED"], weight=ft.FontWeight.W_600),
                            ft.Text(f"{qty_disp} {unit}", size=22, color=colors["TEXT"], weight=ft.FontWeight.W_700),
                        ],
                    ),
                    ft.Container(width=1, height=40, bgcolor=colors["DIVIDER"], margin=ft.Margin(12, 0, 12, 0)),
                    ft.Column(
                        spacing=4,
                        expand=True,
                        controls=[
                            ft.Text("STORAGE", size=11, color=colors["MUTED"], weight=ft.FontWeight.W_600),
                            ft.Text(storage, size=14, color=colors["TEXT"], weight=ft.FontWeight.W_500),
                        ],
                    ),
                ],
            ),
        )

        def section_label(text):
            return ft.Text(text, size=11, color=colors["MUTED"], weight=ft.FontWeight.W_600)

        dialog_body = ft.Column(
            spacing=16,
            controls=[
                info_row,
                ft.Column(
                    spacing=8,
                    controls=[
                        section_label("ACTION TYPE"),
                        ft.Row(spacing=10, controls=[restock_btn, withdraw_btn]),
                    ],
                ),
                ft.Column(
                    spacing=8,
                    controls=[
                        section_label(f"ADJUSTMENT AMOUNT ({unit.upper()})"),
                        ft.Row(controls=[amount_field]),
                    ],
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                    bgcolor=colors["ORANGE_BG"],
                    border_radius=8,
                    border=ft.Border.all(1, colors["BORDER"]),
                    content=ft.Row(
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.ARROW_FORWARD, size=18, color=colors["ORANGE"]),
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text("Projected New Total", size=11, color=colors["ORANGE"], weight=ft.FontWeight.W_500),
                                    projected_text,
                                ],
                            ),
                        ],
                    ),
                ),
                ft.Column(
                    spacing=8,
                    controls=[
                        section_label("ADJUSTMENT NOTE (OPTIONAL)"),
                        note_field,
                    ],
                ),
            ],
        )

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                spacing=10,
                controls=[
                    ft.Icon(ft.Icons.INVENTORY_2_OUTLINED, color=colors["ORANGE"], size=22),
                    ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text("Update Stock", size=18, weight=ft.FontWeight.W_600, color=colors["TEXT"]),
                            ft.Text(
                                f"Adjusting inventory levels for {item_name}",
                                size=12,
                                color=colors["MUTED"],
                            ),
                        ],
                    ),
                ],
            ),
            content=ft.Container(width=440, content=dialog_body),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=on_cancel,
                    style=ft.ButtonStyle(color=colors["MUTED"]),
                ),
                ft.Button(
                    "Save Changes",
                    icon=ft.Icons.SAVE_OUTLINED,
                    on_click=on_save,
                    style=ft.ButtonStyle(
                        bgcolor=colors["ORANGE"],
                        color="#FFFFFF",
                        elevation=0,
                        shape=ft.RoundedRectangleBorder(radius=8),
                        padding=ft.Padding.symmetric(horizontal=20, vertical=10),
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=colors["CARD_BG"],
            shape=ft.RoundedRectangleBorder(radius=12),
        )
        page.show_dialog(dlg)

    def on_update_stock(e):
        show_update_stock_dialog()

    page_header = ft.Container(
        padding=ft.Padding.only(left=32, right=32, top=4, bottom=12),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(item_name, size=26, weight=ft.FontWeight.W_700, color=colors["TEXT"]),
                ft.Row(
                    spacing=12,
                    controls=[
                        ft.OutlinedButton(
                            content=ft.Row(
                                spacing=6,
                                controls=[
                                    ft.Icon(ft.Icons.DELETE_OUTLINE, size=16, color=colors["TEXT_SECONDARY"]),
                                    ft.Text("Record Waste", size=13, color=colors["TEXT_SECONDARY"]),
                                ],
                            ),
                            on_click=on_record_waste,
                            style=ft.ButtonStyle(
                                side=ft.BorderSide(1, colors["BORDER"]),
                                shape=ft.RoundedRectangleBorder(radius=8),
                                padding=ft.Padding.symmetric(horizontal=16, vertical=10),
                            ),
                        ),
                        ft.Button(
                            content=ft.Row(
                                spacing=6,
                                controls=[
                                    ft.Icon(ft.Icons.SYNC, size=16, color="#FFFFFF"),
                                    ft.Text("Update Stock", size=13, color="#FFFFFF"),
                                ],
                            ),
                            on_click=on_update_stock,
                            style=ft.ButtonStyle(
                                bgcolor=colors["ORANGE"],
                                color="#FFFFFF",
                                elevation=0,
                                shape=ft.RoundedRectangleBorder(radius=8),
                                padding=ft.Padding.symmetric(horizontal=16, vertical=10),
                            ),
                        ),
                    ],
                ),
            ],
        ),
    )

    # ───────────────────── SUMMARY CARD ─────────────────────

    def build_meta_cell(label, value, icon=None):
        controls = []
        if icon:
            controls.append(ft.Icon(icon, size=14, color=colors["MUTED"]))
        controls.append(
            ft.Column(
                spacing=2,
                controls=[
                    ft.Text(label, size=11, color=colors["MUTED"], weight=ft.FontWeight.W_500),
                    ft.Text(value, size=14, color=colors["TEXT"], weight=ft.FontWeight.W_600),
                ],
            )
        )
        return ft.Container(
            expand=True,
            content=ft.Row(spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=controls),
        )

    item_icon_box = ft.Container(
        width=64,
        height=64,
        bgcolor=colors["ORANGE_BG"],
        border_radius=12,
        alignment=ft.Alignment(0, 0),
        content=ft.Icon(ft.Icons.RESTAURANT, size=28, color=colors["ORANGE"]),
        margin=ft.Margin(0, 0, 12, 0),
    )

    status_pill = ft.Container(
        padding=ft.Padding.symmetric(horizontal=14, vertical=6),
        bgcolor=status_bg,
        border_radius=6,
        content=ft.Text(status_label, size=12, color=status_color, weight=ft.FontWeight.W_700),
    )

    status_cell = ft.Container(
        expand=True,
        content=ft.Column(
            spacing=2,
            controls=[
                ft.Text("STATUS", size=11, color=colors["MUTED"], weight=ft.FontWeight.W_500),
                status_pill,
            ],
        ),
    )

    summary_card = ft.Container(
        margin=ft.Margin(32, 0, 32, 0),
        bgcolor=colors["CARD_BG"],
        border=ft.Border.all(1, colors["BORDER"]),
        border_radius=12,
        shadow=card_shadow(),
        padding=ft.Padding.all(24),
        content=ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                item_icon_box,
                ft.Container(width=1, height=60, bgcolor=colors["DIVIDER"], margin=ft.Margin(0, 0, 24, 0)),
                build_meta_cell("Category", category),
                ft.Container(width=1, height=40, bgcolor=colors["DIVIDER"]),
                build_meta_cell("Storage", storage),
                ft.Container(width=1, height=40, bgcolor=colors["DIVIDER"]),
                build_meta_cell("Purchase Date", purchase_date),
                ft.Container(width=1, height=40, bgcolor=colors["DIVIDER"]),
                ft.Container(
                    expand=True,
                    content=ft.Row(
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text("Current Stock", size=11, color=colors["MUTED"], weight=ft.FontWeight.W_500),
                                    stock_value_text,
                                ],
                            ),
                        ],
                    ),
                ),
                ft.Container(width=1, height=40, bgcolor=colors["DIVIDER"]),
                status_cell,
            ],
        ),
    )

    # ───────────────────── TABS ─────────────────────

    TAB_LABELS = ["Expiry Batches", "Waste History", "Activity Timeline"]
    selected_tab = [0]

    tab_body_col = ft.Column(spacing=0)

    def build_expiry_batches_tab():
        header = ft.Container(
            bgcolor=colors["TABLE_HEADER_BG"],
            padding=ft.Padding.symmetric(horizontal=20, vertical=12),
            border=ft.Border(bottom=ft.BorderSide(1, colors["DIVIDER"])),
            content=ft.Row(
                spacing=8,
                controls=[
                    ft.Container(expand=20, content=ft.Text("Batch Number", size=12, color=colors["MUTED"], weight=ft.FontWeight.W_600)),
                    ft.Container(expand=15, content=ft.Text("Expiry Date", size=12, color=colors["MUTED"], weight=ft.FontWeight.W_600)),
                    ft.Container(expand=15, content=ft.Text("Time Remaining", size=12, color=colors["MUTED"], weight=ft.FontWeight.W_600)),
                    ft.Container(expand=15, content=ft.Text("Status", size=12, color=colors["MUTED"], weight=ft.FontWeight.W_600)),
                    ft.Container(expand=3, content=ft.Text("Actions", size=12, color=colors["MUTED"], weight=ft.FontWeight.W_600)),
                ],
            ),
        )

        # Time remaining text color: orange/red if expiring/expired, normal if fresh
        time_color = colors["TEXT_SECONDARY"]
        if status_label == "Expired":
            time_color = colors["RED"]
        elif status_label == "Expiring Soon":
            time_color = colors["ORANGE"]

        batch_row = ft.Container(
            padding=ft.Padding.symmetric(horizontal=20, vertical=14),
            border=ft.Border(bottom=ft.BorderSide(1, colors["DIVIDER"])),
            content=ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        expand=20,
                        content=ft.Text(batch_number, size=13, color=colors["TEXT"], weight=ft.FontWeight.W_500),
                    ),
                    ft.Container(
                        expand=15,
                        content=ft.Text(expiry_date, size=13, color=colors["TEXT_SECONDARY"]),
                    ),
                    ft.Container(
                        expand=15,
                        content=ft.Text(time_remaining, size=13, color=time_color, weight=ft.FontWeight.W_500),
                    ),
                    ft.Container(
                        expand=15,
                        content=ft.Container(
                            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                            bgcolor=status_bg,
                            border_radius=4,
                            width=110,
                            alignment=ft.Alignment(0, 0),
                            content=ft.Text(status_label, size=11, color=status_color, weight=ft.FontWeight.W_600),
                        ),
                    ),
                    ft.Container(
                        expand=3,
                        content=ft.PopupMenuButton(
                            icon=ft.Icons.MORE_VERT,
                            icon_size=18,
                            icon_color=colors["MUTED"],
                                    items=[
                                ft.PopupMenuItem(
                                    content=ft.Text("Mark as Used"),
                                    icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                                ),
                                ft.PopupMenuItem(
                                    content=ft.Text("Record Waste"),
                                    icon=ft.Icons.DELETE_OUTLINE,
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        )

        return ft.Column(spacing=0, controls=[header, batch_row])

    def build_empty_state(message):
        return ft.Container(
            padding=ft.Padding.symmetric(vertical=48),
            alignment=ft.Alignment(0, 0),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
                controls=[
                    ft.Icon(ft.Icons.INBOX_OUTLINED, size=40, color=colors["MUTED"]),
                    ft.Text(message, size=14, color=colors["MUTED"]),
                ],
            ),
        )

    def get_tab_content(idx):
        if idx == 0:
            return build_expiry_batches_tab()
        elif idx == 1:
            return build_empty_state("No waste history yet")
        else:
            return build_empty_state("No activity recorded yet")

    tab_headers_row = ft.Row(spacing=0)
    tab_content_wrapper = ft.Container(content=get_tab_content(0))

    def build_tab_headers():
        controls = []
        for idx, label in enumerate(TAB_LABELS):
            is_active = idx == selected_tab[0]
            controls.append(
                ft.Container(
                    padding=ft.Padding.only(left=20, right=20, top=14, bottom=10),
                    border=ft.Border(
                        bottom=ft.BorderSide(2, colors["ORANGE"] if is_active else "transparent")
                    ),
                    ink=True,
                    on_click=lambda e, i=idx: switch_tab(i),
                    content=ft.Text(
                        label,
                        size=14,
                        color=colors["ORANGE"] if is_active else colors["MUTED"],
                        weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.W_400,
                    ),
                )
            )
        tab_headers_row.controls = controls

    def switch_tab(idx):
        selected_tab[0] = idx
        build_tab_headers()
        tab_content_wrapper.content = get_tab_content(idx)
        page.update()

    build_tab_headers()

    tabs_card = ft.Container(
        margin=ft.Margin(32, 16, 32, 0),
        bgcolor=colors["CARD_BG"],
        border=ft.Border.all(1, colors["BORDER"]),
        border_radius=12,
        shadow=card_shadow(),
        content=ft.Column(
            spacing=0,
            controls=[
                ft.Container(
                    border=ft.Border(bottom=ft.BorderSide(1, colors["DIVIDER"])),
                    content=tab_headers_row,
                ),
                tab_content_wrapper,
            ],
        ),
    )

    # ───────────────────── BOTTOM INFO CARDS ─────────────────────

    def build_info_card(title, title_icon, body_controls):
        return ft.Container(
            expand=True,
            bgcolor=colors["CARD_BG"],
            border=ft.Border.all(1, colors["BORDER"]),
            border_radius=12,
            shadow=card_shadow(),
            padding=ft.Padding.all(20),
            content=ft.Column(
                spacing=12,
                controls=[
                    ft.Row(
                        spacing=8,
                        controls=[
                            ft.Icon(title_icon, size=16, color=colors["MUTED"]),
                            ft.Text(title, size=14, weight=ft.FontWeight.W_600, color=colors["TEXT"]),
                        ],
                    ),
                    ft.Divider(height=1, color=colors["DIVIDER"]),
                    *body_controls,
                ],
            ),
        )

    staff_avatar = ft.Container(
        width=40,
        height=40,
        bgcolor=colors["ORANGE_BG"],
        border_radius=20,
        alignment=ft.Alignment(0, 0),
        content=ft.Icon(ft.Icons.PERSON_OUTLINE, size=20, color=colors["ORANGE"]),
    )

    last_handled_card = build_info_card(
        "Last Handled By",
        ft.Icons.PERSON_OUTLINE,
        [
            ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    staff_avatar,
                    ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text("Kitchen Staff", size=14, weight=ft.FontWeight.W_600, color=colors["TEXT"]),
                            ft.Text("Inventory Specialist • Shift A", size=12, color=colors["MUTED"]),
                        ],
                    ),
                ],
            ),
        ],
    )

    supplier_card = build_info_card(
        "Supplier Info",
        ft.Icons.OPEN_IN_NEW,
        [
            ft.Text("Local Supplier", size=14, weight=ft.FontWeight.W_600, color=colors["TEXT"]),
            ft.Text("ID: N/A  •  Lead Time: N/A", size=12, color=colors["MUTED"]),
            ft.TextButton(
                "View Contract",
                style=ft.ButtonStyle(
                    color=colors["ORANGE"],
                    padding=ft.Padding.all(0),
                ),
            ),
        ],
    )

    usage_card = build_info_card(
        "Usage Policy",
        ft.Icons.WARNING_AMBER_OUTLINED,
        [
            ft.Text(
                "Store according to food safety guidelines. "
                "Check expiry date before use. "
                "Mark as used immediately in the tracker.",
                size=13,
                color=colors["TEXT_SECONDARY"],
            ),
        ],
    )

    info_cards_row = ft.Container(
        margin=ft.Margin(32, 16, 32, 16),
        content=ft.Row(spacing=16, controls=[last_handled_card, supplier_card, usage_card]),
    )

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

    # ───────────────────── LAYOUT ASSEMBLY ─────────────────────

    scrollable_content = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=0,
        controls=[
            back_link,
            page_header,
            summary_card,
            tabs_card,
            info_cards_row,
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
        route=f"/item/{item_id}",
        padding=0,
        spacing=0,
        bgcolor=colors["BG"],
        controls=[layout],
    )
