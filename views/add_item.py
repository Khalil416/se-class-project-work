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
    "DIVIDER": "#F0F0F0",
    "SHADOW": "#08000000",
    "AVATAR_BG": "#FFE0B2",
    "SEARCH_BG": "#F5F5F5",
    "SEARCH_BORDER": "#EEEEEE",
    "GREEN": "#16A34A",
    "GREEN_BG": "#ECFDF5",
    "RED": "#DC2626",
    "ORANGE_BG": "#FFF7ED",
}

DARK = {
    "ORANGE": "#E68A17",
    "BG": "#0F0F0F",
    "CARD_BG": "#1A1A1A",
    "TEXT": "#F0F0F0",
    "TEXT_SECONDARY": "#CCCCCC",
    "MUTED": "#999999",
    "BORDER": "#2C2C2C",
    "DIVIDER": "#252525",
    "SHADOW": "#30000000",
    "AVATAR_BG": "#5D4037",
    "SEARCH_BG": "#222222",
    "SEARCH_BORDER": "#333333",
    "GREEN": "#22C55E",
    "GREEN_BG": "#14532D",
    "RED": "#EF4444",
    "ORANGE_BG": "#3D2810",
}

CATEGORIES = [
    "Dairy & Eggs", "Meat", "Produce", "Bakery", "Pantry", "Seafood",
    "Beverages", "Frozen", "Condiments", "Grains", "Snacks", "Spices",
]
STORAGES = [
    "Walk-in Cooler 1", "Walk-in Fridge", "Freezer A", "Freezer B",
    "Dry Storage", "Pantry Shelf", "Cold Room", "Fridge A",
]
UNITS = [
    "Kilograms (kg)", "Liters (L)", "Pieces (pcs)", "Bags (bags)",
    "Loaves (loaves)", "Cups (cups)", "Bottles (bottles)",
]
UNIT_MAP = {
    "Kilograms (kg)": "kg",
    "Liters (L)": "L",
    "Pieces (pcs)": "pcs",
    "Bags (bags)": "bags",
    "Loaves (loaves)": "loaves",
    "Cups (cups)": "cups",
    "Bottles (bottles)": "bottles",
}
UNIT_REVERSE = {v: k for k, v in UNIT_MAP.items()}
# Map display categories back to DB short names
CAT_MAP = {
    "Dairy & Eggs": "Dairy",
    "Meat": "Meat",
    "Produce": "Produce",
    "Bakery": "Bakery",
    "Pantry": "Pantry",
    "Seafood": "Seafood",
    "Beverages": "Beverages",
    "Frozen": "Frozen",
    "Condiments": "Condiments",
    "Grains": "Grains",
    "Snacks": "Snacks",
    "Spices": "Spices",
}
CAT_REVERSE = {v: k for k, v in CAT_MAP.items()}
STORAGE_MAP = {s: s for s in STORAGES}


def _get_categories_from_db():
    """Fetch category list from categories table in DB, fallback to CATEGORIES if empty."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT category_name FROM categories ORDER BY category_name ASC")
        rows = cur.fetchall()
        conn.close()
        if rows:
            return [r[0] for r in rows]
    except Exception:
        pass
    return CATEGORIES


def _ensure_columns():
    """Add new columns if they don't exist yet (migration-safe)."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
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


def _add_item(item_name, category, storage, quantity, unit, purchase_date,
              internal_notes, batch_number, expiry_date, alert_threshold):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Auto-generate SKU
    cur.execute("SELECT MAX(id) FROM inventory")
    next_id = (cur.fetchone()[0] or 0) + 1
    sku = f"SKU-{next_id:05d}"
    try:
        cur.execute(
            """INSERT INTO inventory
               (item_name, sku, category, quantity, unit, storage, expiry_date,
                purchase_date, internal_notes, batch_number, alert_threshold)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (item_name, sku, category, float(quantity), unit, storage,
             expiry_date, purchase_date, internal_notes, batch_number, int(alert_threshold)),
        )
        conn.commit()
        return None
    except sqlite3.IntegrityError:
        return "Item could not be saved (duplicate SKU)."
    finally:
        conn.close()


def _update_item(item_id, item_name, category, storage, quantity, unit,
                 purchase_date, internal_notes, batch_number, expiry_date, alert_threshold):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute(
            """UPDATE inventory
               SET item_name=?, category=?, quantity=?, unit=?, storage=?,
                   expiry_date=?, purchase_date=?, internal_notes=?,
                   batch_number=?, alert_threshold=?
               WHERE id=?""",
            (item_name, category, float(quantity), unit, storage,
             expiry_date, purchase_date, internal_notes, batch_number,
             int(alert_threshold), item_id),
        )
        conn.commit()
        return None
    except Exception as ex:
        return str(ex)
    finally:
        conn.close()


def _get_item(item_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM inventory WHERE id=?", (item_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def add_item_view(page: ft.Page) -> ft.View:
    _ensure_columns()
    colors = LIGHT.copy() if page.theme_mode == ft.ThemeMode.LIGHT else DARK.copy()
    role = page.session.store.get("role") or "chef"

    def get_role_label(r):
        """Map role string to display label."""
        role_map = {"chef": "Kitchen Staff", "inventory_staff": "Inventory Manager", "manager": "General Manager"}
        return role_map.get(r, "Kitchen Staff")

    # Determine if editing
    edit_id = page.session.store.get("edit_item_id")
    editing = edit_id is not None
    prefill = {}
    if editing:
        prefill = _get_item(edit_id) or {}

    page_title = "Edit Food Item" if editing else "Add New Food Item"
    page_subtitle = (
        "Update the product details below."
        if editing
        else "Populate the fields below to register a new ingredient or product in the kitchen inventory."
    )

    def card_shadow():
        return ft.BoxShadow(
            blur_radius=12, spread_radius=0,
            color=colors["SHADOW"], offset=ft.Offset(0, 2),
        )

    # ───────────────────── TOP BAR ─────────────────────
    username = page.session.store.get("username") or "Chef Julian"
    initials = username[:2].upper()

    user_avatar = ft.Container(
        width=38, height=38,
        bgcolor=colors["AVATAR_BG"], border_radius=19,
        alignment=ft.Alignment(0, 0),
        content=ft.Text(initials, size=14, weight=ft.FontWeight.W_600, color=colors["ORANGE"]),
    )

    top_bar = ft.Container(
        padding=ft.Padding.symmetric(horizontal=32, vertical=14),
        border=ft.Border(bottom=ft.BorderSide(1, colors["BORDER"])),
        bgcolor=colors["CARD_BG"],
        content=ft.Row(
            alignment=ft.MainAxisAlignment.END,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
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

    # ───────────────────── BACK LINK + HEADER ─────────────────────

    def go_back(e):
        if editing and page.session.store.contains_key("edit_item_id"):
            page.session.store.remove("edit_item_id")
        page.go("/inventory")

    back_link = ft.Container(
        padding=ft.Padding.only(left=60, top=20, bottom=4),
        content=ft.Row(
            spacing=4,
            controls=[
                ft.Icon(ft.Icons.CHEVRON_LEFT, size=18, color=colors["ORANGE"]),
                ft.Text(
                    "Back to Inventory", size=14,
                    color=colors["ORANGE"], weight=ft.FontWeight.W_500,
                ),
            ],
        ),
        ink=True,
        on_click=go_back,
    )

    header = ft.Container(
        padding=ft.Padding.only(left=60, right=60, bottom=20),
        content=ft.Column(
            spacing=6,
            controls=[
                ft.Text(page_title, size=26, weight=ft.FontWeight.W_700, color=colors["TEXT"]),
                ft.Text(page_subtitle, size=14, color=colors["MUTED"]),
            ],
        ),
    )

    # ───────────────────── SECTION BUILDER ─────────────────────

    def section_header(icon, icon_bg, title, subtitle):
        return ft.Container(
            padding=ft.Padding.only(bottom=16),
            content=ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=38, height=38,
                        bgcolor=icon_bg, border_radius=19,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Icon(icon, size=18, color=colors["ORANGE"]),
                    ),
                    ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text(title, size=16, weight=ft.FontWeight.W_700, color=colors["TEXT"]),
                            ft.Text(subtitle, size=13, color=colors["MUTED"]),
                        ],
                    ),
                ],
            ),
        )

    def field_label(text, required=False):
        parts = [ft.Text(text, size=13, weight=ft.FontWeight.W_500, color=colors["TEXT"])]
        if required:
            parts.append(ft.Text("*", size=13, color=colors["RED"]))
        return ft.Row(spacing=2, controls=parts)

    def helper_text(text):
        return ft.Text(text, size=11, color=colors["MUTED"], italic=True)

    # ───────────────────── FORM FIELDS ─────────────────────

    # Basic Details
    f_item_name = ft.TextField(
        value=prefill.get("item_name", ""),
        hint_text="e.g. Organic Whole Milk",
        border_radius=8, border_color=colors["BORDER"],
        focused_border_color=colors["ORANGE"], cursor_color=colors["ORANGE"],
        text_size=14, color=colors["TEXT"], bgcolor=colors["CARD_BG"],
        content_padding=ft.Padding.symmetric(horizontal=14, vertical=12),
    )

    cat_display = CAT_REVERSE.get(prefill.get("category", ""), CATEGORIES[0])
    f_category = ft.Dropdown(
        value=cat_display,
        border_radius=8, border_color=colors["BORDER"],
        focused_border_color=colors["ORANGE"],
        text_size=14, color=colors["TEXT"], bgcolor=colors["CARD_BG"],
        options=[ft.DropdownOption(key=c, text=c) for c in _get_categories_from_db()],
    )

    storage_val = prefill.get("storage", STORAGES[0])
    if storage_val not in STORAGES:
        storage_val = STORAGES[0]
    f_storage = ft.Dropdown(
        value=storage_val,
        border_radius=8, border_color=colors["BORDER"],
        focused_border_color=colors["ORANGE"],
        text_size=14, color=colors["TEXT"], bgcolor=colors["CARD_BG"],
        options=[ft.DropdownOption(key=s, text=s) for s in STORAGES],
    )

    # Inventory & Units
    qty_val = prefill.get("quantity", "")
    f_quantity = ft.TextField(
        value=str(qty_val) if qty_val else "0.00",
        border_radius=8, border_color=colors["BORDER"],
        focused_border_color=colors["ORANGE"], cursor_color=colors["ORANGE"],
        text_size=14, color=colors["TEXT"], bgcolor=colors["CARD_BG"],
        keyboard_type=ft.KeyboardType.NUMBER,
        content_padding=ft.Padding.symmetric(horizontal=14, vertical=12),
    )

    unit_display = UNIT_REVERSE.get(prefill.get("unit", "L"), "Liters (L)")
    f_unit = ft.Dropdown(
        value=unit_display,
        border_radius=8, border_color=colors["BORDER"],
        focused_border_color=colors["ORANGE"],
        text_size=14, color=colors["TEXT"], bgcolor=colors["CARD_BG"],
        options=[ft.DropdownOption(key=u, text=u) for u in UNITS],
    )

    today_str = datetime.now().strftime("%Y-%m-%d")
    f_purchase_date = ft.TextField(
        value=prefill.get("purchase_date", today_str) or today_str,
        border_radius=8, border_color=colors["BORDER"],
        focused_border_color=colors["ORANGE"], cursor_color=colors["ORANGE"],
        text_size=14, color=colors["TEXT"], bgcolor=colors["CARD_BG"],
        prefix_icon=ft.Icons.CALENDAR_TODAY_OUTLINED,
        content_padding=ft.Padding.symmetric(horizontal=14, vertical=12),
    )

    f_notes = ft.TextField(
        value=prefill.get("internal_notes", ""),
        hint_text="e.g. Grass-fed, supplied by Local Meadows Farm...",
        border_radius=8, border_color=colors["BORDER"],
        focused_border_color=colors["ORANGE"], cursor_color=colors["ORANGE"],
        text_size=14, color=colors["TEXT"], bgcolor=colors["CARD_BG"],
        multiline=True, min_lines=3, max_lines=5,
        content_padding=ft.Padding.all(14),
    )

    # Expiry Monitoring
    f_batch = ft.TextField(
        value=prefill.get("batch_number", ""),
        hint_text="e.g. BATCH 2024-001",
        border_radius=8, border_color=colors["BORDER"],
        focused_border_color=colors["ORANGE"], cursor_color=colors["ORANGE"],
        text_size=14, color=colors["TEXT"], bgcolor=colors["CARD_BG"],
        content_padding=ft.Padding.symmetric(horizontal=14, vertical=12),
    )

    f_expiry = ft.TextField(
        value=prefill.get("expiry_date", ""),
        hint_text="YYYY-MM-DD",
        border_radius=8, border_color=colors["BORDER"],
        focused_border_color=colors["ORANGE"], cursor_color=colors["ORANGE"],
        text_size=14, color=colors["TEXT"], bgcolor=colors["CARD_BG"],
        content_padding=ft.Padding.symmetric(horizontal=14, vertical=12),
    )

    f_threshold = ft.TextField(
        value=str(prefill.get("alert_threshold", 3)),
        border_radius=8, border_color=colors["BORDER"],
        focused_border_color=colors["ORANGE"], cursor_color=colors["ORANGE"],
        text_size=14, color=colors["TEXT"], bgcolor=colors["CARD_BG"],
        prefix_icon=ft.Icons.ACCESS_TIME,
        keyboard_type=ft.KeyboardType.NUMBER,
        content_padding=ft.Padding.symmetric(horizontal=14, vertical=12),
    )

    error_text = ft.Text("", size=13, color=colors["RED"], visible=False)

    # ───────────────────── CARDS ─────────────────────

    basic_card = ft.Container(
        bgcolor=colors["CARD_BG"],
        border=ft.Border.all(1, colors["BORDER"]),
        border_radius=12, shadow=card_shadow(),
        padding=ft.Padding.all(28),
        content=ft.Column(
            spacing=16,
            controls=[
                section_header(ft.Icons.INVENTORY_2_OUTLINED, colors["ORANGE_BG"],
                               "Basic Details", "General identification for this product."),
                field_label("Item Name", required=True),
                f_item_name,
                ft.Row(
                    spacing=16,
                    controls=[
                        ft.Container(
                            expand=True,
                            content=ft.Column(spacing=8, controls=[
                                field_label("Category", required=True),
                                f_category,
                            ]),
                        ),
                        ft.Container(
                            expand=True,
                            content=ft.Column(spacing=8, controls=[
                                field_label("Storage Location", required=True),
                                f_storage,
                            ]),
                        ),
                    ],
                ),
            ],
        ),
    )

    inventory_card = ft.Container(
        bgcolor=colors["CARD_BG"],
        border=ft.Border.all(1, colors["BORDER"]),
        border_radius=12, shadow=card_shadow(),
        padding=ft.Padding.all(28),
        content=ft.Column(
            spacing=16,
            controls=[
                section_header(ft.Icons.WIDGETS_OUTLINED, colors["ORANGE_BG"],
                               "Inventory & Units", "Current quantities and purchase metadata."),
                ft.Row(
                    spacing=16,
                    controls=[
                        ft.Container(
                            expand=1,
                            content=ft.Column(spacing=8, controls=[
                                field_label("Quantity", required=True),
                                f_quantity,
                            ]),
                        ),
                        ft.Container(
                            expand=1,
                            content=ft.Column(spacing=8, controls=[
                                field_label("Unit", required=True),
                                f_unit,
                            ]),
                        ),
                        ft.Container(
                            expand=1,
                            content=ft.Column(spacing=8, controls=[
                                field_label("Purchase Date"),
                                f_purchase_date,
                            ]),
                        ),
                    ],
                ),
                field_label("Internal Notes"),
                f_notes,
                helper_text("Optional details like supplier or quality grade."),
            ],
        ),
    )

    expiry_card = ft.Container(
        bgcolor=colors["CARD_BG"],
        border=ft.Border.all(1, colors["BORDER"]),
        border_radius=12, shadow=card_shadow(),
        padding=ft.Padding.all(28),
        content=ft.Column(
            spacing=16,
            controls=[
                section_header(ft.Icons.TIMER_OUTLINED, colors["ORANGE_BG"],
                               "Expiry Monitoring",
                               "Configure alerts to prevent food waste before expiration."),
                ft.Row(
                    spacing=16,
                    controls=[
                        ft.Container(
                            expand=True,
                            content=ft.Column(spacing=8, controls=[
                                field_label("Batch Number"),
                                f_batch,
                                helper_text("Helpful for tracking specific shipments."),
                            ]),
                        ),
                        ft.Container(
                            expand=True,
                            content=ft.Column(spacing=8, controls=[
                                field_label("Expiry Date", required=True),
                                f_expiry,
                            ]),
                        ),
                    ],
                ),
                ft.Container(
                    content=ft.Column(spacing=8, controls=[
                        field_label("Alert Threshold (Days)"),
                        f_threshold,
                        helper_text("Days before expiry to receive a notification."),
                    ]),
                ),
            ],
        ),
    )

    # ───────────────────── ACTIONS ─────────────────────

    def validate_and_collect():
        error_text.visible = False
        name_val = (f_item_name.value or "").strip()
        cat_val = CAT_MAP.get(f_category.value, f_category.value)
        storage_val = f_storage.value
        qty_val = (f_quantity.value or "").strip()
        unit_val = UNIT_MAP.get(f_unit.value, f_unit.value)
        purchase_val = (f_purchase_date.value or "").strip()
        notes_val = (f_notes.value or "").strip()
        batch_val = (f_batch.value or "").strip()
        expiry_val = (f_expiry.value or "").strip()
        threshold_val = (f_threshold.value or "3").strip()

        if not name_val:
            error_text.value = "Item Name is required."
            error_text.visible = True
            page.update()
            return None
        if not qty_val:
            error_text.value = "Quantity is required."
            error_text.visible = True
            page.update()
            return None
        try:
            float(qty_val)
        except ValueError:
            error_text.value = "Quantity must be a number."
            error_text.visible = True
            page.update()
            return None
        if not expiry_val:
            error_text.value = "Expiry Date is required."
            error_text.visible = True
            page.update()
            return None
        try:
            datetime.strptime(expiry_val, "%Y-%m-%d")
        except ValueError:
            error_text.value = "Invalid expiry date. Use YYYY-MM-DD."
            error_text.visible = True
            page.update()
            return None
        try:
            int(threshold_val)
        except ValueError:
            error_text.value = "Alert threshold must be a whole number."
            error_text.visible = True
            page.update()
            return None

        return {
            "item_name": name_val,
            "category": cat_val,
            "storage": storage_val,
            "quantity": float(qty_val),
            "unit": unit_val,
            "purchase_date": purchase_val,
            "internal_notes": notes_val,
            "batch_number": batch_val,
            "expiry_date": expiry_val,
            "alert_threshold": int(threshold_val),
        }

    def on_save(e):
        data = validate_and_collect()
        if data is None:
            return
        if editing:
            err = _update_item(edit_id, **data)
        else:
            err = _add_item(**data)
        if err:
            error_text.value = err
            error_text.visible = True
            page.update()
            return
        if editing and page.session.store.contains_key("edit_item_id"):
            page.session.store.remove("edit_item_id")
        page.go("/inventory")

    def on_save_and_add(e):
        data = validate_and_collect()
        if data is None:
            return
        err = _add_item(**data)
        if err:
            error_text.value = err
            error_text.visible = True
            page.update()
            return
        # Reset form
        f_item_name.value = ""
        f_category.value = CATEGORIES[0]
        f_storage.value = STORAGES[0]
        f_quantity.value = "0.00"
        f_unit.value = UNITS[1]
        f_purchase_date.value = today_str
        f_notes.value = ""
        f_batch.value = ""
        f_expiry.value = ""
        f_threshold.value = "3"
        error_text.visible = False
        page.update()
        snack = ft.SnackBar(
            content=ft.Text("Item saved! Add another one.", color="#FFFFFF"),
            bgcolor=colors["GREEN"],
            duration=2000,
        )
        page.show_dialog(snack)

    def on_cancel(e):
        if editing and page.session.store.contains_key("edit_item_id"):
            page.session.store.remove("edit_item_id")
        page.go("/inventory")

    action_row = ft.Container(
        padding=ft.Padding.only(left=60, right=60, top=8, bottom=24),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    spacing=6,
                    controls=[
                        ft.Icon(ft.Icons.INFO_OUTLINE, size=14, color=colors["MUTED"]),
                        ft.Text(
                            "Fields marked with an asterisk (*) are mandatory.",
                            size=12, color=colors["MUTED"],
                        ),
                    ],
                ),
                ft.Row(
                    spacing=12,
                    controls=[
                        ft.TextButton(
                            "Cancel", on_click=on_cancel,
                            style=ft.ButtonStyle(
                                color=colors["TEXT_SECONDARY"],
                                padding=ft.Padding.symmetric(horizontal=16, vertical=10),
                            ),
                        ),
                        *([] if editing else [
                            ft.OutlinedButton(
                                "Save & Add Another",
                                on_click=on_save_and_add,
                                style=ft.ButtonStyle(
                                    color=colors["TEXT"],
                                    side=ft.BorderSide(1, colors["BORDER"]),
                                    shape=ft.RoundedRectangleBorder(radius=8),
                                    padding=ft.Padding.symmetric(horizontal=20, vertical=10),
                                ),
                            ),
                        ]),
                        ft.Button(
                            "Save Product" if not editing else "Update Product",
                            icon=ft.Icons.SAVE_OUTLINED,
                            on_click=on_save,
                            style=ft.ButtonStyle(
                                bgcolor=colors["ORANGE"],
                                color="#FFFFFF",
                                elevation=0,
                                shape=ft.RoundedRectangleBorder(radius=8),
                                padding=ft.Padding.symmetric(horizontal=24, vertical=12),
                            ),
                        ),
                    ],
                ),
            ],
        ),
    )

    error_row = ft.Container(
        padding=ft.Padding.only(left=60, right=60),
        content=error_text,
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
                    size=12, color=colors["MUTED"],
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

    # ───────────────────── LAYOUT ─────────────────────

    form_content = ft.Container(
        padding=ft.Padding.symmetric(horizontal=60, vertical=0),
        content=ft.Column(
            spacing=20,
            controls=[basic_card, inventory_card, expiry_card],
        ),
    )

    scrollable = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=0,
        controls=[
            back_link,
            header,
            form_content,
            error_row,
            action_row,
            ft.Container(expand=True),
            footer,
        ],
    )

    content_area = ft.Container(
        expand=True,
        bgcolor=colors["BG"],
        content=ft.Column(
            expand=True, spacing=0,
            controls=[top_bar, scrollable],
        ),
    )

    return ft.View(
        route="/add-item",
        padding=0,
        spacing=0,
        bgcolor=colors["BG"],
        controls=[content_area],
    )
