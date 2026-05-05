import flet as ft
import flet_charts as fch
import sqlite3
import requests
from datetime import datetime, timedelta, date

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
    "CHART_GRID": "#F0F0F0",
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
    "CHART_GRID": "#252525",
    "TABLE_HEADER_BG": "#202020",
    "AVATAR_BG": "#5D4037",
}


def dashboard_view(page: ft.Page) -> ft.View:
    colors = LIGHT.copy() if page.theme_mode == ft.ThemeMode.LIGHT else DARK.copy()
    role = page.session.store.get("role") or "chef"

    # ───────────────────── Helpers ─────────────────────

    def card_shadow():
        return ft.BoxShadow(
            blur_radius=12,
            spread_radius=0,
            color=colors["SHADOW"],
            offset=ft.Offset(0, 2),
        )

    # -------------------- DB helpers --------------------
    DB_PATH = "inventory.db"

    def _connect(db_path=DB_PATH):
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _safe_int(v):
        try:
            return int(v)
        except Exception:
            return 0

    def get_total_items():
        try:
            response = requests.get(f"{API_URL}/dashboard/stats", timeout=5)
            if response.status_code == 200:
                return response.json().get("total_items", 0)
        except Exception:
            return 0

    def get_near_expiry(days=7):
        try:
            response = requests.get(f"{API_URL}/dashboard/stats", timeout=5)
            if response.status_code == 200:
                return response.json().get("items_near_expiry", 0)
        except Exception:
            return 0

    def get_expired_today():
        try:
            response = requests.get(f"{API_URL}/dashboard/stats", timeout=5)
            if response.status_code == 200:
                return response.json().get("items_expired", 0)
        except Exception:
            return 0

    def get_waste_sum_since(days=7):
        try:
            if days == 7:
                response = requests.get(f"{API_URL}/dashboard/stats", timeout=5)
                if response.status_code == 200:
                    return float(response.json().get("weekly_waste_cost", 0.0))
            response = requests.get(f"{API_URL}/waste-logs", timeout=5)
            rows = response.json().get("data", []) if response.status_code == 200 else []
            cutoff = (date.today() - timedelta(days=days - 1)).isoformat()
            total = 0.0
            for row in rows:
                if (row.get("waste_date") or "") >= cutoff:
                    total += float(row.get("cost_estimate") or 0)
            return total
        except Exception:
            return 0.0

    def get_waste_distribution(top_n=5):
        try:
            response = requests.get(f"{API_URL}/dashboard/waste-summary", timeout=5)
            rows = response.json().get("data", []) if response.status_code == 200 else []
            return [(row.get("reason") or "other", float(row.get("cost_total") or 0)) for row in rows[:top_n]]
        except Exception:
            return []

    def get_daily_trend(days=7):
        try:
            response = requests.get(f"{API_URL}/waste-logs", timeout=5)
            rows = response.json().get("data", []) if response.status_code == 200 else []
            results = []
            labels = []
            for i in range(days - 1, -1, -1):
                dt = date.today() - timedelta(days=i)
                labels.append(dt.strftime("%a"))
                total = 0.0
                for row in rows:
                    if (row.get("waste_date") or "") == dt.isoformat():
                        total += float(row.get("cost_estimate") or 0)
                results.append(total)
            return [(i, v) for i, v in enumerate(results)], labels
        except Exception:
            return [], []

    def get_expiring_items(days=7, limit=5):
        try:
            response = requests.get(f"{API_URL}/inventory", params={"status": "Expiring Soon"}, timeout=5)
            if response.status_code == 200:
                return response.json().get("data", [])[:limit]
        except Exception:
            return []

    def get_recent_waste_logs(limit=5):
        try:
            response = requests.get(f"{API_URL}/waste-logs", timeout=5)
            if response.status_code == 200:
                return response.json().get("data", [])[:limit]
        except Exception:
            return []

    # ───────────────────── SIDEBAR ─────────────────────

    def _get_role_label(r):
        return {"chef": "Kitchen Staff", "inventory_staff": "Inventory Manager", "manager": "General Manager"}.get(r, "Kitchen Staff")

    today_date = date.today()

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

    def on_search_submit(e):
        val = (search_field.value or "").strip()
        if val:
            page.session.store.set("global_search", val)
            page.go("/inventory")

    search_field.on_submit = on_search_submit

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
                                    ft.Text(_get_role_label(role), size=12, color=colors["MUTED"]),
                                ],
                            ),
                            user_avatar,
                        ],
                    ),
                ),
            ],
        ),
    )

    # ───────────────────── CONTENT HEADER ─────────────────────

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
                            "Kitchen Dashboard", size=26,
                            weight=ft.FontWeight.W_700,
                            color=colors["TEXT"],
                        ),
                        ft.Text(
                            "Monitor inventory status and track waste efficiency.",
                            size=14, color=colors["MUTED"],
                        ),
                    ],
                ),
                ft.Row(
                    spacing=14,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=([ ] + [
                        ft.Button(
                            "Record Waste",
                            icon=ft.Icons.ADD,
                            on_click=lambda e: page.go("/waste/new"),
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
                    ] if role in ("chef", "manager") else [])
                ),
            ],
        ),
    )

    # ───────────────────── STAT CARDS ─────────────────────

    def stat_card(icon, icon_bg, label, value, trend_icon, trend_text):
        return ft.Container(
            expand=True,
            bgcolor=colors["CARD_BG"],
            border=ft.Border.all(1, colors["BORDER"]),
            border_radius=12,
            padding=18,
            shadow=card_shadow(),
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Container(
                                width=42,
                                height=42,
                                bgcolor=icon_bg,
                                border_radius=21,
                                alignment=ft.Alignment(0, 0),
                                content=ft.Icon(
                                    icon, size=20, color=colors["MUTED"],
                                ),
                            ),
                            ft.Row(
                                spacing=4,
                                controls=[
                                    ft.Icon(
                                        trend_icon, size=14,
                                        color=colors["MUTED"],
                                    ),
                                    ft.Text(
                                        trend_text, size=11,
                                        color=colors["MUTED"],
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ft.Text(label, size=13, color=colors["MUTED"]),
                    ft.Text(
                        value, size=28,
                        weight=ft.FontWeight.W_700,
                        color=colors["TEXT"],
                    ),
                ],
            ),
        )

    # Fetch dynamic stats from DB
    total_items = get_total_items()
    near_expiry_count = get_near_expiry(7)
    expired_today_count = get_expired_today()
    waste_week = get_waste_sum_since(7)
    # compute previous week for simple percent delta
    waste_2weeks = get_waste_sum_since(14)
    prev_week = max(0.0, waste_2weeks - waste_week)
    waste_delta_pct = None
    try:
        if prev_week > 0:
            waste_delta_pct = int(((waste_week - prev_week) / prev_week) * 100)
        else:
            waste_delta_pct = None
    except Exception:
        waste_delta_pct = None

    # Format display values
    total_val = f"{total_items:,}"
    near_val = str(near_expiry_count)
    expired_val = str(expired_today_count)
    waste_val = f"${waste_week:,.2f}"
    waste_trend_text = (f"{waste_delta_pct}% vs prev week" if waste_delta_pct is not None else "—")

    stats_row = ft.Container(
        padding=ft.Padding.symmetric(horizontal=32, vertical=10),
        content=ft.Row(
            spacing=16,
            controls=[
                stat_card(
                    ft.Icons.INVENTORY_2_OUTLINED, colors["SEARCH_BG"],
                    "Total Items", total_val,
                    ft.Icons.TRENDING_UP, "",
                ),
                stat_card(
                    ft.Icons.WARNING_AMBER_OUTLINED, colors["ORANGE_BG"],
                    "Near Expiry", near_val,
                    ft.Icons.TRENDING_UP, "needs attention",
                ),
                stat_card(
                    ft.Icons.ERROR_OUTLINE, colors["RED_BG"],
                    "Expired Today", expired_val,
                    ft.Icons.TRENDING_DOWN, "",
                ),
                stat_card(
                    ft.Icons.ATTACH_MONEY, colors["GREEN_BG"],
                    "Waste Cost (Wk)", waste_val,
                    ft.Icons.TRENDING_UP, waste_trend_text,
                ),
            ],
        ),
    )

    # ───────────────────── WASTE DISTRIBUTION ─────────────────────

    waste_data = get_waste_distribution(5)
    if not waste_data:
        # placeholder when no data
        waste_data = []
        max_waste = 1
    else:
        max_waste = max(v for _, v in waste_data) or 1

    def waste_bar(label, value):
        bar_w = (value / max_waste) * 320
        return ft.Container(
            padding=ft.Padding.symmetric(vertical=5),
            content=ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        label, size=12, color=colors["MUTED"],
                        width=60, text_align=ft.TextAlign.RIGHT,
                    ),
                    ft.Container(
                        width=bar_w,
                        height=26,
                        bgcolor=colors["ORANGE"],
                        border_radius=4,
                    ),
                ],
            ),
        )

    waste_card = ft.Container(
        expand=True,
        bgcolor=colors["CARD_BG"],
        border=ft.Border.all(1, colors["BORDER"]),
        border_radius=12,
        padding=20,
        shadow=card_shadow(),
        content=ft.Column(
            spacing=14,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text(
                                    "Waste Distribution", size=16,
                                    weight=ft.FontWeight.W_600,
                                    color=colors["TEXT"],
                                ),
                                ft.Text(
                                    "Estimated cost by food category this week",
                                    size=12, color=colors["MUTED"],
                                ),
                            ],
                        ),
                        ft.IconButton(
                            ft.Icons.MORE_VERT,
                            icon_size=18,
                            icon_color=colors["MUTED"],
                        ),
                    ],
                ),
                ft.Column(
                    spacing=2,
                    controls=[waste_bar(l, v) for l, v in waste_data] if waste_data else [ft.Text("No waste data yet", color=colors["MUTED"])],
                ),
            ],
        ),
    )

    # ───────────────────── DAILY WASTE TREND ─────────────────────

    trend_points, day_labels = get_daily_trend(7)
    if not trend_points:
        trend_points = [(i, 0) for i in range(6)]
        day_labels = [(date.today() - timedelta(days=5 - i)).strftime("%a") for i in range(6)]

    target_y = int(sum(y for _, y in trend_points) / max(1, len(trend_points)))

    trend_series = fch.LineChartData(
        points=[fch.LineChartDataPoint(x, y) for x, y in trend_points],
        stroke_width=2.5,
        color=colors["ORANGE"],
        curved=True,
        rounded_stroke_cap=True,
        below_line_gradient=ft.LinearGradient(
            begin=ft.Alignment(0, -1),
            end=ft.Alignment(0, 1),
            colors=["#40E68A17", "#05E68A17"],
        ),
    )

    target_series = fch.LineChartData(
        points=[fch.LineChartDataPoint(x, target_y) for x in range(len(trend_points))],
        stroke_width=1.5,
        color="#BBBBBB",
        dash_pattern=[6, 4],
    )

    trend_chart = fch.LineChart(
    data_series=[trend_series, target_series],
    min_x=0,
    max_x=max(0, len(trend_points) - 1),
    min_y=0,
    max_y=max(target_y * 2, 10),
    height=200,
    
    expand=True,
        bgcolor="transparent",
        horizontal_grid_lines=fch.ChartGridLines(
            interval=max(1, int((max(y for _, y in trend_points) or 10) / 4)),
            color=colors["CHART_GRID"],
            width=1,
        ),
        left_axis=fch.ChartAxis(show_labels=False, label_size=0),
        right_axis=fch.ChartAxis(show_labels=False, label_size=0),
        top_axis=fch.ChartAxis(show_labels=False, label_size=0),
        bottom_axis=fch.ChartAxis(
            labels=[
                fch.ChartAxisLabel(
                    value=i,
                    label=ft.Text(d, size=11, color=colors["MUTED"]),
                )
                for i, d in enumerate(day_labels)
            ],
            label_size=28,
        ),
        tooltip=fch.LineChartTooltip(bgcolor=colors["CARD_BG"]),
    )

    on_track_badge = ft.Container(
        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
        bgcolor=colors["GREEN_BG"],
        border_radius=12,
        content=ft.Text(
            "On Track", size=11,
            color=colors["GREEN"],
            weight=ft.FontWeight.W_600,
        ),
    )

    trend_card = ft.Container(
        expand=True,
        bgcolor=colors["CARD_BG"],
        border=ft.Border.all(1, colors["BORDER"]),
        border_radius=12,
        padding=20,
        shadow=card_shadow(),
        content=ft.Column(
            spacing=14,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text(
                                    "Daily Waste Trend", size=16,
                                    weight=ft.FontWeight.W_600,
                                    color=colors["TEXT"],
                                ),
                                ft.Text(
                                    "Comparison against daily reduction target",
                                    size=12, color=colors["MUTED"],
                                ),
                            ],
                        ),
                        on_track_badge,
                    ],
                ),
                trend_chart,
            ],
        ),
    )

    charts_row = ft.Container(
        padding=ft.Padding.symmetric(horizontal=32, vertical=10),
        content=ft.Row(
            spacing=16,
            controls=[waste_card, trend_card],
        ),
    )

    # ───────────────────── EXPIRING SOON TABLE ─────────────────────

    def status_badge(text, expired=False):
        bg = colors["RED_BG"] if expired else colors["ORANGE_BG"]
        color = colors["RED"] if expired else colors["ORANGE"]
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            bgcolor=bg,
            border_radius=4,
            content=ft.Text(
                text, size=11, color=color,
                weight=ft.FontWeight.W_600,
            ),
        )

    # fetch expiring items from DB
    expiring_rows = get_expiring_items(7, limit=5)
    expiring_rows_data = []
    for r in expiring_rows:
        name = r["item_name"] if r["item_name"] else ""
        cat = r["category"] if r["category"] else ""
        ex_date = r["expiry_date"]
        try:
            ex_dt = datetime.strptime(ex_date[:10], "%Y-%m-%d").date()
            days_left = (ex_dt - date.today()).days
            expired_flag = days_left < 0
            if expired_flag:
                ex_text = ex_dt.strftime("%b %d")
                status = "Expired"
            else:
                ex_text = ex_dt.strftime("%b %d") if days_left > 0 else "Today"
                status = "Near Expiry"
        except Exception:
            ex_text = str(ex_date)
            status = "Near Expiry"
            expired_flag = False
        expiring_rows_data.append((name, cat, ex_text, status, expired_flag))

    expiring_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text(
                "Item Name", size=12,
                color=colors["MUTED"], weight=ft.FontWeight.W_600,
            )),
            ft.DataColumn(ft.Text(
                "Category", size=12,
                color=colors["MUTED"], weight=ft.FontWeight.W_600,
            )),
            ft.DataColumn(ft.Text(
                "Expiry", size=12,
                color=colors["MUTED"], weight=ft.FontWeight.W_600,
            )),
            ft.DataColumn(ft.Text(
                "Status", size=12,
                color=colors["MUTED"], weight=ft.FontWeight.W_600,
            )),
        ],
        rows=[
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(
                    n, size=13, color=colors["TEXT"],
                    weight=ft.FontWeight.W_500,
                )),
                ft.DataCell(ft.Text(
                    c, size=13, color=colors["TEXT_SECONDARY"],
                )),
                ft.DataCell(ft.Text(
                    e, size=13, color=colors["TEXT_SECONDARY"],
                )),
                ft.DataCell(status_badge(s, ex)),
            ])
            for n, c, e, s, ex in expiring_rows_data
        ],
        horizontal_lines=ft.BorderSide(1, colors["DIVIDER"]),
        heading_row_color=colors["TABLE_HEADER_BG"],
        column_spacing=20,
        data_row_max_height=52,
    )

    expiring_card = ft.Container(
        expand=True,
        bgcolor=colors["CARD_BG"],
        border=ft.Border.all(1, colors["BORDER"]),
        border_radius=12,
        padding=20,
        shadow=card_shadow(),
        content=ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text(
                                    "Expiring Soon", size=16,
                                    weight=ft.FontWeight.W_600,
                                    color=colors["TEXT"],
                                ),
                                ft.Text(
                                    "Action items for chef planning",
                                    size=12, color=colors["MUTED"],
                                ),
                            ],
                        ),
                        ft.TextButton(
                            on_click=lambda e: page.go("/expiry"),
                            content=ft.Row(
                                spacing=4,
                                controls=[
                                    ft.Text(
                                        "View Monitor", size=13,
                                        color=colors["ORANGE"],
                                        weight=ft.FontWeight.W_600,
                                    ),
                                    ft.Icon(
                                        ft.Icons.CHEVRON_RIGHT,
                                        size=16, color=colors["ORANGE"],
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
                ft.Container(
                    height=220,
                    content=ft.Column(
                        scroll=ft.ScrollMode.AUTO,
                        controls=[expiring_table],
                    ),
                ),
            ],
        ),
    )

    # ───────────────────── RECENT WASTE LOGS TABLE ─────────────────────

    # fetch recent waste logs
    recent_logs = get_recent_waste_logs(5)
    logs_rows_data = []
    for r in recent_logs:
        item_name = r["item_name"] or "Unknown"
        qty = r["qty_wasted"]
        unit = r["unit"] or ""
        qty_display = f"{qty} {unit}".strip()
        reason = r["reason"] or ""
        cost = float(r["cost_estimate"] or 0.0)
        cost_display = f"${cost:,.2f}"
        # relative time
        rec_date = None
        try:
            rec_date = datetime.strptime(r["waste_date"][:10], "%Y-%m-%d")
            diff = datetime.now() - rec_date
            if diff.days == 0:
                rec = "Today"
            elif diff.days == 1:
                rec = "1d ago"
            else:
                rec = f"{diff.days}d ago"
        except Exception:
            rec = str(r["waste_date"])
        logs_rows_data.append((item_name, qty_display, reason, cost_display, rec))

    def log_item_cell(name, sub):
        return ft.DataCell(
            ft.Column(
                spacing=0,
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        name, size=13, color=colors["TEXT"],
                        weight=ft.FontWeight.W_500,
                    ),
                    ft.Text(sub, size=11, color=colors["MUTED"]),
                ],
            ),
        )

    def reason_cell(reason):
        return ft.DataCell(
            ft.Row(
                spacing=6,
                controls=[
                    ft.Container(
                        width=8, height=8,
                        bgcolor=colors["ORANGE"],
                        border_radius=4,
                    ),
                    ft.Text(
                        reason, size=13,
                        color=colors["TEXT_SECONDARY"],
                    ),
                ],
            ),
        )

    logs_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text(
                "Item", size=12,
                color=colors["MUTED"], weight=ft.FontWeight.W_600,
            )),
            ft.DataColumn(ft.Text(
                "Reason", size=12,
                color=colors["MUTED"], weight=ft.FontWeight.W_600,
            )),
            ft.DataColumn(ft.Text(
                "Cost", size=12,
                color=colors["MUTED"], weight=ft.FontWeight.W_600,
            )),
            ft.DataColumn(ft.Text(
                "Recorded", size=12,
                color=colors["MUTED"], weight=ft.FontWeight.W_600,
            )),
        ],
        rows=[
            ft.DataRow(cells=[
                log_item_cell(n, sub),
                reason_cell(r),
                ft.DataCell(ft.Text(
                    cost, size=13, color=colors["TEXT"],
                    weight=ft.FontWeight.W_500,
                )),
                ft.DataCell(ft.Text(
                    rec, size=13, color=colors["MUTED"],
                )),
            ])
            for n, sub, r, cost, rec in logs_rows_data
        ],
        horizontal_lines=ft.BorderSide(1, colors["DIVIDER"]),
        heading_row_color=colors["TABLE_HEADER_BG"],
        column_spacing=20,
        data_row_max_height=56,
    )

    logs_card = ft.Container(
        expand=True,
        bgcolor=colors["CARD_BG"],
        border=ft.Border.all(1, colors["BORDER"]),
        border_radius=12,
        padding=20,
        shadow=card_shadow(),
        content=ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text(
                                    "Recent Waste Logs", size=16,
                                    weight=ft.FontWeight.W_600,
                                    color=colors["TEXT"],
                                ),
                                ft.Text(
                                    "Track disposal reasons and costs",
                                    size=12, color=colors["MUTED"],
                                ),
                            ],
                        ),
                        ft.TextButton(
                            on_click=lambda e: page.go("/waste-logs"),
                            content=ft.Row(
                                spacing=4,
                                controls=[
                                    ft.Text(
                                        "All Logs", size=13,
                                        color=colors["ORANGE"],
                                        weight=ft.FontWeight.W_600,
                                    ),
                                    ft.Icon(
                                        ft.Icons.CHEVRON_RIGHT,
                                        size=16, color=colors["ORANGE"],
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
                ft.Container(
                    height=260,
                    content=ft.Column(
                        scroll=ft.ScrollMode.AUTO,
                        controls=[logs_table],
                    ),
                ),
            ],
        ),
    )

    tables_row = ft.Container(
        padding=ft.Padding.only(left=32, right=32, top=10, bottom=24),
        content=ft.Row(
            spacing=16,
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[expiring_card, logs_card],
        ),
    )

    # ───────────────────── LAYOUT ASSEMBLY ─────────────────────

    scrollable_content = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=0,
        controls=[
            content_header,
            stats_row,
            charts_row,
            tables_row,
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
        route="/dashboard",
        padding=0,
        spacing=0,
        bgcolor=colors["BG"],
        controls=[layout],
    )
