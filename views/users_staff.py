import flet as ft
import sqlite3
from datetime import datetime

DB_PATH = "reg.db"

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


def _init_staff_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS staff_profiles (
            staff_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            full_name TEXT NOT NULL,
            functional_role TEXT NOT NULL,
            section_shift TEXT,
            phone TEXT,
            hired_date TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def _get_users():
    """Fetch all users from reg.db"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, username, email FROM users ORDER BY id DESC")
    base_rows = [dict(r) for r in cur.fetchall()]
    
    try:
        cur.execute("SELECT id, role, is_active, created_at FROM users")
        optional_data = {r["id"]: {"role": r["role"], "is_active": r["is_active"], "created_at": r["created_at"]} for r in cur.fetchall()}
    except Exception:
        optional_data = {}
    
    for row in base_rows:
        row_id = row["id"]
        if row_id in optional_data:
            row.update(optional_data[row_id])
        else:
            row["role"] = "chef"
            row["is_active"] = 1
            row["created_at"] = ""
    
    conn.close()
    return base_rows


def _get_staff_profiles():
    """Fetch all staff profiles"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM staff_profiles ORDER BY staff_id ASC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def _add_user(username, email, password, role):
    """Add a new user to users table"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, email, password, role, is_active) VALUES (?, ?, ?, ?, ?)",
            (username, email, password, role, 1),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return "Username or email already exists."
    conn.close()
    return None


def _update_user(user_id, email, role):
    """Update user email and role"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE users SET email=?, role=? WHERE id=?", (email, role, user_id))
    conn.commit()
    conn.close()


def _toggle_user_active(user_id, is_active):
    """Toggle user active status"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_active=? WHERE id=?", (1 if is_active else 0, user_id))
    conn.commit()
    conn.close()


def _add_staff_profile(payload):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO staff_profiles (user_id, full_name, functional_role, section_shift, phone, hired_date) VALUES (?, ?, ?, ?, ?, ?)",
            (payload.get("user_id"), payload.get("full_name"), payload.get("functional_role"), payload.get("section_shift"), payload.get("phone"), payload.get("hired_date")),
        )
        conn.commit()
    except Exception:
        conn.close()
        return "Error"
    conn.close()
    return None


def _update_staff_profile(staff_id, payload):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "UPDATE staff_profiles SET user_id=?, full_name=?, functional_role=?, section_shift=?, phone=?, hired_date=? WHERE staff_id=?",
        (payload.get("user_id"), payload.get("full_name"), payload.get("functional_role"), payload.get("section_shift"), payload.get("phone"), payload.get("hired_date"), staff_id),
    )
    conn.commit()
    conn.close()


def users_staff_view(page: ft.Page) -> ft.View:
    _init_staff_db()
    colors = LIGHT.copy() if page.theme_mode == ft.ThemeMode.LIGHT else DARK.copy()
    role = page.session.store.get("role") or "chef"

    current_tab = [0]  # 0 = Staff Profiles, 1 = System Users
    search_value = [""]

    username = page.session.store.get("username") or "User"
    initials = username[:2].upper()

    def card_shadow():
        return ft.BoxShadow(blur_radius=12, spread_radius=0, color=colors["SHADOW"], offset=ft.Offset(0, 2))

    # ───────────────────── SIDEBAR ─────────────────────
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

    def build_nav_item(icon, label, active=False, route=None):
        text_color = colors["ORANGE"] if active else colors["SIDEBAR_TEXT"]
        icon_color = colors["ORANGE"] if active else colors["SIDEBAR_ICON"]
        bg = colors["SIDEBAR_ACTIVE_BG"] if active else "transparent"
        weight = ft.FontWeight.W_600 if active else ft.FontWeight.W_400

        row_controls = [ft.Icon(icon, size=20, color=icon_color), ft.Text(label, size=14, color=text_color, weight=weight, expand=True)]
        if active:
            row_controls.append(ft.Icon(ft.Icons.CHEVRON_RIGHT, size=18, color=icon_color))

        def nav_click(e, r=route):
            if r:
                page.go(r)

        return ft.Container(padding=ft.Padding.symmetric(horizontal=14, vertical=10), bgcolor=bg, border_radius=8, content=ft.Row(spacing=12, controls=row_controls), ink=True, on_click=nav_click if route else None)

    nav_column = ft.Column(spacing=2, controls=[build_nav_item(i, l, a, r) for i, l, a, r in nav_items_data])

    sign_out = ft.Container(padding=ft.Padding.symmetric(horizontal=14, vertical=10), ink=True, on_click=lambda e: (page.session.store.clear(), page.go("/")), content=ft.Row(spacing=12, controls=[ft.Icon(ft.Icons.LOGOUT, size=20, color=colors["SIDEBAR_TEXT"]), ft.Text("Sign Out", size=14, color=colors["SIDEBAR_TEXT"])]))

    sidebar = ft.Container(width=240, bgcolor=colors["SIDEBAR_BG"], border=ft.Border(right=ft.BorderSide(1, colors["BORDER"])), padding=ft.Padding.only(top=20, bottom=12, left=12, right=12), content=ft.Column(expand=True, spacing=0, controls=[ft.Container(padding=ft.Padding.only(left=6, bottom=24), content=ft.Row(spacing=10, controls=[logo_icon, logo_text])), nav_column, ft.Container(expand=True), ft.Divider(height=1, color=colors["DIVIDER"]), sign_out]))

    # ───────────────────── TOP BAR ─────────────────────
    top_search = ft.TextField(hint_text="Search users or staff...", width=420, height=42, border_radius=10, border_color=colors["SEARCH_BORDER"], focused_border_color=colors["ORANGE"], bgcolor=colors["SEARCH_BG"], prefix_icon=ft.Icons.SEARCH, content_padding=ft.Padding.symmetric(horizontal=14, vertical=8), text_size=14, color=colors["TEXT"], cursor_color=colors["ORANGE"], on_change=lambda e: (search_value.__setitem__(0, e.control.value), refresh_view()))

    user_avatar = ft.Container(width=38, height=38, bgcolor=colors["AVATAR_BG"], border_radius=19, alignment=ft.Alignment(0, 0), content=ft.Text(initials, size=14, weight=ft.FontWeight.W_600, color=colors["ORANGE"]))

    btn_new_user = ft.Button("New User", icon=ft.Icons.PERSON_ADD, on_click=lambda e: open_new_user_dialog(), style=ft.ButtonStyle(bgcolor=colors["ORANGE"], color="#FFFFFF", elevation=0, shape=ft.RoundedRectangleBorder(radius=8)))

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
                                ft.Text("Manager" if role == "manager" else role.replace("_", " ").title(), size=12, color=colors["MUTED"]),
                            ],
                        ),
                        user_avatar,
                        btn_new_user,
                    ],
                ),
            ],
        ),
    )

    # ───────────────────── CONTENT HEADER ─────────────────────
    content_header = ft.Container(
        padding=ft.Padding.only(left=32, right=32, top=24, bottom=8),
        content=ft.Column(
            spacing=4,
            controls=[
                ft.Text("Users & Staff", size=26, weight=ft.FontWeight.W_700, color=colors["TEXT"]),
                ft.Text("Manage staff profiles and system users.", size=14, color=colors["MUTED"]),
            ],
        ),
    )

    # ───────────────────── TABS ─────────────────────
    def build_tab_chip(label, idx):
        active = current_tab[0] == idx
        return ft.Container(
            padding=ft.Padding.only(left=20, right=20, top=14, bottom=10),
            border=ft.Border(bottom=ft.BorderSide(2, colors["ORANGE"] if active else "transparent")),
            ink=True,
            on_click=lambda e, i=idx: switch_tab(i),
            content=ft.Text(label, size=14, color=colors["ORANGE"] if active else colors["MUTED"], weight=ft.FontWeight.W_600 if active else ft.FontWeight.W_400),
        )

    tab_headers = ft.Row(spacing=0, controls=[build_tab_chip("Staff Profiles", 0), build_tab_chip("System Users", 1)])

    # Body containers
    staff_columns = ft.Row(spacing=24)
    users_table_col = ft.Column(spacing=0)

    def refresh_view():
        if current_tab[0] == 0:
            build_staff_profiles()
        else:
            build_system_users()
        page.update()

    def switch_tab(idx):
        current_tab[0] = idx
        tab_headers.controls[:] = [build_tab_chip("Staff Profiles", 0), build_tab_chip("System Users", 1)]
        refresh_view()

    # ───────────────────── STAFF PROFILES TAB ─────────────────────
    def build_staff_profiles():
        staff_columns.controls.clear()
        rows = _get_staff_profiles()
        users = _get_users()
        user_map = {u["id"]: u for u in users}

        # Group staff by user role
        groups = {"Chef/Prep": [], "Inventory Staff": [], "Manager": [], "Unlinked": []}
        for s in rows:
            user_id = s.get("user_id")
            if user_id and user_id in user_map:
                user_role = user_map[user_id].get("role", "chef")
                # Map role values
                if user_role == "chef":
                    role_key = "Chef/Prep"
                elif user_role == "inventory_staff":
                    role_key = "Inventory Staff"
                elif user_role == "manager":
                    role_key = "Manager"
                else:
                    role_key = "Chef/Prep"
                groups[role_key].append(s)
            else:
                groups["Unlinked"].append(s)

        for title, items in [("Chefs", groups["Chef/Prep"]), ("Inventory Staff", groups["Inventory Staff"]), ("Managers", groups["Manager"]), ("Unlinked", groups["Unlinked"])]:
            if items or title != "Unlinked":  # Always show first 3 groups, only show Unlinked if has items
                staff_columns.controls.append(build_staff_group(title, items))

    def build_staff_group(title, items):
        header = ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text(f"{title}", size=16, weight=ft.FontWeight.W_600, color=colors["TEXT"]), ft.Text(f"{len(items)}", size=13, color=colors["MUTED"])])
        cards = []
        for it in items:
            name = it.get("full_name")
            phone = it.get("phone") or ""
            shift = it.get("section_shift") or ""
            initials_local = (name[:2] if name else "SM").upper()
            card = ft.Container(
                width=300,
                padding=ft.Padding.all(12),
                bgcolor=colors["CARD_BG"],
                border_radius=12,
                shadow=card_shadow(),
                ink=True,
                on_click=lambda e, s=it: open_edit_staff_dialog(s),
                content=ft.Row(
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(width=44, height=44, bgcolor=colors["AVATAR_BG"], border_radius=22, alignment=ft.Alignment(0, 0), content=ft.Text(initials_local, size=14, weight=ft.FontWeight.W_600, color=colors["ORANGE"])),
                        ft.Column(spacing=2, controls=[ft.Text(name, size=14, weight=ft.FontWeight.W_600, color=colors["TEXT"]), ft.Text(phone, size=12, color=colors["MUTED"]), ft.Text(shift, size=12, color=colors["MUTED"])]),
                    ],
                ),
            )
            cards.append(card)
        col = ft.Column(spacing=12, controls=[header] + cards)
        return col

    # ───────────────────── SYSTEM USERS TAB ─────────────────────
    def build_system_users():
        users_table_col.controls.clear()
        users = _get_users()

        header_row = ft.Row(
            spacing=12,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Container(expand=1.5, content=ft.Text("Username", size=12, weight=ft.FontWeight.W_600, color=colors["MUTED"])),
                ft.Container(expand=2, content=ft.Text("Email", size=12, weight=ft.FontWeight.W_600, color=colors["MUTED"])),
                ft.Container(expand=1, content=ft.Text("Role", size=12, weight=ft.FontWeight.W_600, color=colors["MUTED"])),
                ft.Container(expand=1, content=ft.Text("Status", size=12, weight=ft.FontWeight.W_600, color=colors["MUTED"])),
                ft.Container(expand=0.5, content=ft.Text("Actions", size=12, weight=ft.FontWeight.W_600, color=colors["MUTED"])),
            ],
        )

        header_container = ft.Container(
            bgcolor=colors["TABLE_HEADER_BG"],
            padding=ft.Padding.symmetric(horizontal=20, vertical=12),
            border=ft.Border(bottom=ft.BorderSide(1, colors["DIVIDER"])),
            content=header_row,
        )

        rows = [header_container]
        for u in users:
            status = "Active" if u.get("is_active") in (1, "1", True, None) else "Inactive"
            is_active = u.get("is_active") in (1, "1", True, None)

            def make_edit(uu=u):
                return lambda e: open_edit_user_dialog(uu)

            def make_toggle(uu=u, active=is_active):
                return lambda e: (
                    _toggle_user_active(uu.get("id"), not active),
                    refresh_view(),
                )

            row_container = ft.Container(
                padding=ft.Padding.symmetric(horizontal=20, vertical=12),
                border=ft.Border(bottom=ft.BorderSide(1, colors["DIVIDER"])),
                content=ft.Row(
                    spacing=12,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Container(expand=1.5, content=ft.Text(u.get("username"), size=13, color=colors["TEXT"])),
                        ft.Container(expand=2, content=ft.Text(u.get("email"), size=13, color=colors["MUTED"])),
                        ft.Container(expand=1, content=ft.Text(str(u.get("role") or "chef").replace("_", " ").title(), size=13, color=colors["MUTED"])),
                        ft.Container(expand=1, content=ft.Text(status, size=13, color=colors["MUTED"])),
                        ft.Container(
                            expand=0.5,
                            content=ft.Row(
                                spacing=4,
                                controls=[
                                    ft.IconButton(ft.Icons.EDIT, icon_size=18, on_click=make_edit()),
                                    ft.IconButton(
                                        ft.Icons.PERSON_OFF if is_active else ft.Icons.PERSON,
                                        icon_size=18,
                                        on_click=make_toggle(),
                                        tooltip="Deactivate" if is_active else "Activate",
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
            )
            rows.append(row_container)

        users_table_col.controls[:] = rows

    # ───────────────────── DIALOGS ─────────────────────
    def open_new_user_dialog():
        username_field = ft.TextField(label="Username", width=420)
        email_field = ft.TextField(label="Email", width=420)
        password_field = ft.TextField(label="Password", password=True, can_reveal_password=True, width=420)
        confirm_pwd_field = ft.TextField(label="Confirm Password", password=True, can_reveal_password=True, width=420)
        role_dropdown = ft.Dropdown(
            label="Role",
            value="chef",
            options=[
                ft.DropdownOption(key="chef", text="Chef / Prep"),
                ft.DropdownOption(key="inventory_staff", text="Inventory Staff"),
                ft.DropdownOption(key="manager", text="Manager"),
            ],
            width=420,
        )
        error_text = ft.Text("", size=12, color=colors["RED"], visible=False)

        def on_create(e):
            if not username_field.value or not email_field.value or not password_field.value:
                error_text.value = "All fields required."
                error_text.visible = True
                page.update()
                return
            if password_field.value != confirm_pwd_field.value:
                error_text.value = "Passwords do not match."
                error_text.visible = True
                page.update()
                return

            err = _add_user(username_field.value, email_field.value, password_field.value, role_dropdown.value)
            if err:
                error_text.value = err
                error_text.visible = True
                page.update()
            else:
                page.pop_dialog()
                refresh_view()

        def on_cancel(e):
            page.pop_dialog()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                spacing=10,
                controls=[
                    ft.Icon(ft.Icons.PERSON_ADD, color=colors["ORANGE"], size=22),
                    ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text("Create New User", size=18, weight=ft.FontWeight.W_600, color=colors["TEXT"]),
                            ft.Text("Add a new system user", size=12, color=colors["MUTED"]),
                        ],
                    ),
                ],
            ),
            content=ft.Container(
                width=480,
                content=ft.Column(
                    spacing=12,
                    controls=[username_field, email_field, password_field, confirm_pwd_field, role_dropdown, error_text],
                ),
            ),
            actions=[
                ft.TextButton("Cancel", on_click=on_cancel, style=ft.ButtonStyle(color=colors["MUTED"])),
                ft.Button("Create User", on_click=on_create, style=ft.ButtonStyle(bgcolor=colors["ORANGE"], color="#FFFFFF", elevation=0, shape=ft.RoundedRectangleBorder(radius=8))),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=colors["CARD_BG"],
            shape=ft.RoundedRectangleBorder(radius=12),
        )
        page.dialog = dlg
        page.show_dialog(dlg)

    def open_edit_user_dialog(user):
        email_field = ft.TextField(label="Email", value=user.get("email"), width=420)
        role_dropdown = ft.Dropdown(
            label="Role",
            value=user.get("role", "chef"),
            options=[
                ft.DropdownOption(key="chef", text="Chef / Prep"),
                ft.DropdownOption(key="inventory_staff", text="Inventory Staff"),
                ft.DropdownOption(key="manager", text="Manager"),
            ],
            width=420,
        )

        def on_save(e):
            _update_user(user.get("id"), email_field.value, role_dropdown.value)
            page.pop_dialog()
            refresh_view()

        def on_cancel(e):
            page.pop_dialog()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                spacing=10,
                controls=[
                    ft.Icon(ft.Icons.EDIT, color=colors["ORANGE"], size=22),
                    ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text("Edit User", size=18, weight=ft.FontWeight.W_600, color=colors["TEXT"]),
                            ft.Text(f"Update {user.get('username')}", size=12, color=colors["MUTED"]),
                        ],
                    ),
                ],
            ),
            content=ft.Container(width=480, content=ft.Column(spacing=12, controls=[email_field, role_dropdown])),
            actions=[
                ft.TextButton("Cancel", on_click=on_cancel, style=ft.ButtonStyle(color=colors["MUTED"])),
                ft.Button("Update User", on_click=on_save, style=ft.ButtonStyle(bgcolor=colors["ORANGE"], color="#FFFFFF", elevation=0, shape=ft.RoundedRectangleBorder(radius=8))),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=colors["CARD_BG"],
            shape=ft.RoundedRectangleBorder(radius=12),
        )
        page.dialog = dlg
        page.show_dialog(dlg)

    def open_edit_staff_dialog(staff):
        full_name = ft.TextField(label="Full Name", value=staff.get("full_name", ""), width=420)
        functional_role = ft.Dropdown(
            label="Functional Role",
            value=staff.get("functional_role", "Chef/Prep"),
            options=[
                ft.DropdownOption(key="Chef/Prep", text="Chef/Prep"),
                ft.DropdownOption(key="Inventory Staff", text="Inventory Staff"),
                ft.DropdownOption(key="Manager", text="Manager"),
            ],
            width=420,
        )
        section_shift = ft.TextField(label="Section / Shift", value=staff.get("section_shift", ""), width=420)
        phone = ft.TextField(label="Phone", value=staff.get("phone", ""), width=420)
        hired_date = ft.TextField(label="Hired Date (YYYY-MM-DD)", value=staff.get("hired_date", ""), width=420)

        users = _get_users()
        user_options = [ft.DropdownOption(key="", text="(Unlinked)")] + [ft.DropdownOption(key=str(u.get("id")), text=u.get("username")) for u in users]
        linked_user = str(staff.get("user_id")) if staff and staff.get("user_id") else ""
        link_user = ft.Dropdown(label="Link User Account", value=linked_user, options=user_options, width=420)

        def on_save(e):
            payload = {
                "user_id": int(link_user.value) if link_user.value else None,
                "full_name": full_name.value,
                "functional_role": functional_role.value,
                "section_shift": section_shift.value,
                "phone": phone.value,
                "hired_date": hired_date.value or None,
            }
            if staff and staff.get("staff_id"):
                _update_staff_profile(staff.get("staff_id"), payload)
            else:
                _add_staff_profile(payload)
            page.pop_dialog()
            refresh_view()

        def on_cancel(e):
            page.pop_dialog()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                spacing=10,
                controls=[
                    ft.Icon(ft.Icons.PERSON, color=colors["ORANGE"], size=22),
                    ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text("Staff Profile", size=18, weight=ft.FontWeight.W_600, color=colors["TEXT"]),
                            ft.Text("Edit staff member", size=12, color=colors["MUTED"]),
                        ],
                    ),
                ],
            ),
            content=ft.Container(
                width=480,
                content=ft.Column(
                    spacing=12,
                    controls=[full_name, functional_role, section_shift, phone, hired_date, link_user, ft.Text("Linking a staff profile to an existing user account allows staff actions to be attributed to that user.", size=12, color=colors["MUTED"])],
                ),
            ),
            actions=[
                ft.TextButton("Cancel", on_click=on_cancel, style=ft.ButtonStyle(color=colors["MUTED"])),
                ft.Button("Save Staff Profile", on_click=on_save, style=ft.ButtonStyle(bgcolor=colors["ORANGE"], color="#FFFFFF", elevation=0, shape=ft.RoundedRectangleBorder(radius=8))),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=colors["CARD_BG"],
            shape=ft.RoundedRectangleBorder(radius=12),
        )
        page.dialog = dlg
        page.show_dialog(dlg)

    # Initial build
    build_staff_profiles()
    build_system_users()

    content = ft.Column(
        spacing=12,
        controls=[
            content_header,
            tab_headers,
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=32, vertical=12),
                content=ft.Column(
                    spacing=12,
                    controls=[
                        staff_columns if current_tab[0] == 0 else users_table_col,
                    ],
                ),
            ),
        ],
    )

    layout = ft.Row(spacing=0, controls=[sidebar, ft.Column(expand=True, controls=[top_bar, content])])

    return ft.View(route="/users", padding=0, spacing=0, bgcolor=colors["BG"], controls=[layout])
