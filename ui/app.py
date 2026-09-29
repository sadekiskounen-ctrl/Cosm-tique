import customtkinter as ctk
import datetime
from ui.theme import FONTS, COLORS
from services.auth_service import AuthService
from services.stock_service import StockService
from services.backup_service import BackupService
from ui.views.login_view import LoginView
from ui.views.dashboard_view import DashboardView
from ui.views.pos_view import POSView
from ui.views.products_view import ProductsView
from ui.views.stock_view import StockView
from ui.views.alerts_view import AlertsView
from ui.views.suppliers_view import SuppliersView
from ui.views.cash_register_view import CashRegisterView
from ui.views.reports_view import ReportsView
from ui.views.settings_view import SettingsView

# ─── Role-Based Access Control ────────────────────────────────────────────────
ADMIN_VIEWS = {
    "dashboard", "pos", "products", "stock",
    "alerts", "suppliers", "cash_register", "reports", "settings"
}
CASHIER_VIEWS = {"pos", "cash_register"}

# ─── Commerce Storefront – Burnt Orange Palette ───────────────────────────────
_NAV_BG       = "#09090B"     # Zinc-950 – deepest base
_NAV_ACTIVE   = "#D9480F"     # Burnt Orange primary
_NAV_HOVER    = "#27272A"     # Zinc-800
_NAV_TEXT     = "#A1A1AA"     # Zinc-400 muted
_NAV_TEXT_ACT = "#FFFFFF"
_HDR_BG_DARK  = "#18181B"     # Zinc-900
_HDR_BG_LIGHT = "#FFFFFF"
_BDY_BG_DARK  = "#09090B"
_SEPARATOR    = "#3F3F46"     # Zinc-700


class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CosmétiquePro – Gestion de Stock & Caisse")
        self.geometry("1400x820")
        self.minsize(1100, 680)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        self.current_user = None
        self.current_view_name = None
        self.nav_buttons = {}
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._show_login_screen()
        self._start_background_updates()

    # ── Login / Logout ─────────────────────────────────────────────────────────

    def _show_login_screen(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.login_view = LoginView(self, on_login_success=self._on_login_success)
        self.login_view.pack(fill="both", expand=True)

    def _on_login_success(self, user):
        self.current_user = user
        self.login_view.destroy()
        self._build_main_ui()
        self.navigate_to("pos" if user.role == "caissier" else "dashboard")

    def _logout(self):
        AuthService.logout()
        self.current_user = None
        self.current_view_name = None
        self.views.clear()
        self._show_login_screen()

    # ── Main UI Builder ────────────────────────────────────────────────────────

    def _build_main_ui(self):
        is_admin = self.current_user.role == "admin"

        # ─── Sidebar (Commerce Storefront / Stone-Black) ───────────────────────
        self.sidebar = ctk.CTkFrame(
            self, width=248, corner_radius=0,
            fg_color=(_NAV_BG, _NAV_BG)
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)

        # ── Brand Header ──────────────────────────────────────────────────────
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=80)
        brand_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(18, 6))
        brand_frame.pack_propagate(False)

        # Orange flame badge
        badge_frame = ctk.CTkFrame(
            brand_frame, width=44, height=44, corner_radius=12,
            fg_color=_NAV_ACTIVE
        )
        badge_frame.pack(side="left", padx=(0, 12))
        badge_frame.pack_propagate(False)
        ctk.CTkLabel(
            badge_frame, text="✦", font=("Segoe UI", 22, "bold"),
            text_color="white"
        ).place(relx=0.5, rely=0.5, anchor="center")

        brand_text = ctk.CTkFrame(brand_frame, fg_color="transparent")
        brand_text.pack(side="left", fill="y", expand=True)
        ctk.CTkLabel(
            brand_text, text="COSMÉTIQUE PRO",
            font=("Segoe UI", 13, "bold"), text_color="#FAFAFA"
        ).pack(anchor="w")
        ctk.CTkLabel(
            brand_text, text="Stock & Caisse 2.0",
            font=("Segoe UI", 10), text_color="#71717A"
        ).pack(anchor="w")

        current_row = 1

        # ── Caissier badge ────────────────────────────────────────────────────
        if not is_admin:
            badge = ctk.CTkFrame(
                self.sidebar, corner_radius=8,
                fg_color=("#7C3AED", "#7C3AED"), height=34
            )
            badge.grid(row=current_row, column=0, sticky="ew", padx=14, pady=(0, 6))
            badge.pack_propagate(False)
            ctk.CTkLabel(
                badge, text="💼  MODE CAISSIER  🔒",
                font=("Segoe UI", 10, "bold"), text_color="#EDE9FE"
            ).pack(expand=True)
            current_row += 1

        # ── Separator ─────────────────────────────────────────────────────────
        ctk.CTkFrame(
            self.sidebar, height=1, fg_color=_SEPARATOR
        ).grid(row=current_row, column=0, sticky="ew", padx=18, pady=(2, 8))
        current_row += 1

        # ── Nav scroll area ───────────────────────────────────────────────────
        self.sidebar.grid_rowconfigure(current_row, weight=1)
        self.nav_scroll = ctk.CTkScrollableFrame(
            self.sidebar, fg_color="transparent", scrollbar_fg_color="transparent"
        )
        self.nav_scroll.grid(row=current_row, column=0, sticky="nsew", padx=8, pady=0)
        self.nav_scroll.grid_columnconfigure(0, weight=1)
        current_row += 1

        # ── Separator before footer ───────────────────────────────────────────
        ctk.CTkFrame(
            self.sidebar, height=1, fg_color=_SEPARATOR
        ).grid(row=current_row, column=0, sticky="ew", padx=18, pady=(4, 4))
        current_row += 1

        # ── User footer card ──────────────────────────────────────────────────
        self.user_card = ctk.CTkFrame(
            self.sidebar, corner_radius=12,
            fg_color=("#27272A", "#27272A"), height=68
        )
        self.user_card.grid(row=current_row, column=0, sticky="ew", padx=12, pady=(0, 12))
        self.user_card.pack_propagate(False)

        user_info_f = ctk.CTkFrame(self.user_card, fg_color="transparent")
        user_info_f.pack(side="left", padx=12, pady=10, fill="y")

        role_badge = "👑 Administrateur" if is_admin else "💼 Caissier"
        role_color = _NAV_ACTIVE if is_admin else "#A78BFA"

        ctk.CTkLabel(
            user_info_f, text=self.current_user.full_name[:20],
            font=("Segoe UI", 12, "bold"), text_color="#FAFAFA", anchor="w"
        ).pack(anchor="w")
        ctk.CTkLabel(
            user_info_f, text=role_badge,
            font=("Segoe UI", 10), text_color=role_color, anchor="w"
        ).pack(anchor="w")

        ctk.CTkButton(
            self.user_card, text="🚪", width=36, height=36,
            font=("Segoe UI", 14), fg_color="transparent",
            hover_color=_SEPARATOR, text_color="#71717A",
            command=self._logout
        ).pack(side="right", padx=10)

        self._build_nav_buttons()

        # ─── Main Content Area ─────────────────────────────────────────────────
        self.main_container = ctk.CTkFrame(
            self, fg_color=("white", _BDY_BG_DARK), corner_radius=0
        )
        self.main_container.grid(row=0, column=1, sticky="nsew")
        self.main_container.grid_rowconfigure(1, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        # ── Top Header bar ────────────────────────────────────────────────────
        self.header_bar = ctk.CTkFrame(
            self.main_container, height=56, corner_radius=0,
            fg_color=(_HDR_BG_LIGHT, _HDR_BG_DARK),
            border_width=0
        )
        self.header_bar.grid(row=0, column=0, sticky="ew")
        self.header_bar.pack_propagate(False)

        # Orange left-accent stripe
        ctk.CTkFrame(
            self.header_bar, width=4, corner_radius=0,
            fg_color=_NAV_ACTIVE
        ).pack(side="left", fill="y")

        self.view_title_lbl = ctk.CTkLabel(
            self.header_bar, text="Tableau de Bord",
            font=("Segoe UI", 16, "bold"),
            text_color=("#1C1917", "#FAFAFA")
        )
        self.view_title_lbl.pack(side="left", padx=18)

        header_right = ctk.CTkFrame(self.header_bar, fg_color="transparent")
        header_right.pack(side="right", padx=16)

        if not is_admin:
            ctk.CTkLabel(
                header_right,
                text="🔒 Mode Caissier",
                font=("Segoe UI", 10, "bold"), text_color="#A78BFA"
            ).pack(side="left", padx=10)

        # Backup status pill
        self.backup_badge = ctk.CTkLabel(
            header_right,
            text="💾 Sync C:",
            font=("Segoe UI", 10, "bold"),
            text_color=COLORS["emerald"]
        )
        self.backup_badge.pack(side="left", padx=8)

        # Separator dot
        ctk.CTkLabel(
            header_right, text="·",
            font=("Segoe UI", 14), text_color="#52525B"
        ).pack(side="left")

        # Live clock
        self.clock_lbl = ctk.CTkLabel(
            header_right, text="",
            font=("Consolas", 12, "bold"),
            text_color=("#78716C", "#A1A1AA")
        )
        self.clock_lbl.pack(side="left", padx=8)

        # ── Views host ────────────────────────────────────────────────────────
        self.view_host = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.view_host.grid(row=1, column=0, sticky="nsew")
        self.view_host.grid_columnconfigure(0, weight=1)
        self.view_host.grid_rowconfigure(0, weight=1)

        self.views = {}

    def _build_nav_buttons(self):
        is_admin = self.current_user.role == "admin"

        if is_admin:
            items = [
                ("dashboard",     "Tableau de Bord",          "📊"),
                ("pos",           "Point de Vente (Caisse)",  "⚡"),
                ("products",      "Produits & Barcodes",      "💄"),
                ("stock",         "Gestion du Stock",         "📦"),
                ("alerts",        "Alertes & Ruptures",       "🚨"),
                ("suppliers",     "Fournisseurs & Achats",    "🏭"),
                ("cash_register", "Clôture de Caisse",        "💵"),
                ("reports",       "Rapports & Marges",        "📈"),
                ("settings",      "Paramètres & Config.",     "⚙️"),
            ]
        else:
            items = [
                ("pos",           "Point de Vente",     "⚡"),
                ("cash_register", "Clôture de Caisse",  "💵"),
            ]

        self.nav_buttons.clear()
        for key, label, icon in items:
            btn = ctk.CTkButton(
                self.nav_scroll,
                text=f"  {icon}   {label}",
                font=("Segoe UI", 12, "bold"),
                height=42,
                corner_radius=10,
                anchor="w",
                fg_color="transparent",
                text_color=_NAV_TEXT,
                hover_color=_NAV_HOVER,
                command=lambda k=key: self.navigate_to(k)
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons[key] = btn

    # ── Navigation ─────────────────────────────────────────────────────────────

    def navigate_to(self, view_name: str):
        is_admin = self.current_user and self.current_user.role == "admin"
        allowed = ADMIN_VIEWS if is_admin else CASHIER_VIEWS
        if view_name not in allowed:
            view_name = "pos"

        if self.current_view_name == view_name:
            return

        for k, btn in self.nav_buttons.items():
            if k == view_name:
                btn.configure(
                    fg_color=_NAV_ACTIVE,
                    text_color=_NAV_TEXT_ACT
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=_NAV_TEXT
                )

        for v in self.view_host.winfo_children():
            v.pack_forget()

        if view_name not in self.views:
            builders = {
                "dashboard":     lambda: DashboardView(self.view_host, on_navigate=self.navigate_to),
                "pos":           lambda: POSView(self.view_host),
                "products":      lambda: ProductsView(self.view_host),
                "stock":         lambda: StockView(self.view_host),
                "alerts":        lambda: AlertsView(self.view_host, on_navigate=self.navigate_to),
                "suppliers":     lambda: SuppliersView(self.view_host),
                "cash_register": lambda: CashRegisterView(self.view_host),
                "reports":       lambda: ReportsView(self.view_host),
                "settings":      lambda: SettingsView(self.view_host),
            }
            if view_name in builders:
                self.views[view_name] = builders[view_name]()

        view = self.views.get(view_name)
        if not view:
            return

        view.pack(fill="both", expand=True)

        titles = {
            "dashboard":     "Tableau de Bord – Métriques Clés",
            "pos":           "Point de Vente – Caisse & Scan Douchette",
            "products":      "Catalogue Produits & Étiquettes Codes-barres",
            "stock":         "Mouvements de Stock, Réceptions & Inventaire",
            "alerts":        "Centre de Surveillance des Alertes",
            "suppliers":     "Fournisseurs & Bons de Commande",
            "cash_register": "Gestion & Clôture de Caisse",
            "reports":       "Analyse Financière & Journal des Ventes",
            "settings":      "Paramètres Généraux & Configuration",
        }
        self.view_title_lbl.configure(text=titles.get(view_name, "CosmétiquePro"))
        self.current_view_name = view_name

        # Auto-refresh on navigate
        if hasattr(view, "load_data"):
            view.load_data()
        elif hasattr(view, "load_products"):
            view.load_products()
        elif hasattr(view, "load_alerts"):
            view.load_alerts()
        elif hasattr(view, "refresh_session_ui"):
            view.refresh_session_ui()

    # ── Background Updates ─────────────────────────────────────────────────────

    def _start_background_updates(self):
        """Updates clock, backup badge, and alert counter every second."""
        now = datetime.datetime.now().strftime("%d/%m/%Y  %H:%M:%S")

        if hasattr(self, "clock_lbl") and self.clock_lbl.winfo_exists():
            self.clock_lbl.configure(text=now)

        if hasattr(self, "backup_badge") and self.backup_badge.winfo_exists():
            try:
                status = BackupService.get_backup_status()
                if status["secondary"]["drive_present"] and status["secondary"]["exists"]:
                    self.backup_badge.configure(
                        text="💾 C: & D: Sync ✔",
                        text_color=COLORS["emerald"]
                    )
                else:
                    self.backup_badge.configure(
                        text="💾 C: Actif (D: Absent)",
                        text_color=COLORS["warning"]
                    )
            except Exception:
                pass

        if "alerts" in self.nav_buttons and self.nav_buttons["alerts"].winfo_exists():
            try:
                tot, low, out, exp = StockService.get_total_alerts_count()
                if tot > 0:
                    alert_text = f"  🚨   Alertes ({tot})"
                    alert_col = COLORS["danger"] if self.current_view_name != "alerts" else _NAV_TEXT_ACT
                else:
                    alert_text = "  🚨   Alertes & Ruptures"
                    alert_col = _NAV_TEXT if self.current_view_name != "alerts" else _NAV_TEXT_ACT
                self.nav_buttons["alerts"].configure(text=alert_text, text_color=alert_col)
            except Exception:
                pass

        self.after(1000, self._start_background_updates)
