import flet as ft


ORANGE = "#E68A17"
BG = "#F5F5F5"
CARD_BG = "#FFFFFF"
TEXT = "#222222"
MUTED = "#7A7A7A"
BORDER = "#E7E7E7"
CHIP_BG = "#FAFAFA"


def persona_chip(icon, label):
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=10, vertical=6),
        bgcolor=CHIP_BG,
        border=ft.border.all(1, "#EFEFEF"),
        border_radius=8,
        content=ft.Row(
            tight=True,
            spacing=6,
            controls=[
                ft.Icon(icon, size=14, color="#D5A160"),
                ft.Text(
                    label,
                    size=11,
                    color="#777777",
                    weight=ft.FontWeight.W_600,
                ),
            ],
        ),
    )


def labeled_field(label, hint, icon, password=False):
    return ft.Column(
        spacing=8,
        controls=[
            ft.Text(
                label,
                size=15,
                color=TEXT,
                weight=ft.FontWeight.W_500,
            ),
            ft.TextField(
                hint_text=hint,
                password=password,
                can_reveal_password=password,
                height=48,
                border_radius=10,
                border_color=BORDER,
                focused_border_color=ORANGE,
                cursor_color=ORANGE,
                prefix_icon=icon,
                content_padding=ft.padding.symmetric(horizontal=14, vertical=10),
                text_size=14,
            ),
        ],
    )


def main(page: ft.Page):
    page.title = "Kitchen Waste Tracker"
    page.bgcolor = BG
    page.padding = 0
    page.spacing = 0
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO
    page.window_bgcolor = BG
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    logo = ft.Container(
        width=58,
        height=58,
        border_radius=29,
        bgcolor=ORANGE,
        alignment=ft.Alignment.CENTER,
        content=ft.Icon(ft.Icons.ECO_OUTLINED, color="#FFFFFF", size=30),
    )

    header = ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=10,
        controls=[
            logo,
            ft.Text(
                "Kitchen Waste Tracker",
                size=28,
                weight=ft.FontWeight.W_700,
                color=TEXT,
            ),
            ft.Text(
                "Manage inventory, reduce waste,\nand optimize kitchen operations.",
                size=14,
                color=MUTED,
                text_align=ft.TextAlign.CENTER,
            ),
        ],
    )

    password_label = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Text(
                "Password",
                size=15,
                color=TEXT,
                weight=ft.FontWeight.W_500,
            ),
            ft.TextButton(
                "Forgot password?",
                style=ft.ButtonStyle(
                    color=ORANGE,
                    padding=0,
                    text_style=ft.TextStyle(
                        size=13,
                        weight=ft.FontWeight.W_600,
                    ),
                ),
            ),
        ],
    )

    login_card = ft.Container(
        width=430,
        bgcolor=CARD_BG,
        border=ft.border.all(1, "#E8E8E8"),
        border_radius=20,
        padding=24,
        shadow=ft.BoxShadow(
            blur_radius=18,
            spread_radius=0,
            color="#14000000",
            offset=ft.Offset(0, 4),
        ),
        content=ft.Column(
            spacing=18,
            controls=[
                ft.Text(
                    "Sign In",
                    size=22,
                    weight=ft.FontWeight.W_700,
                    color=TEXT,
                ),
                labeled_field(
                    "Email or Username",
                    "e.g. chef_julian",
                    ft.Icons.MAIL_OUTLINE,
                ),
                ft.Column(
                    spacing=8,
                    controls=[
                        password_label,
                        ft.TextField(
                            hint_text="••••••••",
                            password=True,
                            can_reveal_password=True,
                            height=48,
                            border_radius=10,
                            border_color=BORDER,
                            focused_border_color=ORANGE,
                            cursor_color=ORANGE,
                            prefix_icon=ft.Icons.LOCK_OUTLINE,
                            content_padding=ft.padding.symmetric(horizontal=14, vertical=10),
                            text_size=14,
                        ),
                    ],
                ),
                ft.Checkbox(
                    label="Keep me logged in",
                    value=False,
                    active_color=ORANGE,
                    check_color="#FFFFFF",
                ),
                ft.ElevatedButton(
                    width=382,
                    height=48,
                    style=ft.ButtonStyle(
                        bgcolor=ORANGE,
                        color="#FFFFFF",
                        elevation=0,
                        shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                        controls=[
                            ft.Text(
                                "Sign In",
                                size=16,
                                weight=ft.FontWeight.W_700,
                                color="#FFFFFF",
                            ),
                            ft.Icon(ft.Icons.ARROW_FORWARD, size=18, color="#FFFFFF"),
                        ],
                    ),
                ),
                ft.Divider(height=20, color="#EEEEEE"),
                ft.Column(
                    spacing=12,
                    controls=[
                        ft.Row(
                            spacing=8,
                            controls=[
                                ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color="#777777"),
                                ft.Text(
                                    "AUTHORIZED PERSONAS",
                                    size=12,
                                    color="#6F6F6F",
                                    weight=ft.FontWeight.W_700,
                                ),
                            ],
                        ),
                        ft.Row(
                            wrap=True,
                            spacing=8,
                            run_spacing=8,
                            controls=[
                                persona_chip(ft.Icons.RESTAURANT_OUTLINED, "KITCHEN STAFF"),
                                persona_chip(ft.Icons.INVENTORY_2_OUTLINED, "INVENTORY MGR"),
                                persona_chip(ft.Icons.BAR_CHART_OUTLINED, "GENERAL MGR"),
                            ],
                        ),
                        ft.Text(
                            "* Credentials are managed by your kitchen administrator. "
                            "Please contact your manager if you cannot sign in.",
                            size=12,
                            color="#7E7E7E",
                            italic=True,
                        ),
                    ],
                ),
                ft.Container(
                    margin=ft.margin.only(top=6),
                    padding=ft.padding.only(top=14),
                    border=ft.border.only(top=ft.BorderSide(1, "#EFEFEF")),
                    alignment=ft.Alignment.CENTER,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                        controls=[
                            ft.Icon(ft.Icons.SHIELD_OUTLINED, size=16, color="#5F5F5F"),
                            ft.Text(
                                "Secured by enterprise-grade encryption",
                                size=14,
                                color="#666666",
                                weight=ft.FontWeight.W_500,
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )

    help_links = ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=18,
        controls=[
            ft.Row(
                spacing=6,
                controls=[
                    ft.Icon(ft.Icons.HELP_OUTLINE, size=18, color="#7A7A7A"),
                    ft.Text("Need Help?", size=14, color="#666666"),
                ],
            ),
            ft.Text("|", color="#CFCFCF", size=14),
            ft.Text("Support Center", size=14, color="#666666"),
        ],
    )

    center_content = ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=26,
        controls=[
            header,
            login_card,
            help_links,
        ],
    )

    footer = ft.Container(
        padding=ft.padding.symmetric(horizontal=32, vertical=18),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text(
                    "© 2026 Kitchen Food Waste Tracker. All rights reserved.",
                    size=13,
                    color="#6E6E6E",
                ),
                ft.Row(
                    spacing=24,
                    controls=[
                        ft.Text("Privacy Policy", size=13, color="#6E6E6E"),
                        ft.Text("Terms of Service", size=13, color="#6E6E6E"),
                        ft.Text("Help Center", size=13, color="#6E6E6E"),
                    ],
                ),
            ],
        ),
    )

    made_with = ft.Container(
        left=24,
        bottom=16,
        content=ft.Row(
            spacing=4,
            controls=[
                ft.Text("Made with", size=12, color="#8A8A8A"),
                ft.Text("Visily", size=12, color="#4A4A4A", weight=ft.FontWeight.W_700),
            ],
        ),
    )

    main_layout = ft.Stack(
        expand=True,
        controls=[
            ft.Container(
                expand=True,
                padding=ft.padding.symmetric(horizontal=20, vertical=20),
                content=ft.Column(
                    expand=True,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            expand=True,
                            alignment=ft.Alignment.CENTER,
                            content=center_content,
                        ),
                        footer,
                    ],
                ),
            ),
            made_with,
        ],
    )

    page.add(main_layout)


ft.run(main)