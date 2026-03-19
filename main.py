import flet as ft

# --- Palette ---
BG = "#f3f4f6"
SURFACE = "#ffffff"
CARD_BORDER = "#e5e7eb"
TEXT_PRIMARY = "#111827"
TEXT_SECONDARY = "#6b7280"
TEXT_TERTIARY = "#9ca3af"
BRAND = "#e68614"
BRAND_HOVER = "#d87907"
INPUT_BG = "#ffffff"
INPUT_BG_HOVER = "#fbfbfc"
INPUT_BORDER = "#d1d5db"
INPUT_BORDER_HOVER = "#9ca3af"
INPUT_BORDER_FOCUS = "#e68614"
CHIP_BG = "#f8fafc"
CHIP_BG_HOVER = "#f1f5f9"
CHIP_BORDER = "#e5e7eb"


class HoverLink(ft.Container):
    def __init__(self, text: str, base: str = TEXT_SECONDARY, hover: str = BRAND, size: int = 14):
        self.label = ft.Text(text, size=size, color=base)
        super().__init__(
            content=self.label,
            ink=True,
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=2, vertical=2),
            mouse_cursor=ft.MouseCursor.CLICK,
            on_hover=self._on_hover,
        )
        self._base = base
        self._hover = hover

    def _on_hover(self, e: ft.HoverEvent):
        self.label.color = self._hover if e.data == "true" else self._base
        self.update()


class PersonaChip(ft.Container):
    def __init__(self, icon: str, label: str):
        self.icon = ft.Icon(icon, size=13, color="#d9a25f")
        self.text = ft.Text(label, size=11, weight=ft.FontWeight.W_600, color="#6b7280")
        super().__init__(
            bgcolor=CHIP_BG,
            border=ft.border.all(1, CHIP_BORDER),
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            animate=ft.animation.Animation(140, "easeOut"),
            mouse_cursor=ft.MouseCursor.CLICK,
            on_hover=self._on_hover,
            content=ft.Row(spacing=6, tight=True, controls=[self.icon, self.text]),
        )

    def _on_hover(self, e: ft.HoverEvent):
        hovering = e.data == "true"
        self.bgcolor = CHIP_BG_HOVER if hovering else CHIP_BG
        self.border = ft.border.all(1, "#d7dee8" if hovering else CHIP_BORDER)
        self.text.color = "#4b5563" if hovering else "#6b7280"
        self.update()


class HoverTextField(ft.Container):
    def __init__(self, label: str, hint: str, icon: str, password: bool = False, show_label: bool = True):
        self.tf = ft.TextField(
            hint_text=hint,
            hint_style=ft.TextStyle(size=14, color="#9ca3af"),
            border=ft.InputBorder.NONE,
            text_size=14,
            cursor_color=BRAND,
            password=password,
            can_reveal_password=password,
            prefix_icon=icon,
            content_padding=ft.padding.only(left=12, right=12, top=12, bottom=12),
            on_focus=self._on_focus,
            on_blur=self._on_blur,
        )
        self.wrapper = ft.Container(
            height=48,
            border=ft.border.all(1, INPUT_BORDER),
            border_radius=8,
            bgcolor=INPUT_BG,
            animate=ft.animation.Animation(150, "easeOut"),
            content=self.tf,
        )
        controls = [self.wrapper]
        if show_label:
            controls.insert(0, ft.Text(label, size=16, color="#2b2f36", weight=ft.FontWeight.W_500))
        super().__init__(on_hover=self._on_hover, content=ft.Column(spacing=8, controls=controls))
        self._focused = False

    def _on_hover(self, e: ft.HoverEvent):
        if self._focused:
            return
        hovering = e.data == "true"
        self.wrapper.bgcolor = INPUT_BG_HOVER if hovering else INPUT_BG
        self.wrapper.border = ft.border.all(1, INPUT_BORDER_HOVER if hovering else INPUT_BORDER)
        self.wrapper.update()

    def _on_focus(self, _):
        self._focused = True
        self.wrapper.bgcolor = "#fffdf9"
        self.wrapper.border = ft.border.all(1.4, INPUT_BORDER_FOCUS)
        self.wrapper.update()

    def _on_blur(self, _):
        self._focused = False
        self.wrapper.bgcolor = INPUT_BG
        self.wrapper.border = ft.border.all(1, INPUT_BORDER)
        self.wrapper.update()


def brand_logo() -> ft.Control:
    return ft.Container(
        width=74,
        height=74,
        border_radius=37,
        alignment=ft.alignment.center,
        content=ft.Container(
            width=74,
            height=74,
            border_radius=37,
            alignment=ft.alignment.center,
            content=ft.Container(
                width=56,
                height=56,
                border_radius=28,
                bgcolor=BRAND,
                alignment=ft.alignment.center,
                content=ft.Icon(ft.Icons.ECO_OUTLINED, color="white", size=34),
            ),
        ),
    )


def main(page: ft.Page):
    page.title = "Kitchen Waste Tracker"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = BG
    page.window_bgcolor = BG
    page.padding = 24
    page.fonts = {}

    email_field = HoverTextField("Email or Username", "e.g. chef_julian", ft.Icons.MAIL_OUTLINE)
    password_field = HoverTextField("", "••••••••", ft.Icons.LOCK_OUTLINE, password=True, show_label=False)

    forgot = HoverLink("Forgot password?", base=BRAND, hover=BRAND_HOVER, size=13)

    keep_logged = ft.Checkbox(
        label="Keep me logged in",
        value=False,
        active_color=BRAND,
        check_color="white",
        label_style=ft.TextStyle(size=17, color="#30353b"),
        visual_density=ft.VisualDensity.COMFORTABLE,
    )

    sign_in_btn = ft.ElevatedButton(
        height=50,
        style=ft.ButtonStyle(
            bgcolor={
                ft.ControlState.DEFAULT: BRAND,
                ft.ControlState.HOVERED: BRAND_HOVER,
                ft.ControlState.PRESSED: "#c56f07",
            },
            color={ft.ControlState.DEFAULT: "white"},
            elevation={
                ft.ControlState.DEFAULT: 0,
                ft.ControlState.HOVERED: 2,
                ft.ControlState.PRESSED: 0,
            },
            overlay_color={ft.ControlState.HOVERED: "#ffffff11"},
            shape=ft.RoundedRectangleBorder(radius=8),
            animation_duration=180,
        ),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
            controls=[
                ft.Text("Sign In", size=30/2, weight=ft.FontWeight.W_700),
                ft.Icon(ft.Icons.ARROW_FORWARD, size=18),
            ],
        ),
    )

    personas = ft.Row(
        wrap=True,
        spacing=8,
        run_spacing=8,
        controls=[
            PersonaChip(ft.Icons.RESTAURANT_MENU_OUTLINED, "KITCHEN STAFF"),
            PersonaChip(ft.Icons.INVENTORY_2_OUTLINED, "INVENTORY MGR"),
            PersonaChip(ft.Icons.INSERT_CHART_OUTLINED, "GENERAL MGR"),
        ],
    )

    card = ft.Container(
        width=580,
        border_radius=20,
        bgcolor=SURFACE,
        border=ft.border.all(1, CARD_BORDER),
        shadow=ft.BoxShadow(
            blur_radius=20,
            spread_radius=0,
            color="#15000000",
            offset=ft.Offset(0, 6),
        ),
        content=ft.Column(
            spacing=0,
            controls=[
                ft.Container(
                    padding=ft.padding.fromLTRB(44, 36, 44, 20),
                    content=ft.Column(
                        spacing=18,
                        controls=[
                            ft.Text("Sign In", size=40/2, weight=ft.FontWeight.W_700, color="#1f2937"),
                            email_field,
                            ft.Column(
                                spacing=8,
                                controls=[
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        controls=[
                                            ft.Text(
                                                "Password",
                                                size=16,
                                                color="#2b2f36",
                                                weight=ft.FontWeight.W_500,
                                            ),
                                            forgot,
                                        ],
                                    ),
                                    password_field,
                                ],
                            ),
                            keep_logged,
                            sign_in_btn,
                            ft.Divider(height=28, color="#eceef1"),
                            ft.Column(
                                spacing=12,
                                controls=[
                                    ft.Row(
                                        spacing=8,
                                        controls=[
                                            ft.Icon(ft.Icons.INFO_OUTLINED, size=16, color="#6b7280"),
                                            ft.Text(
                                                "AUTHORIZED PERSONAS",
                                                size=18/2,
                                                color="#6b7280",
                                                weight=ft.FontWeight.W_700,
                                                letter_spacing=0.5,
                                            ),
                                        ],
                                    ),
                                    personas,
                                    ft.Text(
                                        "* Credentials are managed by your kitchen administrator. Please contact your\n"
                                        "manager if you cannot sign in.",
                                        size=13,
                                        color="#6b7280",
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
                    border_radius=ft.border_radius.only(bottom_left=20, bottom_right=20),
                    padding=ft.padding.symmetric(horizontal=20, vertical=16),
                    alignment=ft.alignment.center,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                        controls=[
                            ft.Icon(ft.Icons.VERIFIED_USER_OUTLINED, size=16, color="#4b5563"),
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

    center_panel = ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=20,
        controls=[
            brand_logo(),
            ft.Text("Kitchen Waste Tracker", size=50/2, weight=ft.FontWeight.W_700, color=TEXT_PRIMARY),
            ft.Text(
                "Manage inventory, reduce waste,\nand optimize kitchen operations.",
                size=38/2,
                color=TEXT_SECONDARY,
                text_align=ft.TextAlign.CENTER,
                weight=ft.FontWeight.W_400,
            ),
            ft.Container(height=8),
            card,
            ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=16,
                controls=[
                    ft.Row(
                        spacing=6,
                        controls=[
                            ft.Icon(ft.Icons.HELP_OUTLINE, size=17, color=TEXT_SECONDARY),
                            HoverLink("Need Help?"),
                        ],
                    ),
                    ft.Text("|", color="#c7cbd1"),
                    HoverLink("Support Center"),
                ],
            ),
        ],
    )

    footer = ft.Container(
        padding=ft.padding.symmetric(horizontal=40, vertical=24),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text("© 2026 Kitchen Food Waste Tracker. All rights reserved.", size=14, color="#6b7280"),
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
    )

    watermark = ft.Container(
        alignment=ft.alignment.bottom_left,
        padding=ft.padding.only(left=2, bottom=2),
        content=ft.Row(
            spacing=4,
            controls=[
                ft.Text("Made with", size=15, color="#9ca3af"),
                ft.Icon(ft.Icons.BOLT, size=16, color="#6d5efc"),
                ft.Text("Visily", size=16, color="#111827", weight=ft.FontWeight.W_700),
            ],
        ),
    )

    page.add(
        ft.Container(
            expand=True,
            border=ft.border.all(1, "#e5e7eb"),
            bgcolor=BG,
            content=ft.Column(
                expand=True,
                spacing=0,
                controls=[
                    ft.Container(expand=True, alignment=ft.alignment.center, content=center_panel),
                    footer,
                    watermark,
                ],
            ),
        )
    )


if __name__ == "__main__":
    ft.app(target=main)
