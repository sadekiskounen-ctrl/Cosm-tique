import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ui.theme import FONTS, COLORS
from ui.components.kpi_card import KPICard
from services.reporting_service import ReportingService
from services.stock_service import StockService

class DashboardView(ctk.CTkScrollableFrame):
    def __init__(self, parent, on_navigate):
        super().__init__(parent, fg_color="transparent")
        self.on_navigate = on_navigate

        self.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Header Title
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=4, sticky="ew", padx=15, pady=(15, 10))
        
        ctk.CTkLabel(
            header_frame,
            text="Tableau de Bord & Métriques Clés",
            font=FONTS["title_medium"],
            text_color=("#0F172A", "#F8FAFC")
        ).pack(side="left")

        # Refresh button
        self.refresh_btn = ctk.CTkButton(
            header_frame,
            text="🔄 Actualiser",
            width=110,
            height=32,
            font=FONTS["caption_bold"],
            fg_color=("#E2E8F0", "#334155"),
            text_color=("#0F172A", "#F8FAFC"),
            hover_color=("#CBD5E1", "#475569"),
            command=self.load_data
        )
        self.refresh_btn.pack(side="right")

        # 1. Row of 4 KPI Cards
        self.kpi_today = KPICard(self, "Ventes du Jour", "0 DA", "0 transaction(s)", "💰", COLORS["success"])
        self.kpi_today.grid(row=1, column=0, padx=8, pady=8, sticky="nsew")

        self.kpi_month = KPICard(self, "Chiffre du Mois", "0 DA", "Mois en cours", "📈", COLORS["primary"])
        self.kpi_month.grid(row=1, column=1, padx=8, pady=8, sticky="nsew")

        self.kpi_margin = KPICard(self, "Marge Brute Estimée", "0 DA", "Bénéfice réalisé", "💎", COLORS["info"])
        self.kpi_margin.grid(row=1, column=2, padx=8, pady=8, sticky="nsew")

        self.kpi_stock = KPICard(self, "Valeur Stock", "0 DA", "0 articles en stock", "📦", COLORS["warning"])
        self.kpi_stock.grid(row=1, column=3, padx=8, pady=8, sticky="nsew")

        # 2. Alert Banner Row
        self.alert_banner = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=("#FEF2F2", "#1E293B"),
            border_width=1,
            border_color=COLORS["danger"]
        )
        self.alert_banner.grid(row=2, column=0, columnspan=4, sticky="ew", padx=8, pady=12)
        
        self.alert_banner_lbl = ctk.CTkLabel(
            self.alert_banner,
            text="🚨 Alertes : 0 rupture(s), 0 stock(s) bas, 0 péremption(s) proche(s)",
            font=FONTS["body_bold"],
            text_color=COLORS["danger"]
        )
        self.alert_banner_lbl.pack(side="left", padx=20, pady=12)

        self.view_alerts_btn = ctk.CTkButton(
            self.alert_banner,
            text="Gérer les Alertes →",
            width=140,
            height=30,
            font=FONTS["caption_bold"],
            fg_color=COLORS["danger"],
            hover_color=COLORS["danger_hover"],
            command=lambda: self.on_navigate("alerts")
        )
        self.view_alerts_btn.pack(side="right", padx=15, pady=8)

        # 3. Chart Frames
        self.charts_container = ctk.CTkFrame(self, fg_color="transparent")
        self.charts_container.grid(row=3, column=0, columnspan=4, sticky="nsew", padx=8, pady=10)
        self.charts_container.grid_columnconfigure((0, 1), weight=1)

        # Chart 1: Sales Trend
        self.chart1_card = ctk.CTkFrame(self.charts_container, corner_radius=12, fg_color=("#FFFFFF", "#1E293B"), border_width=1, border_color=("#E2E8F0", "#334155"))
        self.chart1_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=0)
        
        ctk.CTkLabel(self.chart1_card, text="Évolution du CA (7 Derniers Jours)", font=FONTS["body_bold"], text_color=("#0F172A", "#F8FAFC")).pack(anchor="w", padx=15, pady=(12, 4))
        self.fig1_container = ctk.CTkFrame(self.chart1_card, fg_color="transparent", height=240)
        self.fig1_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Chart 2: Top Selling Products
        self.chart2_card = ctk.CTkFrame(self.charts_container, corner_radius=12, fg_color=("#FFFFFF", "#1E293B"), border_width=1, border_color=("#E2E8F0", "#334155"))
        self.chart2_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=0)

        ctk.CTkLabel(self.chart2_card, text="Top Produits Vendus", font=FONTS["body_bold"], text_color=("#0F172A", "#F8FAFC")).pack(anchor="w", padx=15, pady=(12, 4))
        self.fig2_container = ctk.CTkFrame(self.chart2_card, fg_color="transparent", height=240)
        self.fig2_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.load_data()

    def load_data(self):
        # 1. Update KPIs
        kpis = ReportingService.get_dashboard_kpis()
        self.kpi_today.update_value(f"{kpis['today_sales']:,.0f} DA".replace(",", " "), f"{kpis['today_count']} vente(s)")
        self.kpi_month.update_value(f"{kpis['month_sales']:,.0f} DA".replace(",", " "), "Ce mois-ci")
        self.kpi_margin.update_value(f"{kpis['month_margin']:,.0f} DA".replace(",", " "), "Marge nette")
        self.kpi_stock.update_value(f"{kpis['stock_value']:,.0f} DA".replace(",", " "), f"{kpis['total_products']} références ({kpis['total_units']} u.)")

        # 2. Update Alerts Banner
        tot_alerts, low, out, exp = StockService.get_total_alerts_count()
        self.alert_banner_lbl.configure(text=f"🚨 Alertes Actives : {out} rupture(s) | {low} stock(s) bas | {exp} péremption(s) proche(s)")
        if tot_alerts == 0:
            self.alert_banner.configure(fg_color=("#ECFDF5", "#1E293B"), border_color=COLORS["success"])
            self.alert_banner_lbl.configure(text="✅ Tous les stocks sont au niveau optimal et aucun produit n'est en alerte.", text_color=COLORS["success"])
        else:
            self.alert_banner.configure(fg_color=("#FEF2F2", "#1E293B"), border_color=COLORS["danger"])
            self.alert_banner_lbl.configure(text_color=COLORS["danger"])

        # 3. Render Matplotlib Charts
        self._render_sales_chart()
        self._render_top_products_chart()

    def _render_sales_chart(self):
        for widget in self.fig1_container.winfo_children():
            widget.destroy()

        dates, totals = ReportingService.get_sales_trend(days=7)
        is_dark = ctk.get_appearance_mode() == "Dark"
        bg_color = "#1E293B" if is_dark else "#FFFFFF"
        text_color = "#94A3B8" if is_dark else "#475569"

        fig = Figure(figsize=(5, 2.4), dpi=90, facecolor=bg_color)
        ax = fig.add_subplot(111)
        ax.set_facecolor(bg_color)

        ax.plot(dates, totals, marker="o", color=COLORS["primary"], linewidth=2.5, markersize=6)
        ax.fill_between(dates, totals, color=COLORS["primary"], alpha=0.15)

        ax.tick_params(colors=text_color, labelsize=8)
        for spine in ax.spines.values():
            spine.set_color("#334155" if is_dark else "#E2E8F0")

        ax.grid(True, linestyle="--", alpha=0.3, color=text_color)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.fig1_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _render_top_products_chart(self):
        for widget in self.fig2_container.winfo_children():
            widget.destroy()

        top_items = ReportingService.get_top_selling_products(limit=5)
        is_dark = ctk.get_appearance_mode() == "Dark"
        bg_color = "#1E293B" if is_dark else "#FFFFFF"
        text_color = "#94A3B8" if is_dark else "#475569"

        fig = Figure(figsize=(5, 2.4), dpi=90, facecolor=bg_color)
        ax = fig.add_subplot(111)
        ax.set_facecolor(bg_color)

        if top_items:
            names = [row["product_name"][:14] for row in top_items]
            qtys = [row["total_qty"] for row in top_items]
            names.reverse()
            qtys.reverse()

            bars = ax.barh(names, qtys, color=COLORS["emerald"], height=0.5)
            ax.tick_params(colors=text_color, labelsize=8)
            for spine in ax.spines.values():
                spine.set_color("#334155" if is_dark else "#E2E8F0")
            ax.grid(True, linestyle="--", alpha=0.2, color=text_color, axis="x")
        else:
            ax.text(0.5, 0.5, "Aucune vente enregistrée", horizontalalignment='center', verticalalignment='center', color=text_color, transform=ax.transAxes)
            ax.axis('off')

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.fig2_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
