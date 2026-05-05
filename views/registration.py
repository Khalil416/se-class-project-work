import flet as ft
import sqlite3
import os
import re
import requests

DB_PATH = "reg.db"
API_URL = "http://127.0.0.1:8000"

LIGHT = {
    "ORANGE": "#E68A17",
    "BG": "#F5F5F5",
    "CARD_BG": "#FFFFFF",
    "TEXT": "#222222",
    "MUTED": "#7A7A7A",
    "BORDER": "#E7E7E7",
    "DIVIDER": "#EEEEEE",
    "FOOTER_TEXT": "#6E6E6E",
    "FOOTER_BORDER": "#E6E8EB",
    "TOPBAR_TEXT": "#666666",
    "SHADOW": "#14000000",
    "LABEL_MUTED": "#777777",
    "SECURE_ICON": "#5F5F5F",
}

DARK = {
    "ORANGE": "#E68A17",
    "BG": "#121212",
    "CARD_BG": "#1E1E1E",
    "TEXT": "#F3F3F3",
    "MUTED": "#B0B0B0",
    "BORDER": "#3A3A3A",
    "DIVIDER": "#343434",
    "FOOTER_TEXT": "#BDBDBD",
    "FOOTER_BORDER": "#2C2C2C",
    "TOPBAR_TEXT": "#D0D0D0",
    "SHADOW": "#40000000",
    "LABEL_MUTED": "#C2C2C2",
    "SECURE_ICON": "#C9C9C9",
}


def _init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'chef',
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def _register_user(username: str, email: str, password: str, role: str = "chef") -> str | None:
    try:
        response = requests.post(
            f"{API_URL}/users",
            json={"username": username, "email": email, "password": password, "role": role},
            timeout=5,
        )
        data = response.json()
        if data.get("error"):
            return data["error"]
        return None
    except requests.exceptions.RequestException:
        return "Cannot reach API server."


def registration_view(page: ft.Page) -> ft.View:
    _init_db()

    colors = LIGHT.copy() if page.theme_mode == ft.ThemeMode.LIGHT else DARK.copy()

    logo = ft.Image(
        src="assets/logo.png",
        width=50,
        height=50,
        fit=ft.BoxFit.CONTAIN,
    )

    def themed_shadow():
        return ft.BoxShadow(
            blur_radius=18,
            spread_radius=0,
            color=colors["SHADOW"],
            offset=ft.Offset(0, 4),
        )

    def labeled_field(label, icon, password=False):
        label_ref = ft.Text(
            label,
            size=15,
            color=colors["TEXT"],
            weight=ft.FontWeight.W_500,
        )
        field_ref = ft.TextField(
            width=452,
            password=password,
            can_reveal_password=password,
            height=48,
            border_radius=10,
            border_color=colors["BORDER"],
            focused_border_color=colors["ORANGE"],
            cursor_color=colors["ORANGE"],
            prefix_icon=icon,
            content_padding=ft.Padding.symmetric(horizontal=14, vertical=10),
            text_size=14,
            color=colors["TEXT"],
            bgcolor=colors["CARD_BG"],
        )
        return {
            "label": label_ref,
            "field": field_ref,
            "view": ft.Column(
                spacing=8,
                controls=[label_ref, field_ref],
            ),
        }

    title_text = ft.Text(
        "Kitchen Waste Tracker",
        size=28,
        weight=ft.FontWeight.W_700,
        color=colors["TEXT"],
    )

    subtitle_text = ft.Text(
        "Create your account to get started.",
        size=14,
        color=colors["MUTED"],
        text_align=ft.TextAlign.CENTER,
    )

    # Fields
    username_field = labeled_field("Username", ft.Icons.PERSON_OUTLINE)
    email_field = labeled_field("Email", ft.Icons.MAIL_OUTLINE)
    password_field = labeled_field("Password", ft.Icons.LOCK_OUTLINE, password=True)
    confirm_password_field = labeled_field("Confirm Password", ft.Icons.LOCK_OUTLINE, password=True)

    role_dropdown = ft.Dropdown(
        label="Choose a role",
        value="chef",
        width=452,
        options=[
            ft.DropdownOption("chef", "Kitchen Staff"),
            ft.DropdownOption("inventory_staff", "Inventory Manager"),
            ft.DropdownOption("manager", "General Manager"),
        ],
    )

    role_section = ft.Column(
        spacing=8,
        controls=[
            ft.Text(
                "User Role",
                size=15,
                color=colors["TEXT"],
                weight=ft.FontWeight.W_500,
            ),
            role_dropdown,
        ],
    )

    error_text = ft.Text("", size=13, color="#DC2626", visible=False)
    success_text = ft.Text("", size=13, color="#16A34A", visible=False)

    # If the current session user is not a manager, redirect away (registration is manager-only)
    curr_role = page.session.store.get("role")
    if curr_role != "manager":
        # Non-managers should not access this page
        page.go("/")
        return ft.View(route="/register", padding=0, spacing=0, bgcolor=colors["BG"], controls=[])

    def on_register(e):
        error_text.visible = False
        success_text.visible = False

        username = (username_field["field"].value or "").strip()
        email_val = (email_field["field"].value or "").strip()
        password = password_field["field"].value or ""
        confirm = confirm_password_field["field"].value or ""
        role_val = (role_dropdown.value or "chef")

        if not username or not email_val or not password or not confirm:
            error_text.value = "All fields are required."
            error_text.visible = True
            page.update()
            return

        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email_val):
            error_text.value = "Please enter a valid email address."
            error_text.visible = True
            page.update()
            return

        if len(password) < 4:
            error_text.value = "Password must be at least 4 characters."
            error_text.visible = True
            page.update()
            return

        if password != confirm:
            error_text.value = "Passwords do not match."
            error_text.visible = True
            page.update()
            return

        err = _register_user(username, email_val, password, role_val)
        if err:
            error_text.value = err
            error_text.visible = True
            page.update()
            return

        # On success, redirect back to users list for managers
        page.go("/users")
        return

    register_button = ft.Button(
        width=452,
        height=48,
        on_click=on_register,
        style=ft.ButtonStyle(
            bgcolor=colors["ORANGE"],
            color="#FFFFFF",
            elevation=0,
            shape=ft.RoundedRectangleBorder(radius=10),
        ),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
            controls=[
                ft.Text("Register", size=16, weight=ft.FontWeight.W_700, color="#FFFFFF"),
                ft.Icon(ft.Icons.PERSON_ADD, size=18, color="#FFFFFF"),
            ],
        ),
    )

    back_button = ft.TextButton(
        "Back to Users",
        on_click=lambda e: page.go("/users"),
        style=ft.ButtonStyle(
            color=colors["ORANGE"],
            text_style=ft.TextStyle(size=13, weight=ft.FontWeight.W_600),
        ),
    )

    header = ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=10,
        controls=[logo, title_text, subtitle_text],
    )

    registration_card = ft.Container(
        width=500,
        bgcolor=colors["CARD_BG"],
        border=ft.Border.all(1, colors["BORDER"]),
        border_radius=20,
        padding=24,
        shadow=themed_shadow(),
        content=ft.Column(
            spacing=16,
            controls=[
                ft.Text("Create Account", size=22, weight=ft.FontWeight.W_700, color=colors["TEXT"]),
                username_field["view"],
                email_field["view"],
                password_field["view"],
                confirm_password_field["view"],
                role_section,
                error_text,
                success_text,
                register_button,
                ft.Divider(height=20, color=colors["DIVIDER"]),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[back_button],
                ),
            ],
        ),
    )

    footer = ft.Container(
        padding=ft.Padding.symmetric(horizontal=32, vertical=18),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Text(
                    "\u00a9 2026 Kitchen Food Waste Tracker. All rights reserved.",
                    size=13,
                    color=colors["FOOTER_TEXT"],
                ),
            ],
        ),
    )

    main_layout = ft.Container(
        expand=True,
        bgcolor=colors["BG"],
        border=ft.Border.all(1, colors["FOOTER_BORDER"]),
        content=ft.Column(
            spacing=0,
            expand=True,
            controls=[
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment(0, -1),
                    padding=ft.Padding.only(top=40),
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=26,
                        controls=[header, registration_card],
                    ),
                ),
                footer,
            ],
        ),
    )

    return ft.View(
        route="/register",
        padding=0,
        spacing=0,
        bgcolor=colors["BG"],
        vertical_alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[main_layout],
        scroll=ft.ScrollMode.AUTO,
    )
