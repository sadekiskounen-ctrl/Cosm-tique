# Views package
from .login_view import LoginView
from .dashboard_view import DashboardView
from .pos_view import POSView
from .products_view import ProductsView
from .stock_view import StockView
from .alerts_view import AlertsView
from .suppliers_view import SuppliersView
from .cash_register_view import CashRegisterView
from .reports_view import ReportsView
from .settings_view import SettingsView

__all__ = [
    "LoginView",
    "DashboardView",
    "POSView",
    "ProductsView",
    "StockView",
    "AlertsView",
    "SuppliersView",
    "CashRegisterView",
    "ReportsView",
    "SettingsView"
]
