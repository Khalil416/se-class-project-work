import flet as ft

# Palette
BG = "#f3f4f6"
CARD_BG = "#ffffff"
CARD_BORDER = "#e5e7eb"
TEXT = "#111827"
MUTED = "#6b7280"
MUTED_2 = "#9ca3af"
BRAND = "#e68614"
BRAND_HOVER = "#d97808"
FIELD_BG = "#ffffff"
FIELD_BG_HOVER = "#fafafa"
FIELD_BORDER = "#d1d5db"
FIELD_BORDER_HOVER = "#aeb6c2"
FIELD_BORDER_FOCUS = BRAND
CHIP_BG = "#f8fafc"
CHIP_BG_HOVER = "#f1f5f9"
CHIP_BORDER = "#e5e7eb"


class HoverLink(ft.Container):
    def __init__(self, text: str, base_color: str = MUTED, hover_color: str = BRAND, size: int = 14):
        self.label = ft.Text(text, size=size, color=base_color)
        self.base_color = base_color
        self.hover_color = hover_color
        super().__init__(
            content=self.label,
            padding=ft.padding.symmetric(horizontal=2, vertical=2),
            border_radius=6,
            ink=True,
            mouse_cursor=ft.MouseCursor.CLICK,
            on_hover=self._on_hover,
        )

    def _on_hover(self, e: ft.ControlEvent):
        self.label.color = self.hover_color if e.data == "true" else self.base_color
        self.update()


class HoverChip(ft.Container):
    def __init__(self, icon_name: str, text: str):
        self.icon = ft.Icon(icon_name, size=13, color="#d9a25f")
        self.label = ft.Text(text, size=11, weight=ft.FontWeight.W_600, color=MUTED)
        super().__init__(
            bgcolor=CHIP_BG,
            border=ft.border.all(1, CHIP_BORDER),
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            content=ft.Row(spacing=6, tight=True, controls=[self.icon, self.label]),
            mouse_cursor=ft.MouseCursor.CLICK,
            animate=ft.animation.Animation(140, "easeOut"),
            on_hover=self._on_hover,
        )

    def _on_hover(self, e: ft.ControlEvent):
        hover = e.data == "true"
        self.bgcolor = CHIP_BG_HOVER if hover else CHIP_BG
        self.border = ft.border.all(1, "#dbe3ed" if hover else CHIP_BORDER)
        self.label.color = "#4b5563" if hover else MUTED
        self.update()


class InteractiveField(ft.Container):
    def __init__(self, label: str, hint: str, icon_name: str, password: bool = False):
        self.focused = False
        self.textfield = ft.TextField(
            hint_text=hint,
            border=ft.InputBorder.NONE,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=12),
            text_size=14,
            hint_style=ft.TextStyle(size=14, color=MUTED_2),
            prefix_icon=icon_name,
            cursor_color=BRAND,
            password=password,
            can_reveal_password=password,
            on_focus=self._on_focus,
            on_blur=self._on_blur,
        )
        self.shell = ft.Container(
            height=48,
            bgcolor=FIELD_BG,
            border=ft.border.all(1, FIELD_BORDER),
            border_radius=8,
            animate=ft.animation.Animation(140, "easeOut"),
            content=self.textfield,
        )
        super().__init__(
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Text(label, size=16, weight=ft.FontWeight.W_500, color="#2b2f36"),
                    self.shell,
                ],
            ),
            on_hover=self._on_hover,
        )

    def _on_hover(self, e: ft.ControlEvent):
        if self.focused:
            return
        hover = e.data == "true"
        self.shell.bgcolor = FIELD_BG_HOVER if hover else FIELD_BG
        self.shell.border = ft.border.all(1, FIELD_BORDER_HOVER if hover else FIELD_BORDER)
        self.shell.update()

    def _on_focus(self, e: ft.ControlEvent):
        self.focused = True
        self.shell.bgcolor = "#fffdf9"
        self.shell.border = ft.border.all(1.5, FIELD_BORDER_FOCUS)
        self.shell.update()

    def _on_blur(self, e: ft.ControlEvent):
        self.focused = False
        self.shell.bgcolor = FIELD_BG
        self.shell.border = ft.border.all(1, FIELD_BORDER)
        self.shell.update()


class HoverButton(ft.Container):
    def __init__(self, text: str, icon_name: str):
        self.label = ft.Text(text, size=15, weight=ft.FontWeight.W_700, color="#ffffff")
        self.icon = ft.Icon(icon_name, size=18, color="#ffffff")
        super().__init__(
            width=495,
            height=50,
            bgcolor=BRAND,
            border_radius=8,
            alignment=ft.alignment.center,
            animate=ft.animation.Animation(120, "easeOut"),
            ink=True,
            on_hover=self._on_hover,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
                controls=[self.label, self.icon],
            ),
        )

    def _on_hover(self, e: ft.ControlEvent):
        self.bgcolor = BRAND_HOVER if e.data == "true" else BRAND
        self.update()


def logo() -> ft.Control:
    return ft.Container(
        width=56,
        height=56,
        border_radius=28,
        bgcolor=BRAND,
        alignment=ft.alignment.center,
        content=ft.Icon(ft.icons.ECO_OUTLINED, color="#ffffff", size=32),
    )


def main(page: ft.Page):
    page.title = "Kitchen Waste Tracker"
    page.bgcolor = BG
    page.window_bgcolor = BG
    page.padding = 22
    page.theme_mode = ft.ThemeMode.LIGHT

    username = InteractiveField("Email or Username", "e.g. chef_julian", ft.icons.MAIL_OUTLINE)
    password = InteractiveField("Password", "••••••••", ft.icons.LOCK_OUTLINE, password=True)

    forgot_link = HoverLink("Forgot password?", base_color=BRAND, hover_color=BRAND_HOVER, size=13)

    keep_me = ft.Checkbox(
        label="Keep me logged in",
        value=False,
        active_color=BRAND,
        check_color="#ffffff",
        label_style=ft.TextStyle(size=16, color="#2b2f36"),
    )

    signin_button = HoverButton("Sign In", ft.icons.ARROW_FORWARD)

    card = ft.Container(
        width=575,
        bgcolor=CARD_BG,
        border=ft.border.all(1, CARD_BORDER),
        border_radius=18,
        shadow=ft.BoxShadow(blur_radius=20, spread_radius=0, color="#1a000000", offset=ft.Offset(0, 6)),
        content=ft.Column(
            spacing=0,
            controls=[
                ft.Container(
                    padding=ft.padding.only(left=40, right=40, top=34, bottom=22),
                    content=ft.Column(
                        spacing=18,
                        controls=[
                            ft.Text("Sign In", size=37 / 2, weight=ft.FontWeight.W_700, color="#1f2937"),
                            username,
                            ft.Column(
                                spacing=8,
                                controls=[
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        controls=[
                                            ft.Text(
                                                "Password",
                                                size=16,
                                                weight=ft.FontWeight.W_500,
                                                color="#2b2f36",
                                            ),
                                            forgot_link,
                                        ],
                                    ),
                                    password.shell,
                                ],
                            ),
                            keep_me,
                            signin_button,
                            ft.Divider(height=26, color="#eceef1"),
                            ft.Column(
                                spacing=12,
                                controls=[
                                    ft.Row(
                                        spacing=8,
                                        controls=[
                                            ft.Icon(ft.icons.INFO_OUTLINE, size=16, color=MUTED),
                                            ft.Text(
                                                "AUTHORIZED PERSONAS",
                                                size=9,
                                                weight=ft.FontWeight.W_700,
                                                color=MUTED,
                                                letter_spacing=0.6,
                                            ),
                                        ],
                                    ),
                                    ft.Row(
                                        wrap=True,
                                        spacing=8,
                                        run_spacing=8,
                                        controls=[
                                            HoverChip(ft.icons.RESTAURANT_OUTLINED, "KITCHEN STAFF"),
                                            HoverChip(ft.icons.BADGE_OUTLINED, "INVENTORY MGR"),
                                            HoverChip(ft.icons.BUSINESS_CENTER_OUTLINED, "GENERAL MGR"),
                                        ],
                                    ),
                                    ft.Text(
                                        "* Credentials are managed by your kitchen administrator. Please contact your\n"
                                        "manager if you cannot sign in.",
                                        size=13,
                                        color=MUTED,
                                        italic=True,
                                    ),
                                ],
                            ),
                        ],
                    ),
                ),
                ft.Container(
                    border=ft.border.only(top=ft.BorderSide(1, "#eceef1")),
                    bgcolor="#fbfbfc",
                    border_radius=ft.border_radius.only(bottom_left=18, bottom_right=18),
                    padding=ft.padding.symmetric(horizontal=20, vertical=15),
                    alignment=ft.alignment.center,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                        controls=[
                            ft.Icon(ft.icons.VERIFIED_USER_OUTLINED, size=16, color="#4b5563"),
                            ft.Text(
                                "Secured by enterprise-grade encryption",
                                size=14,
                                color="#4b5563",
                                weight=ft.FontWeight.W_500,
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )

    help_row = ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=16,
        controls=[
            ft.Row(
                spacing=6,
                controls=[
                    ft.Icon(ft.icons.HELP_OUTLINE, size=17, color=MUTED),
                    HoverLink("Need Help?", size=14),
                ],
            ),
            ft.Text("|", color="#d1d5db"),
            HoverLink("Support Center", size=14),
        ],
    )

    page.add(
        ft.Container(
            expand=True,
            bgcolor=BG,
            border=ft.border.all(1, "#e5e7eb"),
            content=ft.Column(
                expand=True,
                spacing=0,
                controls=[
                    ft.Container(
                        expand=True,
                        alignment=ft.alignment.center,
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=20,
                            controls=[
                                logo(),
                                ft.Text(
                                    "Kitchen Waste Tracker",
                                    size=50 / 2,
                                    weight=ft.FontWeight.W_700,
                                    color=TEXT,
                                ),
                                ft.Text(
                                    "Manage inventory, reduce waste,\nand optimize kitchen operations.",
                                    size=19,
                                    color=MUTED,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                ft.Container(height=8),
                                card,
                                help_row,
                            ],
                        ),
                    ),
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=40, vertical=22),
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(
                                    "© 2026 Kitchen Food Waste Tracker. All rights reserved.",
                                    size=14,
                                    color=MUTED,
                                ),
                                ft.Row(
                                    spacing=28,
                                    controls=[
                                        HoverLink("Privacy Policy", size=14),
                                        HoverLink("Terms of Service", size=14),
                                        HoverLink("Help Center", size=14),
                                    ],
                                ),
                            ],
                        ),
                    ),
                    ft.Container(
                        padding=ft.padding.only(left=2, right=2, bottom=2),
                        content=ft.Row(
                            spacing=4,
                            controls=[
                                ft.Text("Made with", size=14, color=MUTED_2),
                                ft.Icon(ft.icons.BOLT, size=15, color="#6d5efc"),
                                ft.Text("Visily", size=15, weight=ft.FontWeight.W_700, color=TEXT),
                            ],
                        ),
                    ),
                ],
            ),
        )
    )


ft.run(main)
