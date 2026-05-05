import flet as ft
import sqlite3
import requests
from datetime import datetime, date

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


def _init_waste_logs_db():
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


def _fetch_waste_logs(search_text="", date_from="", date_to="", reason="All Reasons"):
    try:
        response = requests.get(f"{API_URL}/waste-logs", timeout=5)
        rows = response.json().get("data", []) if response.status_code == 200 else []
    except requests.exceptions.RequestException:
        rows = []

    filtered = []
    for row in rows:
        waste_date = row.get("waste_date") or ""
        if date_from and waste_date and waste_date < date_from:
            continue
        if date_to and waste_date and waste_date > date_to:
            continue
        filtered.append(row)
    return filtered


def waste_logs_view(page: ft.Page) -> ft.View:
    _init_waste_logs_db()
    colors = LIGHT.copy() if page.theme_mode == ft.ThemeMode.LIGHT else DARK.copy()
    role = page.session.store.get("role") or "chef"

    current_page = [1]
    rows_per_page = 8

    def card_shadow():
        return ft.BoxShadow(
            blur_radius=12,
            spread_radius=0,
            color=colors["SHADOW"],
            offset=ft.Offset(0, 2),
        )

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

    logo_icon = ft.Image(src="assets/logo.png", width=36, height=36, fit=ft.BoxFit.CONTAIN)
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
            (ft.Icons.PEOPLE_OUTLINE, "Users", page.route == "/users", "/users"),
        ])
    # Settings removed (not implemented)

    nav_column = ft.Column(
        spacing=2,
        controls=[build_nav_item(i, l, a, r) for i, l, a, r in nav_items_data],
    )

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
    initials = username[:2].upper()

    topbar_search = ft.TextField(
        hint_text="Search waste logs, items, reasons...",
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
                ft.Row(
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.NOTIFICATIONS_NONE, size=22, color=colors["MUTED"]),
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
                                            ft.Text(page.session.store.get("role") or "Kitchen Staff", size=12, color=colors["MUTED"]),
                                        ],
                                    ),
                                    ft.Container(width=38, height=38, bgcolor=colors["AVATAR_BG"], border_radius=19, alignment=ft.Alignment(0, 0), content=ft.Text(initials, size=14, weight=ft.FontWeight.W_600, color=colors["ORANGE"])),
                                ],
                            ),
                        ),
                    ],
                ),
            ],
        ),
    )

    title_block = ft.Container(
        padding=ft.Padding.only(left=32, right=32, top=24, bottom=8),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Column(
                    spacing=4,
                    controls=[
                        ft.Text("Waste Logs", size=26, weight=ft.FontWeight.W_700, color=colors["TEXT"]),
                        ft.Text("Audit trail of all food waste events and costs", size=14, color=colors["MUTED"]),
                    ],
                ),
                ft.Button(
                    "+ Record Waste",
                    icon=ft.Icons.ADD,
                    on_click=lambda e: page.go("/waste/new"),
                    style=ft.ButtonStyle(
                        bgcolor=colors["ORANGE"],
                        color="#FFFFFF",
                        elevation=0,
                        shape=ft.RoundedRectangleBorder(radius=8),
                        padding=ft.Padding.symmetric(horizontal=20, vertical=12),
                    ),
                ),
            ],
        ),
    )

    search_field = ft.TextField(
        hint_text="Search item, category, reason, or quantity...",
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

    date_from = ft.TextField(hint_text="From YYYY-MM-DD", width=160, height=42, border_radius=8, border_color=colors["BORDER"], focused_border_color=colors["ORANGE"], bgcolor=colors["CARD_BG"], text_size=14, color=colors["TEXT"], cursor_color=colors["ORANGE"])
    date_to = ft.TextField(hint_text="To YYYY-MM-DD", width=160, height=42, border_radius=8, border_color=colors["BORDER"], focused_border_color=colors["ORANGE"], bgcolor=colors["CARD_BG"], text_size=14, color=colors["TEXT"], cursor_color=colors["ORANGE"])
    # Reason filter removed (non-functional)

    def parse_date(value):
        if not value:
            return None
        try:
            return datetime.strptime(value.strip(), "%Y-%m-%d").date()
        except Exception:
            return None

    def format_money(value):
        return f"${float(value or 0):,.2f}"

    def get_reason_badge(reason):
        mapping = {
            "expired": ("Expired", colors["RED"], colors["RED_BG"]),
            "spoiled": ("Spoiled", colors["ORANGE"], colors["ORANGE_BG"]),
            "prep_waste": ("Prep Waste", "#B8860B", "#FFF4CC"),
            "overproduction": ("Overproduction", "#1D4ED8", "#DBEAFE"),
            "damaged": ("Damaged", colors["MUTED"], colors["DIVIDER"]),
            "other": ("Other", colors["MUTED"], colors["DIVIDER"]),
        }
        label, fg, bg = mapping.get((reason or "").lower(), (reason or "Other", colors["MUTED"], colors["DIVIDER"]))
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            bgcolor=bg,
            border_radius=4,
            content=ft.Text(label, size=11, color=fg, weight=ft.FontWeight.W_600),
        )

    def get_status_info(reason):
        return get_reason_badge(reason)

    def compute_metrics(rows):
        today = date.today()
        month_start = today.replace(day=1)

        waste_today = 0.0
        month_volume = 0.0
        total_cost_month = 0.0
        avoidable_cost = 0.0
        reason_costs = {}

        for row in rows:
            try:
                row_date = parse_date(row.get("waste_date", "")) or today
            except Exception:
                row_date = today
            qty = float(row.get("qty_wasted") or 0)
            cost = float(row.get("cost_estimate") or 0)
            reason = (row.get("reason") or "other").lower()
            if row_date == today:
                waste_today += cost
            if row_date >= month_start:
                month_volume += qty
                total_cost_month += cost
                reason_costs[reason] = reason_costs.get(reason, 0.0) + cost
                if reason in {"prep_waste", "overproduction"}:
                    avoidable_cost += cost

        avoidable_pct = (avoidable_cost / total_cost_month * 100.0) if total_cost_month else 0.0
        top_reason = "No waste logged this month"
        top_reason_cost = 0.0
        if reason_costs:
            top_reason, top_reason_cost = max(reason_costs.items(), key=lambda item: item[1])
        return waste_today, month_volume, avoidable_pct, top_reason, top_reason_cost

    all_rows_cache = _fetch_waste_logs()

    metric_today_text = ft.Text("$0.00", size=24, weight=ft.FontWeight.W_700, color=colors["TEXT"])
    metric_avoidable_text = ft.Text("0.0%", size=24, weight=ft.FontWeight.W_700, color=colors["TEXT"])

    summary_card_today = ft.Container(
        expand=True,
        bgcolor=colors["CARD_BG"],
        border=ft.Border.all(1, colors["BORDER"]),
        border_radius=12,
        shadow=card_shadow(),
        padding=ft.Padding.all(20),
        content=ft.Column(
            spacing=8,
            controls=[
                ft.Row(spacing=8, controls=[ft.Icon(ft.Icons.ATTACH_MONEY, size=16, color=colors["MUTED"]), ft.Text("Waste Cost Today", size=14, weight=ft.FontWeight.W_600, color=colors["TEXT"])]),
                metric_today_text,
                ft.Text("Cost estimate recorded for today", size=12, color=colors["MUTED"]),
            ],
        ),
    )

    summary_card_avoidable = ft.Container(
        expand=True,
        bgcolor=colors["CARD_BG"],
        border=ft.Border.all(1, colors["BORDER"]),
        border_radius=12,
        shadow=card_shadow(),
        padding=ft.Padding.all(20),
        content=ft.Column(
            spacing=8,
            controls=[
                ft.Row(spacing=8, controls=[ft.Icon(ft.Icons.PERCENT, size=16, color=colors["MUTED"]), ft.Text("Avoidable Waste %", size=14, weight=ft.FontWeight.W_600, color=colors["TEXT"])]),
                metric_avoidable_text,
                ft.Text("Prep waste and overproduction share", size=12, color=colors["MUTED"]),
            ],
        ),
    )

    metric_row = ft.Container(padding=ft.Padding.symmetric(horizontal=32, vertical=8), content=ft.Row(spacing=16, controls=[summary_card_today, summary_card_avoidable]))

    filters_row = ft.Container(
        padding=ft.Padding.symmetric(horizontal=32, vertical=10),
        content=ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                search_field,
                ft.Row(spacing=8, controls=[date_from, date_to]),
            ],
        ),
    )

    table_body = ft.Column(spacing=0)
    pagination_row = ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
    insight_text = ft.Text("No waste logged this month", size=14, color=colors["TEXT_SECONDARY"])

    def build_table_header():
        headers = [
            ("Date & Time", 2.0),
            ("Item & Category", 2.8),
            ("Quantity", 1.2),
            ("Reason", 1.4),
            ("Cost Estimate", 1.4),
            ("Recorded By", 1.4),
            ("Actions", 0.6),
        ]
        return ft.Container(
            bgcolor=colors["TABLE_HEADER_BG"],
            padding=ft.Padding.symmetric(horizontal=20, vertical=12),
            border=ft.Border(bottom=ft.BorderSide(1, colors["DIVIDER"])),
            content=ft.Row(
                spacing=8,
                controls=[
                    ft.Container(expand=20, content=ft.Text(headers[0][0], size=12, color=colors["MUTED"], weight=ft.FontWeight.W_600)),
                    ft.Container(expand=28, content=ft.Text(headers[1][0], size=12, color=colors["MUTED"], weight=ft.FontWeight.W_600)),
                    ft.Container(expand=12, content=ft.Text(headers[2][0], size=12, color=colors["MUTED"], weight=ft.FontWeight.W_600)),
                    ft.Container(expand=14, content=ft.Text(headers[3][0], size=12, color=colors["MUTED"], weight=ft.FontWeight.W_600)),
                    ft.Container(expand=14, content=ft.Text(headers[4][0], size=12, color=colors["MUTED"], weight=ft.FontWeight.W_600)),
                    ft.Container(expand=14, content=ft.Text(headers[5][0], size=12, color=colors["MUTED"], weight=ft.FontWeight.W_600)),
                    ft.Container(expand=6, content=ft.Text(headers[6][0], size=12, color=colors["MUTED"], weight=ft.FontWeight.W_600)),
                ],
            ),
        )

    def build_table_row(row):
        log_id = row["log_id"]
        item_id = row.get("item_id")
        item_name = row.get("item_name") or "Unknown Item"
        category = row.get("category") or "Uncategorized"
        qty = row.get("qty_wasted") or 0
        unit = row.get("unit") or ""
        reason = row.get("reason") or "other"
        waste_date = row.get("waste_date") or "—"
        cost = row.get("cost_estimate") or 0
        recorded_by = page.session.store.get("username") or "User"

        def open_item(e, iid=item_id):
            if iid:
                page.go(f"/item/{iid}")

        def record_again(e):
            page.go("/waste/new")

        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=20, vertical=10),
            border=ft.Border(bottom=ft.BorderSide(1, colors["DIVIDER"])),
            content=ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(expand=20, content=ft.Text(waste_date, size=13, color=colors["TEXT_SECONDARY"])),
                    ft.Container(
                        expand=28,
                        content=ft.Column(
                            spacing=0,
                            controls=[
                                ft.Text(item_name, size=14, color=colors["TEXT"], weight=ft.FontWeight.W_500),
                                ft.Text(category, size=11, color=colors["MUTED"]),
                            ],
                        ),
                    ),
                    ft.Container(expand=12, content=ft.Text(f"{qty} {unit}", size=13, color=colors["TEXT"])),
                    ft.Container(expand=14, content=get_status_info(reason)),
                    ft.Container(expand=14, content=ft.Text(format_money(cost), size=13, color=colors["TEXT"], weight=ft.FontWeight.W_500)),
                    ft.Container(expand=14, content=ft.Text(recorded_by, size=13, color=colors["TEXT_SECONDARY"])),
                    ft.Container(
                        expand=6,
                        content=ft.PopupMenuButton(
                            icon=ft.Icons.MORE_VERT,
                            icon_size=18,
                            icon_color=colors["MUTED"],
                            items=[
                                ft.PopupMenuItem(content=ft.Text("Open Item"), icon=ft.Icons.OPEN_IN_NEW, on_click=open_item),
                                ft.PopupMenuItem(content=ft.Text("Record Waste"), icon=ft.Icons.DELETE_OUTLINE, on_click=record_again),
                            ],
                        ),
                    ),
                ],
            ),
        )

    def build_pagination(total_items):
        total_pages = max(1, (total_items + rows_per_page - 1) // rows_per_page)
        start = (current_page[0] - 1) * rows_per_page + 1 if total_items else 0
        end = min(current_page[0] * rows_per_page, total_items)

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

        page_btns = [
            ft.TextButton("Previous", disabled=current_page[0] <= 1, on_click=go_prev, style=ft.ButtonStyle(color=colors["TEXT_SECONDARY"], padding=ft.Padding.symmetric(horizontal=10, vertical=6))),
        ]
        pages_to_show = list(range(1, total_pages + 1)) if total_pages <= 5 else [1, 2, 3, "...", total_pages]
        for p in pages_to_show:
            if p == "...":
                page_btns.append(ft.Text("...", size=13, color=colors["MUTED"]))
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
                            str(p),
                            size=13,
                            color="#FFFFFF" if is_current else colors["TEXT_SECONDARY"],
                            weight=ft.FontWeight.W_600 if is_current else ft.FontWeight.W_400,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    )
                )
        page_btns.append(ft.TextButton("Next", disabled=current_page[0] >= total_pages, on_click=go_next, style=ft.ButtonStyle(color=colors["TEXT_SECONDARY"], padding=ft.Padding.symmetric(horizontal=10, vertical=6))))

        pagination_row.controls = [
            ft.Text(f"Showing {start}-{end} of {total_items} logs", size=13, color=colors["MUTED"]),
            ft.Row(spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=page_btns),
        ]

    def refresh_metrics(rows):
        waste_today, month_volume, avoidable_pct, top_reason, top_reason_cost = compute_metrics(rows)
        metric_today_text.value = format_money(waste_today)
        metric_avoidable_text.value = f"{avoidable_pct:.1f}%"
        if top_reason_cost > 0:
            insight_text.value = f"Highest cost this month: {top_reason.replace('_', ' ').title()} at {format_money(top_reason_cost)}"
        else:
            insight_text.value = "No waste logged this month"

    def refresh_table():
        search_text = (search_field.value or "").strip().lower()
        rows = _fetch_waste_logs(search_text=search_text, date_from=date_from.value or "", date_to=date_to.value or "")
        refresh_metrics(rows)

        total = len(rows)
        total_pages = max(1, (total + rows_per_page - 1) // rows_per_page)
        if current_page[0] > total_pages:
            current_page[0] = total_pages

        start_idx = (current_page[0] - 1) * rows_per_page
        page_rows = rows[start_idx:start_idx + rows_per_page]

        table_body.controls = [build_table_header()]
        if not page_rows:
            table_body.controls.append(
                ft.Container(
                    padding=ft.Padding.symmetric(vertical=40),
                    alignment=ft.Alignment(0, 0),
                    content=ft.Text("No waste logs match the selected filters.", size=14, color=colors["MUTED"]),
                )
            )
        else:
            for row in page_rows:
                table_body.controls.append(build_table_row(row))
        build_pagination(total)
        page.update()

    def on_search_change(e):
        current_page[0] = 1
        refresh_table()

    def on_date_change(e):
        current_page[0] = 1
        refresh_table()

    search_field.on_change = on_search_change
    date_from.on_change = on_date_change
    date_to.on_change = on_date_change

    table_card = ft.Container(
        margin=ft.Margin(32, 8, 32, 0),
        bgcolor=colors["CARD_BG"],
        border=ft.Border.all(1, colors["BORDER"]),
        border_radius=12,
        shadow=card_shadow(),
        content=ft.Column(spacing=0, controls=[table_body, ft.Container(padding=ft.Padding.symmetric(horizontal=20, vertical=12), content=pagination_row)]),
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
                metric_row,
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=32, vertical=4),
                    content=ft.Row(spacing=12, controls=[search_field, date_from, date_to]),
                ),
                table_card,
                footer,
            ],
        ),
    )

    layout = ft.Row(expand=True, spacing=0, controls=[sidebar, content_area])

    refresh_table()

    return ft.View(route="/waste-logs", padding=0, spacing=0, bgcolor=colors["BG"], controls=[layout])
