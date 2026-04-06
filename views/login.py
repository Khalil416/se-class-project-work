import flet as ft


LIGHT = {
    "ORANGE": "#E68A17",
    "BG": "#F5F5F5",
    "CARD_BG": "#FFFFFF",
    "TEXT": "#222222",
    "MUTED": "#7A7A7A",
    "BORDER": "#E7E7E7",
    "CHIP_BG": "#FAFAFA",
    "CHIP_BORDER": "#EFEFEF",
    "ICON_SOFT": "#D5A160",
    "LABEL_MUTED": "#777777",
    "TOPBAR_TEXT": "#666666",
    "DIVIDER": "#EEEEEE",
    "INFO_TEXT": "#6F6F6F",
    "FOOTER_TEXT": "#6E6E6E",
    "FOOTER_BORDER": "#E6E8EB",
    "SECURE_ICON": "#5F5F5F",
    "SHADOW": "#14000000",
    "STAGE_SHADOW": "#12000000",
}

DARK = {
    "ORANGE": "#E68A17",
    "BG": "#121212",
    "CARD_BG": "#1E1E1E",
    "TEXT": "#F3F3F3",
    "MUTED": "#B0B0B0",
    "BORDER": "#3A3A3A",
    "CHIP_BG": "#262626",
    "CHIP_BORDER": "#3A3A3A",
    "ICON_SOFT": "#D5A160",
    "LABEL_MUTED": "#C2C2C2",
    "TOPBAR_TEXT": "#D0D0D0",
    "DIVIDER": "#343434",
    "INFO_TEXT": "#C8C8C8",
    "FOOTER_TEXT": "#BDBDBD",
    "FOOTER_BORDER": "#2C2C2C",
    "SECURE_ICON": "#C9C9C9",
    "SHADOW": "#40000000",
    "STAGE_SHADOW": "#50000000",
}


def login_view(page: ft.Page) -> ft.View:
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

    def stage_shadow():
        return ft.BoxShadow(
            blur_radius=10,
            spread_radius=0,
            color=colors["STAGE_SHADOW"],
            offset=ft.Offset(0, 2),
        )

    def persona_chip(icon, label):
        icon_ref = ft.Icon(icon, size=14, color=colors["ICON_SOFT"])
        text_ref = ft.Text(
            label,
            size=10,
            color=colors["LABEL_MUTED"],
            weight=ft.FontWeight.W_600,
        )
        chip = ft.Container(
            padding=ft.Padding.symmetric(horizontal=8, vertical=5),
            bgcolor=colors["CHIP_BG"],
            border=ft.Border.all(1, colors["CHIP_BORDER"]),
            border_radius=8,
            content=ft.Row(
                tight=True,
                spacing=6,
                controls=[icon_ref, text_ref],
            ),
        )
        return {
            "container": chip,
            "icon": icon_ref,
            "text": text_ref,
        }

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

    theme_text = ft.Text("Light Mode", size=12, color=colors["TOPBAR_TEXT"])
    theme_button = ft.IconButton(
        icon=ft.Icons.LIGHT_MODE,
        tooltip="Toggle light/dark mode",
        icon_color=colors["TOPBAR_TEXT"],
    )

    title_text = ft.Text(
        "Kitchen Waste Tracker",
        size=28,
        weight=ft.FontWeight.W_700,
        color=colors["TEXT"],
    )

    subtitle_text = ft.Text(
        "Manage inventory, reduce waste,\nand optimize kitchen operations.",
        size=14,
        color=colors["MUTED"],
        text_align=ft.TextAlign.CENTER,
    )

    email_field = labeled_field("Email or Username", ft.Icons.MAIL_OUTLINE)

    password_text = ft.Text(
        "Password",
        size=15,
        color=colors["TEXT"],
        weight=ft.FontWeight.W_500,
    )

    forgot_button = ft.TextButton(
        "Forgot password?",
        style=ft.ButtonStyle(
            color=colors["ORANGE"],
            padding=ft.Padding.symmetric(horizontal=0, vertical=0),
            text_style=ft.TextStyle(
                size=13,
                weight=ft.FontWeight.W_600,
            ),
        ),
    )

    password_input = ft.TextField(
        width=452,
        password=True,
        can_reveal_password=True,
        height=48,
        border_radius=10,
        border_color=colors["BORDER"],
        focused_border_color=colors["ORANGE"],
        cursor_color=colors["ORANGE"],
        prefix_icon=ft.Icons.LOCK_OUTLINE,
        content_padding=ft.Padding.symmetric(horizontal=14, vertical=10),
        text_size=14,
        color=colors["TEXT"],
        bgcolor=colors["CARD_BG"],
    )

    keep_logged_checkbox = ft.Checkbox(
        label="Keep me logged in",
        value=False,
        active_color=colors["ORANGE"],
        check_color="#FFFFFF",
        label_style=ft.TextStyle(color=colors["TEXT"]),
    )

    sign_in_text = ft.Text(
        "Sign In",
        size=16,
        weight=ft.FontWeight.W_700,
        color="#FFFFFF",
    )

    sign_in_icon = ft.Icon(ft.Icons.ARROW_FORWARD, size=18, color="#FFFFFF")

    error_text = ft.Text("", size=13, color="#DC2626", visible=False)

    def on_sign_in(e):
        username = email_field["field"].value or ""
        password = password_input.value or ""

        if not username or not password:
            error_text.value = "Please enter both username and password."
            error_text.visible = True
            page.update()
            return

        # Demo credentials check
        if username == "admin" and password == "admin":
            page.session.store.set("is_logged_in", True)
            page.session.store.set("username", username)
            page.go("/dashboard")
        else:
            error_text.value = "Invalid credentials. Try admin / admin."
            error_text.visible = True
            page.update()

    sign_in_button = ft.Button(
        width=452,
        height=48,
        on_click=on_sign_in,
        style=ft.ButtonStyle(
            bgcolor=colors["ORANGE"],
            color="#FFFFFF",
            elevation=0,
            shape=ft.RoundedRectangleBorder(radius=10),
        ),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
            controls=[sign_in_text, sign_in_icon],
        ),
    )

    divider = ft.Divider(height=20, color=colors["DIVIDER"])

    info_icon = ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color=colors["LABEL_MUTED"])
    info_text_ctrl = ft.Text(
        "AUTHORIZED PERSONAS",
        size=12,
        color=colors["INFO_TEXT"],
        weight=ft.FontWeight.W_700,
    )

    chip1 = persona_chip(ft.Icons.RESTAURANT_OUTLINED, "KITCHEN STAFF")
    chip2 = persona_chip(ft.Icons.INVENTORY_2_OUTLINED, "INVENTORY MGR")
    chip3 = persona_chip(ft.Icons.BAR_CHART_OUTLINED, "GENERAL MGR")

    credentials_text = ft.Text(
        "* Credentials are managed by your kitchen administrator. "
        "Please contact your manager if you cannot sign in.",
        size=12,
        color=colors["LABEL_MUTED"],
        italic=True,
    )

    secure_icon = ft.Icon(ft.Icons.SHIELD_OUTLINED, size=16, color=colors["SECURE_ICON"])
    secure_text = ft.Text(
        "Secured by enterprise-grade encryption",
        size=14,
        color=colors["TOPBAR_TEXT"],
        weight=ft.FontWeight.W_500,
    )

    help_icon = ft.Icon(ft.Icons.HELP_OUTLINE, size=18, color=colors["MUTED"])
    need_help_text = ft.Text("Need Help?", size=14, color=colors["TOPBAR_TEXT"])
    support_center_text = ft.Text("Support Center", size=14, color=colors["TOPBAR_TEXT"])
    pipe_text = ft.Text("|", color=colors["BORDER"], size=14)

    footer_left = ft.Text(
        "\u00a9 2026 Kitchen Food Waste Tracker. All rights reserved.",
        size=13,
        color=colors["FOOTER_TEXT"],
    )
    footer_privacy = ft.Text("Privacy Policy", size=13, color=colors["FOOTER_TEXT"])
    footer_terms = ft.Text("Terms of Service", size=13, color=colors["FOOTER_TEXT"])
    footer_help = ft.Text("Help Center", size=13, color=colors["FOOTER_TEXT"])

    header = ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=10,
        controls=[
            logo,
            title_text,
            subtitle_text,
        ],
    )

    password_label = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            password_text,
            forgot_button,
        ],
    )

    login_card = ft.Container(
        width=500,
        bgcolor=colors["CARD_BG"],
        border=ft.Border.all(1, colors["BORDER"]),
        border_radius=20,
        padding=24,
        shadow=themed_shadow(),
        content=ft.Column(
            spacing=16,
            controls=[
                ft.Text(
                    "Sign In",
                    size=22,
                    weight=ft.FontWeight.W_700,
                    color=colors["TEXT"],
                ),
                email_field["view"],
                ft.Column(
                    spacing=8,
                    controls=[
                        password_label,
                        password_input,
                    ],
                ),
                keep_logged_checkbox,
                error_text,
                sign_in_button,
                divider,
                ft.Column(
                    spacing=12,
                    controls=[
                        ft.Row(
                            spacing=8,
                            controls=[
                                info_icon,
                                info_text_ctrl,
                            ],
                        ),
                        ft.Row(
                            wrap=True,
                            spacing=8,
                            run_spacing=8,
                            controls=[
                                chip1["container"],
                                chip2["container"],
                                chip3["container"],
                            ],
                        ),
                        credentials_text,
                    ],
                ),
                ft.Container(
                    margin=ft.Margin.only(top=6),
                    padding=ft.Padding.only(top=14),
                    border=ft.Border(top=ft.BorderSide(1, colors["CHIP_BORDER"])),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                        controls=[
                            secure_icon,
                            secure_text,
                        ],
                    ),
                ),
            ],
        ),
    )

    login_title = login_card.content.controls[0]

    help_links = ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=18,
        controls=[
            ft.Row(
                spacing=6,
                controls=[
                    help_icon,
                    need_help_text,
                ],
            ),
            pipe_text,
            support_center_text,
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
        padding=ft.Padding.symmetric(horizontal=32, vertical=18),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                footer_left,
                ft.Row(
                    spacing=24,
                    controls=[
                        footer_privacy,
                        footer_terms,
                        footer_help,
                    ],
                ),
            ],
        ),
    )

    topbar = ft.Row(
        alignment=ft.MainAxisAlignment.END,
        controls=[
            theme_text,
            theme_button,
        ],
    )

    main_layout = ft.Container(
        expand=True,
        bgcolor=colors["BG"],
        border=ft.Border.all(1, colors["FOOTER_BORDER"]),
        shadow=stage_shadow(),
        content=ft.Column(
            spacing=0,
            expand=True,
            controls=[
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment(0, -1),
                    padding=ft.Padding.only(top=40),
                    content=center_content,
                ),
                footer,
            ],
        ),
    )

    def apply_theme():
        nonlocal colors
        colors = LIGHT.copy() if page.theme_mode == ft.ThemeMode.LIGHT else DARK.copy()

        # page.bgcolor set via View

        theme_text.value = "Light Mode" if page.theme_mode == ft.ThemeMode.LIGHT else "Dark Mode"
        theme_text.color = colors["TOPBAR_TEXT"]
        theme_button.icon = ft.Icons.LIGHT_MODE if page.theme_mode == ft.ThemeMode.LIGHT else ft.Icons.DARK_MODE
        theme_button.icon_color = colors["TOPBAR_TEXT"]

        title_text.color = colors["TEXT"]
        subtitle_text.color = colors["MUTED"]

        email_field["label"].color = colors["TEXT"]
        email_field["field"].border_color = colors["BORDER"]
        email_field["field"].focused_border_color = colors["ORANGE"]
        email_field["field"].cursor_color = colors["ORANGE"]
        email_field["field"].color = colors["TEXT"]
        email_field["field"].bgcolor = colors["CARD_BG"]

        password_text.color = colors["TEXT"]
        forgot_button.style = ft.ButtonStyle(
            color=colors["ORANGE"],
            padding=ft.Padding.symmetric(horizontal=0, vertical=0),
            text_style=ft.TextStyle(
                size=13,
                weight=ft.FontWeight.W_600,
            ),
        )

        password_input.border_color = colors["BORDER"]
        password_input.focused_border_color = colors["ORANGE"]
        password_input.cursor_color = colors["ORANGE"]
        password_input.color = colors["TEXT"]
        password_input.bgcolor = colors["CARD_BG"]

        keep_logged_checkbox.active_color = colors["ORANGE"]
        keep_logged_checkbox.label_style = ft.TextStyle(color=colors["TEXT"])

        login_card.bgcolor = colors["CARD_BG"]
        login_card.border = ft.Border.all(1, colors["BORDER"])
        login_card.shadow = themed_shadow()
        login_title.color = colors["TEXT"]

        divider.color = colors["DIVIDER"]

        info_icon.color = colors["LABEL_MUTED"]
        info_text_ctrl.color = colors["INFO_TEXT"]

        for chip in [chip1, chip2, chip3]:
            chip["container"].bgcolor = colors["CHIP_BG"]
            chip["container"].border = ft.Border.all(1, colors["CHIP_BORDER"])
            chip["icon"].color = colors["ICON_SOFT"]
            chip["text"].color = colors["LABEL_MUTED"]

        credentials_text.color = colors["LABEL_MUTED"]

        secure_icon.color = colors["SECURE_ICON"]
        secure_text.color = colors["TOPBAR_TEXT"]

        login_card.content.controls[-1].border = ft.Border(
            top=ft.BorderSide(1, colors["CHIP_BORDER"])
        )

        help_icon.color = colors["MUTED"]
        need_help_text.color = colors["TOPBAR_TEXT"]
        support_center_text.color = colors["TOPBAR_TEXT"]
        pipe_text.color = colors["BORDER"]

        footer_left.color = colors["FOOTER_TEXT"]
        footer_privacy.color = colors["FOOTER_TEXT"]
        footer_terms.color = colors["FOOTER_TEXT"]
        footer_help.color = colors["FOOTER_TEXT"]

        main_layout.bgcolor = colors["BG"]
        main_layout.border = ft.Border.all(1, colors["FOOTER_BORDER"])
        main_layout.shadow = stage_shadow()

    def change_theme(e):
        page.theme_mode = (
            ft.ThemeMode.DARK
            if page.theme_mode == ft.ThemeMode.LIGHT
            else ft.ThemeMode.LIGHT
        )
        apply_theme()
        page.update()

    theme_button.on_click = change_theme

    apply_theme()

    return ft.View(
        route="/",
        padding=0,
        spacing=0,
        bgcolor=colors["BG"],
        vertical_alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[topbar, main_layout],
    )
