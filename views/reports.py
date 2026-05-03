import flet as ft
import flet_charts as fch
import sqlite3
from datetime import date, datetime, timedelta

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


def _init_reports_db():
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


def _period_range(period):
    today = date.today()
    if period == "weekly":
        start = today - timedelta(days=27)
    elif period == "monthly":
        start = today - timedelta(days=182)
    else:
        start = today - timedelta(days=6)
    return start, today


def _fetch_rows(period, search_text=""):
    start_date, end_date = _period_range(period)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    query = """
        SELECT
            wl.log_id,
            wl.item_id,
            wl.qty_wasted,
            wl.unit,
            wl.reason,
            wl.waste_date,
            wl.cost_estimate,
            i.item_name,
            i.category
        FROM waste_logs wl
        LEFT JOIN inventory i ON i.id = wl.item_id
        WHERE wl.waste_date BETWEEN ? AND ?
    """
    params = [start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")]
    if search_text:
        query += " AND (i.item_name LIKE ? OR i.category LIKE ? OR wl.reason LIKE ?)"
        like = f"%{search_text}%"
        params.extend([like, like, like])
    cur.execute(query + " ORDER BY wl.waste_date ASC, wl.log_id ASC", params)
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows, start_date, end_date


def _aggregate_by_day(rows, start_date, end_date):
    labels = []
    values = []
    current = start_date
    by_day = {}
    for row in rows:
        by_day[row["waste_date"]] = by_day.get(row["waste_date"], 0.0) + float(row.get("cost_estimate") or 0)
    while current <= end_date:
        key = current.strftime("%Y-%m-%d")
        labels.append(current.strftime("%b %d"))
        values.append(by_day.get(key, 0.0))
        current += timedelta(days=1)
    return labels, values


def _aggregate_reason_cost(rows):
    totals = {}
    for row in rows:
        reason = (row.get("reason") or "other").lower()
        totals[reason] = totals.get(reason, 0.0) + float(row.get("cost_estimate") or 0)
    return totals


def _aggregate_item_cost(rows):
    totals = {}
    for row in rows:
        item_name = row.get("item_name") or "Unknown Item"
        totals[item_name] = totals.get(item_name, 0.0) + float(row.get("cost_estimate") or 0)
    return dict(sorted(totals.items(), key=lambda item: item[1], reverse=True)[:5])


def reports_view(page: ft.Page) -> ft.View:
    _init_reports_db()
    colors = LIGHT.copy() if page.theme_mode == ft.ThemeMode.LIGHT else DARK.copy()
    role = page.session.store.get("role") or "chef"

    selected_period = ["daily"]

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
            (ft.Icons.PEOPLE_OUTLINE, "Users & Staff", page.route == "/users", "/users"),
        ])
    nav_items_data.append((ft.Icons.SETTINGS_OUTLINED, "Settings", False, None))

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

    top_bar = ft.Container(
        padding=ft.Padding.symmetric(horizontal=32, vertical=14),
        border=ft.Border(bottom=ft.BorderSide(1, colors["BORDER"])),
        bgcolor=colors["CARD_BG"],
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.TextField(
                    hint_text="Search analytics...",
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
                ),
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
                                ft.Text(page.session.store.get("role") or "Kitchen Staff", size=12, color=colors["MUTED"]),
                            ],
                        ),
                        ft.Container(width=38, height=38, bgcolor=colors["AVATAR_BG"], border_radius=19, alignment=ft.Alignment(0, 0), content=ft.Text(initials, size=14, weight=ft.FontWeight.W_600, color=colors["ORANGE"])),
                    ],
                ),
            ],
        ),
    )

    title_block = ft.Container(
        padding=ft.Padding.only(left=32, right=32, top=24, bottom=8),
        content=ft.Column(
            spacing=4,
            controls=[
                ft.Text("Waste Analytics & Reports", size=26, weight=ft.FontWeight.W_700, color=colors["TEXT"]),
                ft.Text("Monitor kitchen waste trends and financial impact", size=14, color=colors["MUTED"]),
            ],
        ),
    )

    search_field = ft.TextField(
        hint_text="Search by item or reason...",
        width=260,
        height=40,
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

    period_buttons = {}

    def period_range_label(period):
        return {"daily": "Last 7 Days", "weekly": "Last 4 Weeks", "monthly": "Last 6 Months"}.get(period, "Last 7 Days")

    def reason_label(reason):
        return {
            "expired": "Expired",
            "spoiled": "Spoiled",
            "prep_waste": "Prep Waste",
            "overproduction": "Overproduction",
            "damaged": "Damaged",
            "other": "Other",
        }.get((reason or "other").lower(), (reason or "Other").replace("_", " ").title())

    def status_badge(label, bg, fg):
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            bgcolor=bg,
            border_radius=4,
            content=ft.Text(label, size=11, color=fg, weight=ft.FontWeight.W_600),
        )

    def reason_badge(reason):
        mapping = {
            "expired": (colors["RED"], colors["RED_BG"]),
            "spoiled": (colors["ORANGE"], colors["ORANGE_BG"]),
            "prep_waste": ("#B8860B", "#FFF4CC"),
            "overproduction": ("#1D4ED8", "#DBEAFE"),
            "damaged": (colors["MUTED"], colors["DIVIDER"]),
            "other": (colors["MUTED"], colors["DIVIDER"]),
        }
        fg, bg = mapping.get((reason or "other").lower(), (colors["MUTED"], colors["DIVIDER"]))
        return status_badge(reason_label(reason), bg, fg)

    def pill_button(label, period):
        active = selected_period[0] == period
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=14, vertical=10),
            border_radius=8,
            bgcolor=colors["ORANGE"] if active else colors["CARD_BG"],
            border=ft.Border.all(1, colors["ORANGE"] if active else colors["BORDER"]),
            ink=True,
            on_click=lambda e, p=period: set_period(p),
            content=ft.Text(label, size=13, color="#FFFFFF" if active else colors["TEXT"], weight=ft.FontWeight.W_600 if active else ft.FontWeight.W_400),
        )

    def download_csv(e):
        return None

    selected_period_row = ft.Row(
        spacing=8,
        controls=[
            pill_button("Daily", "daily"),
            pill_button("Weekly", "weekly"),
            pill_button("Monthly", "monthly"),
        ],
    )

    csv_button = ft.Button(
        "Download CSV",
        icon=ft.Icons.DOWNLOAD,
        on_click=download_csv,
        style=ft.ButtonStyle(
            bgcolor=colors["ORANGE"],
            color="#FFFFFF",
            elevation=0,
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.Padding.symmetric(horizontal=18, vertical=12),
        ),
    )

    top_controls = ft.Container(
        padding=ft.Padding.symmetric(horizontal=32, vertical=8),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[selected_period_row, csv_button],
        ),
    )

    metric_value_total = ft.Text("$0.00", size=28, weight=ft.FontWeight.W_700, color=colors["TEXT"])
    metric_value_weight = ft.Text("0.0 kg", size=28, weight=ft.FontWeight.W_700, color=colors["TEXT"])
    metric_value_eff = ft.Text("100.0%", size=28, weight=ft.FontWeight.W_700, color=colors["TEXT"])

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
                    ft.Row(spacing=8, controls=[ft.Icon(icon, size=16, color=colors["MUTED"]), ft.Text(title, size=14, weight=ft.FontWeight.W_600, color=colors["TEXT"])]),
                    value_control,
                    ft.Text(helper_text, size=12, color=colors["MUTED"]),
                ],
            ),
        )

    metrics_row = ft.Container(
        padding=ft.Padding.symmetric(horizontal=32, vertical=10),
        content=ft.Row(
            spacing=16,
            controls=[
                metric_card(ft.Icons.ATTACH_MONEY, "Total Financial Loss", metric_value_total, "Sum of cost estimate from waste logs"),
                metric_card(ft.Icons.STORAGE_OUTLINED, "Wasted Weight", metric_value_weight, "Sum of quantity wasted this period"),
                metric_card(ft.Icons.PERCENT, "Kitchen Efficiency %", metric_value_eff, "100 - avoidable waste percentage"),
            ],
        ),
    )

    trend_title = ft.Text("Waste Cost Trend", size=16, weight=ft.FontWeight.W_600, color=colors["TEXT"])
    reason_title = ft.Text("Waste by Reason", size=16, weight=ft.FontWeight.W_600, color=colors["TEXT"])
    top_items_title = ft.Text("Top Wasted Items by Cost", size=16, weight=ft.FontWeight.W_600, color=colors["TEXT"])
    insight_text = ft.Text("No waste logs found for this period.", size=14, color=colors["TEXT_SECONDARY"])

    trend_chart_host = ft.Container(expand=True)
    reason_chart_host = ft.Column(spacing=8)
    top_items_host = ft.Column(spacing=8)

    def build_card(title_control, subtitle, body_controls):
        return ft.Container(
            expand=True,
            bgcolor=colors["CARD_BG"],
            border=ft.Border.all(1, colors["BORDER"]),
            border_radius=12,
            padding=20,
            shadow=card_shadow(),
            content=ft.Column(
                spacing=12,
                controls=[
                    ft.Column(spacing=2, controls=[title_control, ft.Text(subtitle, size=12, color=colors["MUTED"])]),
                    *body_controls,
                ],
            ),
        )

    def format_money(value):
        return f"${float(value or 0):,.2f}"

    def reason_color(reason):
        return {
            "expired": colors["RED"],
            "spoiled": colors["ORANGE"],
            "prep_waste": "#B8860B",
            "overproduction": "#1D4ED8",
            "damaged": colors["MUTED"],
            "other": colors["MUTED"],
        }.get((reason or "other").lower(), colors["MUTED"])

    def rebuild_charts(rows, start_date, end_date):
        total_loss = sum(float(row.get("cost_estimate") or 0) for row in rows)
        total_weight = sum(float(row.get("qty_wasted") or 0) for row in rows)
        avoidable_loss = sum(float(row.get("cost_estimate") or 0) for row in rows if (row.get("reason") or "").lower() in {"prep_waste", "overproduction"})
        efficiency = max(0.0, 100.0 - ((avoidable_loss / total_loss) * 100.0 if total_loss else 0.0))

        metric_value_total.value = format_money(total_loss)
        metric_value_weight.value = f"{total_weight:.1f} kg"
        metric_value_eff.value = f"{efficiency:.1f}%"

        labels, values = _aggregate_by_day(rows, start_date, end_date)
        max_y = max(values) if values else 1
        max_y = max(max_y, 1)
        points = [fch.LineChartDataPoint(i, value) for i, value in enumerate(values)]
        trend_series = fch.LineChartData(points=points, stroke_width=2.5, color=colors["ORANGE"], curved=True, rounded_stroke_cap=True, below_line_gradient=ft.LinearGradient(begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1), colors=["#40E68A17", "#05E68A17"]))
        trend_chart = fch.LineChart(
            data_series=[trend_series],
            min_x=0,
            max_x=max(0, len(values) - 1),
            min_y=0,
            max_y=max_y * 1.2,
            height=220,
            expand=True,
            bgcolor="transparent",
            horizontal_grid_lines=fch.ChartGridLines(interval=max_y / 4 if max_y else 1, color=colors["CHART_GRID"], width=1),
            left_axis=fch.ChartAxis(show_labels=False, label_size=0),
            right_axis=fch.ChartAxis(show_labels=False, label_size=0),
            top_axis=fch.ChartAxis(show_labels=False, label_size=0),
            bottom_axis=fch.ChartAxis(labels=[fch.ChartAxisLabel(value=i, label=ft.Text(label, size=11, color=colors["MUTED"])) for i, label in enumerate(labels)], label_size=28),
            tooltip=fch.LineChartTooltip(bgcolor=colors["CARD_BG"]),
        )
        trend_chart_host.content = trend_chart

        reason_totals = _aggregate_reason_cost(rows)
        reason_chart_host.controls = []
        if reason_totals:
            for reason, cost in sorted(reason_totals.items(), key=lambda item: item[1], reverse=True):
                reason_chart_host.controls.append(
                    ft.Row(
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text(reason_label(reason), size=12, color=colors["TEXT_SECONDARY"], width=110),
                            ft.Container(expand=True, height=20, bgcolor=colors["DIVIDER"], border_radius=4, content=ft.Container(width=max(12, cost), bgcolor=reason_color(reason), border_radius=4)),
                            ft.Text(format_money(cost), size=12, color=colors["TEXT"], width=90, text_align=ft.TextAlign.RIGHT),
                        ],
                    )
                )
        else:
            reason_chart_host.controls = [ft.Text("No reason data available.", size=13, color=colors["MUTED"])]

        item_totals = _aggregate_item_cost(rows)
        top_items_host.controls = []
        if item_totals:
            for item_name, cost in item_totals.items():
                top_items_host.controls.append(
                    ft.Row(
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text(item_name, size=12, color=colors["TEXT_SECONDARY"], width=140),
                            ft.Container(expand=True, height=20, bgcolor=colors["DIVIDER"], border_radius=4, content=ft.Container(width=max(12, cost), bgcolor=colors["ORANGE"], border_radius=4)),
                            ft.Text(format_money(cost), size=12, color=colors["TEXT"], width=90, text_align=ft.TextAlign.RIGHT),
                        ],
                    )
                )
        else:
            top_items_host.controls = [ft.Text("No item data available.", size=13, color=colors["MUTED"])]

        top_reason = "No waste logs this period"
        top_reason_cost = 0.0
        if reason_totals:
            top_reason, top_reason_cost = max(reason_totals.items(), key=lambda item: item[1])
        insight_text.value = f"Highest-cost reason this period: {reason_label(top_reason)} at {format_money(top_reason_cost)}. Focus controls on this area to reduce kitchen loss."

    def set_period(period):
        selected_period[0] = period
        rebuild_page()

    def rebuild_page():
        search_text = (search_field.value or "").strip()
        rows, start_date, end_date = _fetch_rows(selected_period[0], search_text=search_text)
        rebuild_charts(rows, start_date, end_date)

        period_label_text.value = period_range_label(selected_period[0])
        period_buttons["daily"].bgcolor = colors["ORANGE"] if selected_period[0] == "daily" else colors["CARD_BG"]
        period_buttons["daily"].border = ft.Border.all(1, colors["ORANGE"] if selected_period[0] == "daily" else colors["BORDER"])
        period_buttons["weekly"].bgcolor = colors["ORANGE"] if selected_period[0] == "weekly" else colors["CARD_BG"]
        period_buttons["weekly"].border = ft.Border.all(1, colors["ORANGE"] if selected_period[0] == "weekly" else colors["BORDER"])
        period_buttons["monthly"].bgcolor = colors["ORANGE"] if selected_period[0] == "monthly" else colors["CARD_BG"]
        period_buttons["monthly"].border = ft.Border.all(1, colors["ORANGE"] if selected_period[0] == "monthly" else colors["BORDER"])

        for key, control in period_buttons.items():
            active = selected_period[0] == key
            control.content = ft.Text(key.title(), size=13, color="#FFFFFF" if active else colors["TEXT"], weight=ft.FontWeight.W_600 if active else ft.FontWeight.W_400)
            control.bgcolor = colors["ORANGE"] if active else colors["CARD_BG"]
            control.border = ft.Border.all(1, colors["ORANGE"] if active else colors["BORDER"])

        page.update()

    def make_period_button(label, key):
        button = ft.Container(
            padding=ft.Padding.symmetric(horizontal=14, vertical=10),
            border_radius=8,
            bgcolor=colors["ORANGE"] if selected_period[0] == key else colors["CARD_BG"],
            border=ft.Border.all(1, colors["ORANGE"] if selected_period[0] == key else colors["BORDER"]),
            ink=True,
            on_click=lambda e, p=key: set_period(p),
            content=ft.Text(label, size=13, color="#FFFFFF" if selected_period[0] == key else colors["TEXT"], weight=ft.FontWeight.W_600 if selected_period[0] == key else ft.FontWeight.W_400),
        )
        period_buttons[key] = button
        return button

    period_label_text = ft.Text(period_range_label(selected_period[0]), size=12, color=colors["MUTED"])

    controls_row = ft.Container(
        padding=ft.Padding.symmetric(horizontal=32, vertical=8),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(spacing=8, controls=[make_period_button("Daily", "daily"), make_period_button("Weekly", "weekly"), make_period_button("Monthly", "monthly"), period_label_text]),
                ft.Button(
                    "Download CSV",
                    icon=ft.Icons.DOWNLOAD,
                    on_click=lambda e: None,
                    style=ft.ButtonStyle(bgcolor=colors["ORANGE"], color="#FFFFFF", elevation=0, shape=ft.RoundedRectangleBorder(radius=8), padding=ft.Padding.symmetric(horizontal=18, vertical=12)),
                ),
            ],
        ),
    )

    search_field.on_change = lambda e: rebuild_page()

    summary_cards = ft.Container(
        padding=ft.Padding.symmetric(horizontal=32, vertical=10),
        content=ft.Row(
            spacing=16,
            controls=[
                metric_card(ft.Icons.ATTACH_MONEY, "Total Financial Loss", metric_value_total, "Sum of cost estimate from waste logs"),
                metric_card(ft.Icons.STORAGE_OUTLINED, "Wasted Weight", metric_value_weight, "Sum of quantity wasted this period"),
                metric_card(ft.Icons.PERCENT, "Kitchen Efficiency %", metric_value_eff, "100 - avoidable waste percentage"),
            ],
        ),
    )

    charts_row = ft.Container(
        padding=ft.Padding.symmetric(horizontal=32, vertical=10),
        content=ft.Row(
            spacing=16,
            controls=[
                build_card(trend_title, "Sum of waste cost over time", [trend_chart_host]),
                build_card(reason_title, "Cost grouped by reason", [reason_chart_host]),
            ],
        ),
    )

    items_row = ft.Container(
        padding=ft.Padding.symmetric(horizontal=32, vertical=10),
        content=ft.Row(
            spacing=16,
            controls=[build_card(top_items_title, "Top 5 items by waste cost", [top_items_host])],
        ),
    )

    insight_card = ft.Container(
        margin=ft.Margin(32, 16, 32, 16),
        bgcolor=colors["CARD_BG"],
        border=ft.Border.all(1, colors["BORDER"]),
        border_radius=12,
        shadow=card_shadow(),
        padding=ft.Padding.all(20),
        content=ft.Column(spacing=10, controls=[ft.Row(spacing=8, controls=[ft.Icon(ft.Icons.INSIGHTS_OUTLINED, size=16, color=colors["MUTED"]), ft.Text("Manager Insight", size=14, weight=ft.FontWeight.W_600, color=colors["TEXT"])]), ft.Divider(height=1, color=colors["DIVIDER"]), insight_text]),
    )

    footer = ft.Container(padding=ft.Padding.symmetric(horizontal=32, vertical=14), border=ft.Border(top=ft.BorderSide(1, colors["DIVIDER"])), content=ft.Text("© 2026 Kitchen Food Waste Tracker. All rights reserved.", size=12, color=colors["MUTED"]))

    content_area = ft.Container(
        expand=True,
        bgcolor=colors["BG"],
        content=ft.Column(expand=True, spacing=0, controls=[top_bar, title_block, controls_row, summary_cards, charts_row, items_row, insight_card, ft.Container(expand=True), footer]),
    )

    layout = ft.Row(expand=True, spacing=0, controls=[sidebar, content_area])

    rebuild_page()

    return ft.View(route="/reports", padding=0, spacing=0, bgcolor=colors["BG"], controls=[layout])
