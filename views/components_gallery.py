import flet as ft


def components_gallery_view(page: ft.Page) -> ft.View:
    page.title = "Flet Controls Showcase"

    status_text = ft.Text("Ready", size=12, color=ft.Colors.GREY_700)

    def show_snackbar(_):
        page.open(
            ft.SnackBar(
                content=ft.Text("Saved successfully!"),
                action="UNDO",
                duration=2500,
            )
        )

    def show_bottom_sheet(_):
        sheet = ft.BottomSheet(
            content=ft.Container(
                padding=20,
                content=ft.Column(
                    tight=True,
                    controls=[
                        ft.Text("Bottom Sheet", size=20, weight=ft.FontWeight.BOLD),
                        ft.Text("This is a simple bottom sheet example."),
                        ft.ElevatedButton("Close", on_click=lambda __: page.close(sheet)),
                    ],
                ),
            )
        )
        page.open(sheet)

    def on_nav_change(e: ft.ControlEvent):
        status_text.value = f"NavigationBar tab index: {e.control.selected_index}"
        page.update()

    page.appbar = ft.AppBar(
        title=ft.Text("Kitchen Waste Tracker - Controls Demo"),
        center_title=False,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        actions=[
            ft.IconButton(icon=ft.Icons.NOTIFICATIONS_NONE),
            ft.IconButton(icon=ft.Icons.ACCOUNT_CIRCLE),
        ],
    )

    page.bottom_appbar = ft.BottomAppBar(
        bgcolor=ft.Colors.SURFACE_VARIANT,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
            controls=[
                ft.IconButton(icon=ft.Icons.HOME),
                ft.IconButton(icon=ft.Icons.SEARCH),
                ft.IconButton(icon=ft.Icons.SETTINGS),
            ],
        ),
    )

    page.navigation_bar = ft.NavigationBar(
        selected_index=0,
        on_change=on_nav_change,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.DASHBOARD_OUTLINED, selected_icon=ft.Icons.DASHBOARD, label="Dashboard"),
            ft.NavigationBarDestination(icon=ft.Icons.INVENTORY_2_OUTLINED, selected_icon=ft.Icons.INVENTORY_2, label="Inventory"),
            ft.NavigationBarDestination(icon=ft.Icons.BAR_CHART_OUTLINED, selected_icon=ft.Icons.BAR_CHART, label="Reports"),
        ],
    )

    menu_bar = ft.MenuBar(
        controls=[
            ft.SubmenuButton(
                content=ft.Text("File"),
                controls=[
                    ft.MenuItemButton(content=ft.Text("New")),
                    ft.MenuItemButton(content=ft.Text("Open")),
                    ft.MenuItemButton(content=ft.Text("Exit"), on_click=lambda e: page.go("/dashboard")),
                ],
            ),
            ft.SubmenuButton(
                content=ft.Text("Help"),
                controls=[
                    ft.MenuItemButton(content=ft.Text("About")),
                ],
            ),
        ],
    )

    demo_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Item")),
            ft.DataColumn(ft.Text("Category")),
            ft.DataColumn(ft.Text("Qty"), numeric=True),
        ],
        rows=[
            ft.DataRow(cells=[ft.DataCell(ft.Text("Milk")), ft.DataCell(ft.Text("Dairy")), ft.DataCell(ft.Text("12"))]),
            ft.DataRow(cells=[ft.DataCell(ft.Text("Tomatoes")), ft.DataCell(ft.Text("Produce")), ft.DataCell(ft.Text("35"))]),
            ft.DataRow(cells=[ft.DataCell(ft.Text("Bread")), ft.DataCell(ft.Text("Bakery")), ft.DataCell(ft.Text("18"))]),
        ],
    )

    button_examples = ft.Column(
        spacing=10,
        controls=[
            ft.Button("Basic Button"),
            ft.Button("Button with Icon", icon=ft.Icons.ADD_SHOPPING_CART),
            ft.Button("Button with Click Event", on_click=lambda e: show_snackbar(e)),
            ft.ElevatedButton("Elevated Button", icon=ft.Icons.UPGRADE),
        ],
    )

    content = ft.Column(
        scroll=ft.ScrollMode.AUTO,
        controls=[
            menu_bar,
            ft.Container(
                padding=16,
                border_radius=12,
                bgcolor=ft.Colors.AMBER_100,
                content=ft.Text("Container example", weight=ft.FontWeight.BOLD),
            ),
            ft.Text("Simple DataTable", size=18, weight=ft.FontWeight.BOLD),
            demo_table,
            ft.Text("Button variations", size=18, weight=ft.FontWeight.BOLD),
            button_examples,
            ft.Row(
                controls=[
                    ft.ElevatedButton("Show BottomSheet", on_click=show_bottom_sheet),
                    ft.ElevatedButton("Show Snackbar", on_click=show_snackbar),
                ]
            ),
            status_text,
        ],
    )

    return ft.View(
        route="/components",
        padding=16,
        controls=[content],
    )
