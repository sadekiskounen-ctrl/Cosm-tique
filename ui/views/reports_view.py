import customtkinter as ctk
import datetime
from ui.theme import FONTS, COLORS
from database.db_manager import get_db
from services.reporting_service import ReportingService
from ui.components.modern_table import ModernTable
from ui.components.kpi_card import KPICard
from ui.components.notification import ToastNotification

class ReportsView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # 1. Top Controls Bar
        self.top_bar = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#1E293B"), corner_radius=12, height=60)
        self.top_bar.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        self.top_bar.pack_propagate(False)

        ctk.CTkLabel(self.top_bar, text="📊 Journal des Ventes & Analyse Financière", font=FONTS["title_small"]).pack(side="left", padx=15)

        # Period Filter
        self.period_menu = ctk.CTkOptionMenu(
            self.top_bar,
            values=["Aujourd'hui", "7 Derniers Jours", "Ce Mois-ci", "Toutes les Ventes"],
            height=34,
            font=FONTS["body"],
            command=lambda p: self.load_sales_data()
        )
        self.period_menu.pack(side="left", padx=10)

        # Export Excel Button
        self.export_btn = ctk.CTkButton(
            self.top_bar,
            text="📑 Exporter en Excel (.xlsx)",
            height=36,
            font=FONTS["body_bold"],
            fg_color=COLORS["emerald"],
            hover_color=COLORS["emerald_hover"],
            command=self._export_excel
        )
        self.export_btn.pack(side="right", padx=15)

        # 2. Summary Mini-Cards
        self.kpi_row = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_row.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 10))
        self.kpi_row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.card_rev = KPICard(self.kpi_row, "Chiffre d'Affaires", "0 DA", "Période sélectionnée", "💰", COLORS["primary"])
        self.card_rev.grid(row=0, column=0, padx=4, sticky="nsew")

        self.card_cost = KPICard(self.kpi_row, "Coût d'Achat Global", "0 DA", "Marchandises vendues", "📦", COLORS["warning"])
        self.card_cost.grid(row=0, column=1, padx=4, sticky="nsew")

        self.card_margin = KPICard(self.kpi_row, "Marge Nette Réalisée", "0 DA", "Bénéfice brut", "💎", COLORS["emerald"])
        self.card_margin.grid(row=0, column=2, padx=4, sticky="nsew")

        self.card_tx = KPICard(self.kpi_row, "Transactions", "0", "Tickets émis", "🧾", COLORS["info"])
        self.card_tx.grid(row=0, column=3, padx=4, sticky="nsew")

        # 3. Sales Table
        cols = [
            ("N° Ticket", 3, "w"),
            ("Date & Heure", 3, "w"),
            ("Client", 3, "w"),
            ("Paiement", 2, "center"),
            ("Articles", 2, "center"),
            ("Remise", 2, "e"),
            ("Total TTC", 2, "e"),
            ("Caissier", 2, "w")
        ]
        self.sales_table = ModernTable(self, cols)
        self.sales_table.grid(row=2, column=0, sticky="nsew", padx=15, pady=(0, 15))

        self.load_sales_data()

    def _get_date_filter(self):
        choice = self.period_menu.get()
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        if choice == "Aujourd'hui":
            return today, today
        elif choice == "7 Derniers Jours":
            start = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
            return start, today
        elif choice == "Ce Mois-ci":
            start = datetime.datetime.now().strftime("%Y-%m-01")
            return start, today
        else:
            return None, None

    def load_sales_data(self):
        start_d, end_d = self._get_date_filter()
        db = get_db()
        
        query = """
            SELECT s.*, u.full_name as cashier_name, COUNT(si.id) as items_count, COALESCE(SUM(si.qty * si.purchase_price), 0) as total_cost
            FROM sales s
            LEFT JOIN users u ON s.user_id = u.id
            LEFT JOIN sale_items si ON s.id = si.sale_id
            WHERE 1=1
        """
        params = []
        if start_d:
            query += " AND DATE(s.created_at) >= ?"
            params.append(start_d)
        if end_d:
            query += " AND DATE(s.created_at) <= ?"
            params.append(end_d)

        query += " GROUP BY s.id ORDER BY s.created_at DESC"

        sales = db.execute_query(query, params)

        tot_rev = 0.0
        tot_cost = 0.0
        table_rows = []

        for s in sales:
            tot_rev += s["total_ttc"]
            tot_cost += s["total_cost"]

            table_rows.append([
                s["sale_code"],
                s["created_at"][:16] if s["created_at"] else "-",
                s["customer_name"],
                s["payment_method"].capitalize(),
                f"{s['items_count']} art.",
                f"{s['discount_amount']:,.2f} DA" if s["discount_amount"] > 0 else "-",
                f"{s['total_ttc']:,.2f} DA",
                s["cashier_name"] or "Caissier"
            ])

        self.sales_table.set_data(table_rows)

        # Update KPI Cards
        margin = tot_rev - tot_cost
        self.card_rev.update_value(f"{tot_rev:,.0f} DA".replace(",", " "))
        self.card_cost.update_value(f"{tot_cost:,.0f} DA".replace(",", " "))
        self.card_margin.update_value(f"{margin:,.0f} DA".replace(",", " "))
        self.card_tx.update_value(f"{len(sales)} vente(s)")

    def _export_excel(self):
        start_d, end_d = self._get_date_filter()
        try:
            path = ReportingService.export_sales_to_excel(start_d, end_d)
            ToastNotification.show(self, f"Export réussi : {path}", "success", duration_ms=4500)
        except Exception as e:
            ToastNotification.show(self, f"Erreur export : {e}", "danger")
