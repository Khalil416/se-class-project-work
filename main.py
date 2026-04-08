import flet as ft
from views.login import login_view
from views.dashboard import dashboard_view
from views.registration import registration_view
from views.inventory import inventory_view
from views.add_item import add_item_view

def main(page: ft.Page):
    page.title = "Kitchen Waste Tracker"
    page.padding = 0
    page.spacing = 0
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.ORANGE)
    page.dark_theme = ft.Theme(color_scheme_seed=ft.Colors.ORANGE)

    page.window.width = 1440
    page.window.height = 900
    page.window.min_width = 1100
    page.window.min_height = 760
    # page.window.resizable = False

    def route_change(e=None):
        # Middleware: protect /dashboard if not authenticated
        is_logged_in = page.session.store.get("is_logged_in")

        if page.route == "/dashboard" and not is_logged_in:
            page.route = "/"

        if page.route == "/inventory" and not is_logged_in:
            page.route = "/"

        if page.route == "/add-item" and not is_logged_in:
            page.route = "/"

        page.views.clear()

        # Always add the login view as root
        page.views.append(login_view(page))

        # Add registration on top if route matches
        if page.route == "/register":
            page.views.append(registration_view(page))

        # Add dashboard on top if route matches
        if page.route == "/dashboard":
            page.views.append(dashboard_view(page))

        # Add inventory on top if route matches
        if page.route == "/inventory":
            page.views.append(inventory_view(page))

        # Add add/edit item form on top if route matches
        if page.route == "/add-item":
            page.views.append(add_item_view(page))

        page.update()

    def view_pop(e):
        if e.view is not None:
            page.views.remove(e.view)
            top_view = page.views[-1]
            page.route = top_view.route
            page.update()

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    route_change()


ft.run(main)
