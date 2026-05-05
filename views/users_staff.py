import flet as ft
import sqlite3
import requests

DB_PATH = "reg.db"
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


def _get_users(search="", role_filter="All Roles"):
    try:
        params = {}
        if search:
            params["search"] = search
        if role_filter != "All Roles":
            params["role"] = role_filter
        response = requests.get(f"{API_URL}/users", params=params, timeout=5)
        if response.status_code == 200:
            return response.json().get("data", [])
    except requests.exceptions.RequestException:
        pass
    return []


def _add_user(username, email, password, role):
    try:
        response = requests.post(
            f"{API_URL}/users",
            json={"username": username, "email": email, "password": password, "role": role},
            timeout=5,
        )
        data = response.json()
        if data.get("error"):
            return data["error"]
    except requests.exceptions.RequestException:
        return "Cannot reach API server."
    return None


def _update_user(user_id, email, role):
    try:
        requests.put(f"{API_URL}/users/{user_id}", json={"email": email, "role": role}, timeout=5)
    except requests.exceptions.RequestException:
        return "Cannot reach API server."


def _toggle_user_active(user_id, is_active):
    try:
        response = requests.patch(f"{API_URL}/users/{user_id}/active", params={"is_active": is_active}, timeout=5)
        if response.status_code >= 400:
            data = response.json() if response.content else {}
            return data.get("detail") or data.get("error") or "Cannot update user status."
    except requests.exceptions.RequestException:
        return "Cannot reach API server."
    return None
def _delete_user(user_id):
    try:
        requests.delete(f"{API_URL}/users/{user_id}", timeout=5)
    except requests.exceptions.RequestException:
        return "Cannot reach API server."


def _get_role_label(r):
    m = {"chef": "Kitchen Staff", "inventory_staff": "Inventory Manager", "manager": "General Manager"}
    return m.get(r, "Kitchen Staff")


def users_staff_view(page: ft.Page) -> ft.View:
    colors = LIGHT.copy() if page.theme_mode == ft.ThemeMode.LIGHT else DARK.copy()
    current_username = page.session.store.get("username") or "User"
    current_role = page.session.store.get("role") or "chef"
    current_user_id = page.session.store.get("user_id")

    search_value = [""]

    def card_shadow():
        return ft.BoxShadow(blur_radius=12, spread_radius=0, color=colors["SHADOW"], offset=ft.Offset(0, 2))

    # Sidebar
    logo_icon = ft.Image(src="assets/logo.png", width=36, height=36, fit=ft.BoxFit.CONTAIN)
    logo_text = ft.Text("Kitchen Food Waste", size=15, weight=ft.FontWeight.W_700, color=colors["TEXT"], overflow=ft.TextOverflow.ELLIPSIS, max_lines=1)

    nav_items_data = [
        (ft.Icons.SPACE_DASHBOARD_OUTLINED, "Dashboard", page.route == "/dashboard", "/dashboard"),
        (ft.Icons.INVENTORY_2_OUTLINED, "Inventory", page.route == "/inventory", "/inventory"),
    ]
    if current_role in ("inventory_staff", "manager"):
        nav_items_data.extend([
            (ft.Icons.TIMER_OUTLINED, "Expiry Monitor", page.route == "/expiry", "/expiry"),
            (ft.Icons.RECEIPT_LONG_OUTLINED, "Waste Logs", page.route == "/waste-logs", "/waste-logs"),
        ])
    if current_role == "manager":
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

    # Top bar
    initials = (current_username[:2] if current_username else "US").upper()
    user_avatar = ft.Container(width=38, height=38, bgcolor=colors["AVATAR_BG"], border_radius=19, alignment=ft.Alignment(0, 0), content=ft.Text(initials, size=14, weight=ft.FontWeight.W_600, color=colors["ORANGE"]))

    top_bar = ft.Container(padding=ft.Padding.symmetric(horizontal=32, vertical=14), border=ft.Border(bottom=ft.BorderSide(1, colors["BORDER"])), bgcolor=colors["CARD_BG"], content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[ft.Row(spacing=0, controls=[]), ft.Container(ink=True, on_click=lambda e: page.go("/account"), border_radius=10, padding=ft.Padding.symmetric(horizontal=4, vertical=4), content=ft.Row(spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[ft.Column(spacing=0, horizontal_alignment=ft.CrossAxisAlignment.END, controls=[ft.Text(current_username, size=14, weight=ft.FontWeight.W_600, color=colors["TEXT"]), ft.Text(_get_role_label(current_role), size=12, color=colors["MUTED"])]), user_avatar]))]))

    # Content header
    content_header = ft.Container(padding=ft.Padding.only(left=32, right=32, top=24, bottom=8), content=ft.Column(spacing=4, controls=[ft.Text("Users", size=26, weight=ft.FontWeight.W_700, color=colors["TEXT"]), ft.Text("Manage system users and accounts.", size=14, color=colors["MUTED"]) ]))

    # Filters and New User button (inside content)
    search_field = ft.TextField(hint_text="Search by username or email...", width=360, height=42, border_radius=10, border_color=colors["SEARCH_BORDER"], focused_border_color=colors["ORANGE"], bgcolor=colors["SEARCH_BG"], prefix_icon=ft.Icons.SEARCH, content_padding=ft.Padding.symmetric(horizontal=14, vertical=8), text_size=14, color=colors["TEXT"], cursor_color=colors["ORANGE"]) 

    # Role filter removed (non-functional)

    btn_new_user = ft.Button("+ New User", icon=ft.Icons.PERSON_ADD, on_click=lambda e: page.go('/register'), style=ft.ButtonStyle(bgcolor=colors["ORANGE"], color="#FFFFFF", elevation=0, shape=ft.RoundedRectangleBorder(radius=8)))

    # Event handlers (defined after controls exist)
    def _on_search_change(e):
        search_value[0] = e.control.value
        refresh_grid()

    # Role filter handler removed

    def _on_new_user_click(e):
        # Deprecated: users now created via the registration page
        page.go('/register')

    search_field.on_change = _on_search_change
    # role_dropdown removed
    btn_new_user.on_click = _on_new_user_click

    filter_row = ft.Container(padding=ft.Padding.symmetric(horizontal=32, vertical=12), content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[ft.Row(spacing=12, controls=[search_field]), btn_new_user]))

    # Grid
    users_grid = ft.GridView(expand=True, runs_count=3, spacing=20, run_spacing=20)

    def refresh_grid():
        users_grid.controls.clear()
        users = _get_users(search=search_value[0])
        if not users:
            users_grid.controls.append(ft.Container(expand=True, alignment=ft.Alignment(0, 0), content=ft.Text("No users found", size=14, color=colors["MUTED"])))
        else:
            for u in users:
                users_grid.controls.append(build_user_card(u))
        page.update()

    def build_user_card(u):
        uid = u.get("id")
        username = u.get("username")
        email = u.get("email")
        role = u.get("role") or "chef"
        is_active = u.get("is_active") in (1, "1", True)
        initials = (username[:2] if username else "US").upper()
        role_label = _get_role_label(role)
        status_text = "Active" if is_active else "Inactive"
        status_color = colors["GREEN"] if is_active else colors["RED"]

        # Manager hierarchy
        # Hide buttons entirely for head manager account
        if username == "manager":
            action_buttons = []
        else:
            can_edit = False
            if current_role == "manager":
                if current_username == "manager":
                    # head manager can edit everyone except head manager (already filtered)
                    can_edit = True
                else:
                    # regular manager cannot edit other managers
                    can_edit = (role != "manager")
            # other roles cannot access this page normally
            action_buttons = []
            if can_edit:
                action_buttons = [
                    ft.IconButton(ft.Icons.EDIT, icon_size=18, tooltip="Edit", on_click=lambda e, uu=u: try_open_edit(uu)),
                    ft.IconButton(ft.Icons.PERSON_OFF if is_active else ft.Icons.PERSON, icon_size=18, tooltip=("Deactivate" if is_active else "Activate"), on_click=lambda e, uid=uid, active=is_active: try_toggle_active(uid, active)),
                ]

        card = ft.Container(bgcolor=colors["CARD_BG"], border=ft.Border.all(1, colors["BORDER"]), border_radius=12, padding=16, shadow=card_shadow(), content=ft.Column(spacing=8, controls=[ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Container(width=40, height=40, bgcolor=colors["AVATAR_BG"], border_radius=20, alignment=ft.Alignment(0, 0), content=ft.Text(initials, size=13, weight=ft.FontWeight.W_600, color=colors["ORANGE"])), ft.Row(spacing=4, controls=action_buttons)]), ft.Text(username, size=14, weight=ft.FontWeight.W_600, color=colors["TEXT"]), ft.Text(email or "", size=12, color=colors["MUTED"]), ft.Row(spacing=8, controls=[ft.Container(padding=ft.Padding.symmetric(horizontal=10, vertical=4), bgcolor=colors["ORANGE_BG"], border_radius=6, content=ft.Text(role_label, size=11, color=colors["ORANGE"], weight=ft.FontWeight.W_600)), ft.Container(padding=ft.Padding.symmetric(horizontal=10, vertical=4), bgcolor=colors["GREEN_BG"] if is_active else colors["RED_BG"], border_radius=6, content=ft.Text(status_text, size=11, color=status_color, weight=ft.FontWeight.W_600))])]))
        return card

    def try_open_edit(user):
        # Check manager hierarchy
        if user.get("username") == "manager":
            page.snack_bar = ft.SnackBar(ft.Text("The head manager account cannot be modified.", color="#FFFFFF"))
            page.snack_bar.open = True
            page.update()
            return
        if current_role == "manager" and current_username != "manager" and user.get("role") == "manager":
            page.snack_bar = ft.SnackBar(ft.Text("Only the head manager can modify manager accounts", color="#FFFFFF"))
            page.snack_bar.open = True
            page.update()
            return
        open_edit_user_dialog(user)

    def try_toggle_active(user_id, is_active):
        # Lookup user
        try:
            response = requests.get(f"{API_URL}/users/{user_id}", timeout=5)
            row = response.json() if response.status_code == 200 else None
        except requests.exceptions.RequestException:
            row = None
        if not row:
            return
        target_username, target_role = row.get("username"), row.get("role")
        if target_username == "manager":
            page.snack_bar = ft.SnackBar(ft.Text("The head manager account cannot be modified.", color="#FFFFFF"))
            page.snack_bar.open = True
            page.update()
            return
        if current_role == "manager" and current_username != "manager" and target_role == "manager":
            page.snack_bar = ft.SnackBar(ft.Text("Only the head manager can modify manager accounts", color="#FFFFFF"))
            page.snack_bar.open = True
            page.update()
            return
        err = _toggle_user_active(user_id, not is_active)
        if err:
            page.snack_bar = ft.SnackBar(ft.Text(err, color="#FFFFFF"))
            page.snack_bar.open = True
            page.update()
            return
        refresh_grid()

    def try_delete_user(user):
        if user.get("username") == "manager":
            page.snack_bar = ft.SnackBar(ft.Text("The head manager account cannot be deleted.", color="#FFFFFF"))
            page.snack_bar.open = True
            page.update()
            return
        if current_username == user.get("username"):
            page.snack_bar = ft.SnackBar(ft.Text("You cannot delete your own account.", color="#FFFFFF"))
            page.snack_bar.open = True
            page.update()
            return
        if current_role == "manager" and current_username != "manager" and user.get("role") == "manager":
            page.snack_bar = ft.SnackBar(ft.Text("Only the head manager can delete manager accounts.", color="#FFFFFF"))
            page.snack_bar.open = True
            page.update()
            return
        _delete_user(user.get("id"))
        refresh_grid()

    def open_delete_confirm_dialog(user):
        def on_confirm(e):
            page.pop_dialog()
            try_delete_user(user)

        def on_cancel(e):
            page.pop_dialog()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete User", size=18, weight=ft.FontWeight.W_600, color=colors["TEXT"]),
            content=ft.Container(
                width=420,
                content=ft.Text(
                    "Are you sure you want to delete this user? It will be deleted permanently.",
                    size=14,
                    color=colors["TEXT"],
                ),
            ),
            actions=[
                ft.TextButton("Cancel", on_click=on_cancel, style=ft.ButtonStyle(color=colors["MUTED"])),
                ft.Button(
                    "Delete Permanently",
                    on_click=on_confirm,
                    style=ft.ButtonStyle(
                        bgcolor=colors["RED"],
                        color="#FFFFFF",
                        elevation=0,
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=colors["CARD_BG"],
            shape=ft.RoundedRectangleBorder(radius=12),
        )
        page.show_dialog(dlg)

    # Dialogs
    def open_new_user_dialog():
        username_field = ft.TextField(label="Username", width=420)
        email_field = ft.TextField(label="Email", width=420)
        password_field = ft.TextField(label="Password", password=True, can_reveal_password=True, width=420)
        confirm_pwd_field = ft.TextField(label="Confirm Password", password=True, can_reveal_password=True, width=420)
        role_dropdown = ft.Dropdown(label="Role", value="chef", options=[ft.DropdownOption("chef", "Kitchen Staff"), ft.DropdownOption("inventory_staff", "Inventory Manager"), ft.DropdownOption("manager", "General Manager")], width=420)
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
                refresh_grid()

        def on_cancel(e):
            page.pop_dialog()

        dlg = ft.AlertDialog(modal=True, title=ft.Row(spacing=10, controls=[ft.Icon(ft.Icons.PERSON_ADD, color=colors["ORANGE"], size=22), ft.Column(spacing=2, controls=[ft.Text("Create New User", size=18, weight=ft.FontWeight.W_600, color=colors["TEXT"]), ft.Text("Add a new system user", size=12, color=colors["MUTED"])])]), content=ft.Container(width=480, content=ft.Column(spacing=12, controls=[username_field, email_field, password_field, confirm_pwd_field, role_dropdown, error_text])), actions=[ft.TextButton("Cancel", on_click=on_cancel, style=ft.ButtonStyle(color=colors["MUTED"])), ft.Button("Create User", on_click=on_create, style=ft.ButtonStyle(bgcolor=colors["ORANGE"], color="#FFFFFF", elevation=0, shape=ft.RoundedRectangleBorder(radius=8)))], actions_alignment=ft.MainAxisAlignment.END, bgcolor=colors["CARD_BG"], shape=ft.RoundedRectangleBorder(radius=12))
        page.show_dialog(dlg)

    def open_edit_user_dialog(user):
        # Username display only
        username_field = ft.TextField(label="Username", value=user.get("username"), read_only=True, width=420)
        email_field = ft.TextField(label="Email", value=user.get("email"), width=420)
        role_dropdown = ft.Dropdown(label="Role", value=user.get("role", "chef"), options=[ft.DropdownOption("chef", "Kitchen Staff"), ft.DropdownOption("inventory_staff", "Inventory Manager"), ft.DropdownOption("manager", "General Manager")], width=420)

        def on_save(e):
            # Manager hierarchy enforced at caller
            _update_user(user.get("id"), email_field.value, role_dropdown.value)
            page.pop_dialog()
            refresh_grid()

        def on_cancel(e):
            page.pop_dialog()

        def on_delete(e):
            page.pop_dialog()
            open_delete_confirm_dialog(user)

        dlg = ft.AlertDialog(modal=True, title=ft.Row(spacing=10, controls=[ft.Icon(ft.Icons.EDIT, color=colors["ORANGE"], size=22), ft.Column(spacing=2, controls=[ft.Text("Edit User", size=18, weight=ft.FontWeight.W_600, color=colors["TEXT"]), ft.Text(f"Update {user.get('username')}", size=12, color=colors["MUTED"])])]), content=ft.Container(width=480, content=ft.Column(spacing=12, controls=[username_field, email_field, role_dropdown])), actions=[ft.TextButton("Delete User", on_click=on_delete, style=ft.ButtonStyle(color=colors["RED"])), ft.TextButton("Cancel", on_click=on_cancel, style=ft.ButtonStyle(color=colors["MUTED"])), ft.Button("Update User", on_click=on_save, style=ft.ButtonStyle(bgcolor=colors["ORANGE"], color="#FFFFFF", elevation=0, shape=ft.RoundedRectangleBorder(radius=8)))], actions_alignment=ft.MainAxisAlignment.END, bgcolor=colors["CARD_BG"], shape=ft.RoundedRectangleBorder(radius=12))
        page.show_dialog(dlg)

    # Initial load
    refresh_grid()

    content = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=0,
        controls=[content_header, filter_row, ft.Container(expand=True, padding=ft.Padding.symmetric(horizontal=32, vertical=12), content=users_grid)],
    )

    layout = ft.Row(expand=True, spacing=0, controls=[sidebar, ft.Column(expand=True, spacing=0, controls=[top_bar, content])])

    return ft.View(route="/users", padding=0, spacing=0, bgcolor=colors["BG"], controls=[layout])
