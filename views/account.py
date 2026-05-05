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
    "DIVIDER": "#F0F0F0",
    "SHADOW": "#08000000",
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
    "DIVIDER": "#252525",
    "SHADOW": "#30000000",
    "AVATAR_BG": "#5D4037",
}


def _get_account(user_id=None, username=None):
    try:
        if user_id is not None:
            response = requests.get(f"{API_URL}/users/{user_id}", timeout=5)
            if response.status_code == 200:
                return response.json()
        if username:
            response = requests.get(f"{API_URL}/users", params={"search": username}, timeout=5)
            if response.status_code == 200:
                for row in response.json().get("data", []):
                    if row.get("username") == username:
                        return row
    except requests.exceptions.RequestException:
        pass
    return None


def account_view(page: ft.Page) -> ft.View:
    colors = LIGHT.copy() if page.theme_mode == ft.ThemeMode.LIGHT else DARK.copy()
    username = page.session.store.get("username") or "User"
    user_id = page.session.store.get("user_id")
    account = _get_account(user_id=user_id, username=username) or {}

    role_map = {
        "chef": "Kitchen Staff",
        "inventory_staff": "Inventory Manager",
        "manager": "General Manager",
    }
    initials = (account.get("username") or username)[:2].upper()

    card = ft.Container(
        width=560,
        bgcolor=colors["CARD_BG"],
        border=ft.Border.all(1, colors["BORDER"]),
        border_radius=16,
        padding=28,
        shadow=ft.BoxShadow(blur_radius=16, spread_radius=0, color=colors["SHADOW"], offset=ft.Offset(0, 4)),
        content=ft.Column(
            spacing=18,
            controls=[
                ft.Row(
                    spacing=16,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            width=64,
                            height=64,
                            bgcolor=colors["AVATAR_BG"],
                            border_radius=32,
                            alignment=ft.Alignment(0, 0),
                            content=ft.Text(initials, size=22, weight=ft.FontWeight.W_700, color=colors["ORANGE"]),
                        ),
                        ft.Column(
                            spacing=3,
                            controls=[
                                ft.Text("Account Information", size=24, weight=ft.FontWeight.W_700, color=colors["TEXT"]),
                                ft.Text("View your profile details and login credentials.", size=13, color=colors["TEXT_SECONDARY"]),
                            ],
                        ),
                    ],
                ),
                ft.Divider(height=1, color=colors["DIVIDER"]),
                ft.Column(
                    spacing=14,
                    controls=[
                        ft.TextField(label="Username", value=account.get("username", username), read_only=True),
                        ft.TextField(label="Password", value=account.get("password", ""), read_only=True),
                        ft.TextField(label="Email", value=account.get("email", ""), read_only=True),
                        ft.TextField(label="Role", value=role_map.get(account.get("role") or "chef", "Kitchen Staff"), read_only=True),
                    ],
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.END,
                    controls=[
                        ft.TextButton(
                            "Back",
                            on_click=lambda e: page.go("/dashboard"),
                            style=ft.ButtonStyle(
                                color=colors["ORANGE"],
                                text_style=ft.TextStyle(size=13, weight=ft.FontWeight.W_600),
                            ),
                        ),
                    ],
                ),
            ],
        ),
    )

    return ft.View(
        route="/account",
        padding=0,
        spacing=0,
        bgcolor=colors["BG"],
        controls=[
            ft.Container(
                expand=True,
                alignment=ft.Alignment(0, 0),
                padding=ft.Padding.all(24),
                content=card,
            )
        ],
    )
