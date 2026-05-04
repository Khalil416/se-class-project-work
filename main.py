import flet as ft
from views.login import login_view
from views.dashboard import dashboard_view
from views.inventory import inventory_view
from views.add_item import add_item_view
from views.item_detail import item_detail_view
from views.waste_new import waste_new_view
from views.expiry_monitor import expiry_monitor_view
from views.waste_logs import waste_logs_view
from views.reports import reports_view
from views.categories import categories_view
from views.users_staff import users_staff_view
from views.account import account_view
from views.registration import registration_view

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
        # Middleware: authentication + role-based access control
        is_logged_in = page.session.store.get("is_logged_in")
        user_role = page.session.store.get("role") or "chef"

        # Login check for protected routes
        protected_routes = ["/dashboard", "/inventory", "/add-item", "/waste/new", "/expiry", "/waste-logs", "/reports", "/categories", "/users", "/account", "/register"]
        if any(page.route == r for r in protected_routes) and not is_logged_in:
            page.route = "/"
        
        if page.route.startswith("/item/") and not is_logged_in:
            page.route = "/"

        # Role-based access control
        # Manager-only routes
        if page.route in ("/reports", "/categories", "/users") and user_role != "manager":
            page.route = "/dashboard"
        
        # Manager + Inventory Staff routes
        if page.route in ("/expiry", "/waste-logs") and user_role not in ("manager", "inventory_staff"):
            page.route = "/dashboard"
        
        page.views.clear()

        # Always add the login view as root
        page.views.append(login_view(page))

        # Add dashboard on top if route matches
        if page.route == "/dashboard":
            page.views.append(dashboard_view(page))

        # Add inventory on top if route matches
        if page.route == "/inventory":
            page.views.append(inventory_view(page))

        # Add add/edit item form on top if route matches
        if page.route == "/add-item":
            page.views.append(add_item_view(page))

        # Add item detail on top if route matches /item/{id}
        if page.route.startswith("/item/"):
            try:
                item_id = int(page.route.split("/")[-1])
                page.views.append(item_detail_view(page, item_id))
            except (ValueError, IndexError):
                pass

        # Add Record Waste view
        if page.route == "/waste/new":
            page.views.append(waste_new_view(page))

        if page.route == "/expiry":
            page.views.append(expiry_monitor_view(page))

        if page.route == "/waste-logs":
            page.views.append(waste_logs_view(page))

        if page.route == "/reports":
            page.views.append(reports_view(page))

        if page.route == "/categories":
            page.views.append(categories_view(page))

        if page.route == "/users":
            page.views.append(users_staff_view(page))

        if page.route == "/account":
            page.views.append(account_view(page))

        if page.route == "/register":
            page.views.append(registration_view(page))

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
