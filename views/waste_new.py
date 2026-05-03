import flet as ft
import sqlite3
from datetime import datetime

DB_PATH = "inventory.db"

# Color dicts copied from views/inventory.py
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


def _init_waste_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS waste_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            qty_wasted REAL NOT NULL,
            unit TEXT NOT NULL,
            reason TEXT NOT NULL,
            waste_date TEXT NOT NULL,
            notes TEXT,
            cost_estimate REAL
        )
        """
    )
    conn.commit()
    conn.close()


def _get_inventory_items():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, item_name, unit FROM inventory ORDER BY item_name")
    rows = cur.fetchall()
    conn.close()
    # return list of dicts
    return [dict(r) for r in rows]


def waste_new_view(page: ft.Page) -> ft.View:
    _init_waste_db()
    colors = LIGHT.copy() if page.theme_mode == ft.ThemeMode.LIGHT else DARK.copy()
    role = page.session.store.get("role") or "chef"
    prefill_item_id = page.session.store.get("waste_item_id")

    def get_role_label(r):
        """Map role string to display label."""
        role_map = {"chef": "Kitchen Staff", "inventory_staff": "Inventory Manager", "manager": "General Manager"}
        return role_map.get(r, "Kitchen Staff")

    inventory_items = _get_inventory_items()

    # State fields
    f_item = ft.Dropdown(width=400, height=44)
    f_unit = ft.Dropdown(value="pcs", width=140, height=44)
    f_qty = ft.TextField(hint_text="0", keyboard_type=ft.KeyboardType.NUMBER, width=240, height=44)
    f_date = ft.TextField(value=datetime.now().strftime("%Y-%m-%d"), width=200, height=44)
    f_reason = ft.Dropdown(width=300, height=44)
    f_cost = ft.TextField(hint_text="Enter price per amount", value="0.00", width=200, height=44, keyboard_type=ft.KeyboardType.NUMBER)
    f_notes = ft.TextField(multiline=True, min_lines=3, max_lines=6)

    t_loss = ft.Text("$0.00", size=22, weight=ft.FontWeight.W_700, color=colors["MUTED"])
    t_unit_price = ft.Text("$0.00", size=13, color=colors["MUTED"])
    t_item_name = ft.Text("—", size=13, color=colors["MUTED"])
    t_qty_display = ft.Text("—", size=13, color=colors["MUTED"])
    t_reason_display = ft.Text("—", size=13, color=colors["MUTED"])

    err_text = ft.Text("", color=colors["RED"], visible=False)

    # populate dropdowns
    f_item.options = [ft.DropdownOption(key=str(it["id"]), text=it["item_name"]) for it in inventory_items]
    units = ["g", "kg", "L", "mL", "pcs", "oz", "lb"]
    f_unit.options = [ft.DropdownOption(key=u, text=u) for u in units]
    f_reason.options = [ft.DropdownOption(key=r, text=r) for r in ["Expired", "Spoiled", "Prep Waste", "Overproduction", "Damaged", "Other"]]

    def card_shadow():
        return ft.BoxShadow(blur_radius=12, spread_radius=0, color=colors["SHADOW"], offset=ft.Offset(0, 2))

    def _recalc():
        try:
            unit_price = float(f_cost.value or 0)
        except Exception:
            unit_price = 0.0
        try:
            qty = float(f_qty.value or 0)
        except Exception:
            qty = 0.0
        total_cost = unit_price * qty
        t_loss.value = f"${total_cost:.2f}"
        t_unit_price.value = f"${unit_price:.2f} per amount" if unit_price > 0 else "$0.00 per amount"
        t_loss.color = colors["ORANGE"] if total_cost > 0 else colors["MUTED"]
        unit_val = f_unit.value or ""
        t_qty_display.value = f"{qty} {unit_val}" if qty > 0 else "—"
        t_reason_display.value = f_reason.value or "—"

    if prefill_item_id is not None:
        selected = next((i for i in inventory_items if str(i["id"]) == str(prefill_item_id)), None)
        if selected:
            f_item.value = str(selected["id"])
            f_unit.value = selected.get("unit") or f_unit.value
            t_item_name.value = selected.get("item_name") or "—"
            _recalc()
        page.session.store.remove("waste_item_id")

    def on_item_change(e):
        sel = f_item.value
        if not sel:
            t_item_name.value = "—"
            page.update()
            return
        found = next((i for i in inventory_items if str(i["id"]) == str(sel)), None)
        if found:
            f_unit.value = found.get("unit") or f_unit.value
            t_item_name.value = found.get("item_name")
        _recalc()
        page.update()

    def on_qty_change(e):
        _recalc()
        page.update()

    def on_reason_change(e):
        t_reason_display.value = f_reason.value or "—"
        page.update()

    def on_cancel(e):
        if page.session.store.contains_key("waste_item_id"):
            page.session.store.remove("waste_item_id")
        page.go("/inventory")

    def on_save(e):
        # validation
        err_text.visible = False
        if not f_item.value:
            err_text.value = "Select an item to record waste against."
            err_text.visible = True
            page.update()
            return
        try:
            qty = float(f_qty.value or 0)
        except Exception:
            err_text.value = "Enter a valid quantity."
            err_text.visible = True
            page.update()
            return
        if qty <= 0:
            err_text.value = "Quantity must be greater than zero."
            err_text.visible = True
            page.update()
            return
        if not f_reason.value:
            err_text.value = "Select a reason for the waste."
            err_text.visible = True
            page.update()
            return

        item_id = int(f_item.value)
        unit = f_unit.value or "pcs"
        reason = f_reason.value
        waste_date = f_date.value or datetime.now().strftime("%Y-%m-%d")
        notes = f_notes.value or ""
        try:
            unit_price = float(f_cost.value or 0)
        except Exception:
            unit_price = 0.0
        cost = round(unit_price * qty, 2)

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Check current inventory quantity
        cur.execute("SELECT quantity FROM inventory WHERE id=?", (item_id,))
        row = cur.fetchone()
        if not row:
            err_text.value = "Item not found in inventory."
            err_text.visible = True
            conn.close()
            page.update()
            return
        
        current_qty = float(row[0])
        if qty > current_qty + 1e-9:
            err_text.value = f"Cannot waste {qty} {unit}. Only {current_qty} {unit} available."
            err_text.visible = True
            conn.close()
            page.update()
            return
        
        # Insert waste log and decrement inventory in transaction
        try:
            cur.execute(
                "INSERT INTO waste_logs (item_id, qty_wasted, unit, reason, waste_date, notes, cost_estimate) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (item_id, qty, unit, reason, waste_date, notes, cost),
            )
            # Round to avoid float artifacts like 9.600000000000001 in SQLite/UI.
            new_qty = round(max(0.0, current_qty - qty), 3)
            cur.execute("UPDATE inventory SET quantity=? WHERE id=?", (new_qty, item_id))
            conn.commit()
        except Exception as ex:
            conn.rollback()
            err_text.value = f"Error saving waste: {str(ex)}"
            err_text.visible = True
            conn.close()
            page.update()
            return
        finally:
            conn.close()

        if page.session.store.contains_key("waste_item_id"):
            page.session.store.remove("waste_item_id")

        page.go("/inventory")

    # Layout pieces
    # Sidebar (simplified re-use)
    logo_icon = ft.Image(src="assets/logo.png", width=36, height=36, fit=ft.BoxFit.CONTAIN)
    logo_text = ft.Text("Kitchen Food Waste", size=15, weight=ft.FontWeight.W_700, color=colors["TEXT"]) 

    nav_items = [
        (ft.Icons.SPACE_DASHBOARD_OUTLINED, "Dashboard", "/dashboard"),
        (ft.Icons.INVENTORY_2_OUTLINED, "Inventory", "/inventory"),
        (ft.Icons.RECEIPT_LONG_OUTLINED, "Waste Logs", "/waste-logs"),
        (ft.Icons.TIMER_OUTLINED, "Expiry Monitor", "/expiry"),
        (ft.Icons.BAR_CHART, "Reports", "/reports"),
    ]

    def build_nav_item(icon, label, route=None, active=False):
        text_color = colors["ORANGE"] if active else colors["SIDEBAR_TEXT"]
        icon_color = colors["ORANGE"] if active else colors["SIDEBAR_ICON"]
        bg = colors["SIDEBAR_ACTIVE_BG"] if active else "transparent"
        row_controls = [ft.Icon(icon, size=20, color=icon_color), ft.Text(label, size=14, color=text_color, expand=True)]
        if active:
            row_controls.append(ft.Icon(ft.Icons.CHEVRON_RIGHT, size=18, color=icon_color))
        return ft.Container(padding=ft.Padding.symmetric(horizontal=14, vertical=10), bgcolor=bg, border_radius=8, content=ft.Row(spacing=12, controls=row_controls), ink=True, on_click=(lambda e: page.go(route)) if route else None)

    nav_column = ft.Column(spacing=2, controls=[build_nav_item(i, l, r, True if l=="Waste Logs" else False) for i, l, r in nav_items])

    sign_out = ft.Container(padding=ft.Padding.symmetric(horizontal=14, vertical=10), ink=True, on_click=lambda e: (page.session.store.clear(), page.go("/")), content=ft.Row(spacing=12, controls=[ft.Icon(ft.Icons.LOGOUT, size=20, color=colors["SIDEBAR_TEXT"]), ft.Text("Sign Out", size=14, color=colors["SIDEBAR_TEXT"]) ]))

    sidebar = ft.Container(width=240, bgcolor=colors["SIDEBAR_BG"], border=ft.Border(right=ft.BorderSide(1, colors["BORDER"])), padding=ft.Padding.only(top=20, bottom=12, left=12, right=12), content=ft.Column(expand=True, spacing=0, controls=[ft.Container(padding=ft.Padding.only(left=6, bottom=24), content=ft.Row(spacing=10, controls=[logo_icon, logo_text])), nav_column, ft.Container(expand=True), ft.Divider(height=1, color=colors["DIVIDER"]), sign_out]))

    # Top bar (user info only)
    username = page.session.store.get("username") or "User"
    initials = username[:2].upper()
    user_avatar = ft.Container(width=38, height=38, bgcolor=colors["AVATAR_BG"], border_radius=19, alignment=ft.Alignment(0, 0), content=ft.Text(initials, size=14, weight=ft.FontWeight.W_600, color=colors["ORANGE"]))
    top_bar = ft.Container(padding=ft.Padding.symmetric(horizontal=32, vertical=14), border=ft.Border(bottom=ft.BorderSide(1, colors["BORDER"])), bgcolor=colors["CARD_BG"], content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[ft.Text(""), ft.Row(spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[ft.Icon(ft.Icons.NOTIFICATIONS_NONE, size=22, color=colors["MUTED"]), ft.Column(spacing=0, horizontal_alignment=ft.CrossAxisAlignment.END, controls=[ft.Text(username, size=14, weight=ft.FontWeight.W_600, color=colors["TEXT"]), ft.Text(get_role_label(role), size=12, color=colors["MUTED"]) ]), user_avatar ]) ]))

    # Content header
    content_header = ft.Container(padding=ft.Padding.only(left=32, right=32, top=24, bottom=8), content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[ft.Column(spacing=4, controls=[ft.Text("Record Food Waste", size=26, weight=ft.FontWeight.W_700, color=colors["TEXT"]), ft.Text("Stock Management > Record Food Waste", size=12, color=colors["MUTED"]) ]), ft.Container() ]))

    # Left column cards
    item_card = ft.Container(margin=ft.Margin(32, 16, 32, 0), bgcolor=colors["CARD_BG"], border=ft.Border.all(1, colors["BORDER"]), border_radius=12, shadow=card_shadow(), padding=ft.Padding.all(20), content=ft.Column(spacing=12, controls=[ft.Row(spacing=10, controls=[ft.Icon(ft.Icons.INVENTORY_2, color=colors["ORANGE"]), ft.Text("Item Selection", size=16, weight=ft.FontWeight.W_600, color=colors["TEXT"]) ]), f_item, ft.Row(spacing=12, controls=[ft.Text("Unit:", size=13, color=colors["MUTED"]), f_unit, ft.Container(expand=True)]), err_text]))

    logistics_card = ft.Container(margin=ft.Margin(32, 16, 32, 0), bgcolor=colors["CARD_BG"], border=ft.Border.all(1, colors["BORDER"]), border_radius=12, shadow=card_shadow(), padding=ft.Padding.all(20), content=ft.Column(spacing=12, controls=[ft.Row(spacing=10, controls=[ft.Icon(ft.Icons.SCALE, color=colors["ORANGE"]), ft.Text("Logistics", size=16, weight=ft.FontWeight.W_600, color=colors["TEXT"]) ]), ft.Row(spacing=12, controls=[ft.Column(spacing=6, controls=[ft.Text("Quantity", size=12, color=colors["MUTED"]), f_qty]), ft.Column(spacing=6, controls=[ft.Text("Date", size=12, color=colors["MUTED"]), f_date]) ]), ft.Column(spacing=6, controls=[ft.Text("Reason", size=12, color=colors["MUTED"]), f_reason]), ft.Column(spacing=6, controls=[ft.Text("Price per Amount", size=12, color=colors["MUTED"]), f_cost]) ]))

    notes_card = ft.Container(margin=ft.Margin(32, 16, 32, 0), bgcolor=colors["CARD_BG"], border=ft.Border.all(1, colors["BORDER"]), border_radius=12, shadow=card_shadow(), padding=ft.Padding.all(20), content=ft.Column(spacing=12, controls=[ft.Row(spacing=10, controls=[ft.Icon(ft.Icons.NOTES, color=colors["ORANGE"]), ft.Text("Additional Context", size=16, weight=ft.FontWeight.W_600, color=colors["TEXT"]) ]), ft.Column(spacing=6, controls=[ft.Text("Disposal Notes", size=12, color=colors["MUTED"]), f_notes]) ]))

    left_col = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=0, controls=[item_card, logistics_card, notes_card])

    # Right panel
    impact_card = ft.Container(margin=ft.Margin(16, 16, 32, 0), width=300, bgcolor=colors["CARD_BG"], border=ft.Border.all(1, colors["BORDER"]), border_radius=12, shadow=card_shadow(), padding=ft.Padding.all(16), content=ft.Column(spacing=10, controls=[ft.Text("Waste Impact", size=16, weight=ft.FontWeight.W_600, color=colors["TEXT"]), ft.Divider(height=1, color=colors["DIVIDER"]), ft.Text("Projected Loss", size=12, color=colors["MUTED"]), t_loss, ft.Text("Price per Amount", size=12, color=colors["MUTED"]), t_unit_price, ft.Text("Item", size=12, color=colors["MUTED"]), t_item_name, ft.Text("Quantity", size=12, color=colors["MUTED"]), t_qty_display, ft.Text("Reason", size=12, color=colors["MUTED"]), t_reason_display]))

    action_bar = ft.Container(border=ft.Border(top=ft.BorderSide(1, colors["DIVIDER"])), padding=ft.Padding.symmetric(horizontal=24, vertical=12), content=ft.Row(alignment=ft.MainAxisAlignment.END, controls=[ft.TextButton("Cancel", on_click=on_cancel, style=ft.ButtonStyle(color=colors["MUTED"])), ft.Button("Save Waste Record", on_click=on_save, icon=ft.Icons.SAVE_OUTLINED, style=ft.ButtonStyle(bgcolor=colors["ORANGE"], color="#FFFFFF", elevation=0, shape=ft.RoundedRectangleBorder(radius=8), padding=ft.Padding.symmetric(horizontal=16, vertical=10))) ]))

    content_area = ft.Container(expand=True, bgcolor=colors["BG"], content=ft.Column(expand=True, spacing=0, controls=[top_bar, content_header, ft.Row(expand=True, spacing=0, controls=[ft.Container(expand=True, content=left_col), impact_card]), action_bar]))

    # Wire events
    f_item.on_change = on_item_change
    f_qty.on_change = on_qty_change
    f_cost.on_change = lambda e: (_recalc(), page.update())
    f_unit.on_change = lambda e: (_recalc(), page.update())
    f_reason.on_change = on_reason_change

    layout = ft.Row(expand=True, spacing=0, controls=[sidebar, content_area])

    return ft.View(route="/waste/new", padding=0, spacing=0, bgcolor=colors["BG"], controls=[layout])
