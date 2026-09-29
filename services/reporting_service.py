import datetime
from pathlib import Path
from database.db_manager import get_db
from config import EXPORTS_DIR

class ReportingService:
    @staticmethod
    def get_dashboard_kpis():
        """Récupère les KPI clés : Ventes du jour, Ventes du mois, Total produits, Valeur du stock."""
        db = get_db()
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        first_of_month = datetime.datetime.now().strftime("%Y-%m-01")

        # Ventes du jour
        today_rows = db.execute_query("""
            SELECT 
                COUNT(*) as count, 
                COALESCE(SUM(total_ttc), 0) as total,
                COALESCE(SUM(discount_amount), 0) as discounts
            FROM sales 
            WHERE DATE(created_at) = ?
        """, (today,))
        today_kpi = today_rows[0]

        # Ventes du mois & Marge brute
        month_rows = db.execute_query("""
            SELECT 
                COUNT(DISTINCT s.id) as count,
                COALESCE(SUM(s.total_ttc), 0) as total_sales,
                COALESCE(SUM(si.qty * si.purchase_price), 0) as total_cost
            FROM sales s
            JOIN sale_items si ON s.id = si.sale_id
            WHERE DATE(s.created_at) >= ?
        """, (first_of_month,))
        month_kpi = month_rows[0]
        month_margin = month_kpi["total_sales"] - month_kpi["total_cost"]

        # Statistiques Stock
        stock_rows = db.execute_query("""
            SELECT 
                COUNT(*) as total_products,
                COALESCE(SUM(stock_qty), 0) as total_units,
                COALESCE(SUM(stock_qty * purchase_price), 0) as stock_cost_value,
                COALESCE(SUM(stock_qty * sale_price), 0) as stock_sale_value
            FROM products 
            WHERE is_active = 1
        """)
        stock_kpi = stock_rows[0]

        return {
            "today_sales": today_kpi["total"],
            "today_count": today_kpi["count"],
            "month_sales": month_kpi["total_sales"],
            "month_margin": month_margin,
            "total_products": stock_kpi["total_products"],
            "total_units": stock_kpi["total_units"],
            "stock_value": stock_kpi["stock_sale_value"],
            "stock_cost": stock_kpi["stock_cost_value"],
            "potential_profit": stock_kpi["stock_sale_value"] - stock_kpi["stock_cost_value"]
        }

    @staticmethod
    def get_sales_trend(days=7):
        """Récupère l'historique du CA des N derniers jours pour le graphique."""
        db = get_db()
        date_threshold = (datetime.datetime.now() - datetime.timedelta(days=days-1)).strftime("%Y-%m-%d")
        
        rows = db.execute_query("""
            SELECT 
                DATE(created_at) as sale_date,
                COALESCE(SUM(total_ttc), 0) as daily_total,
                COUNT(*) as daily_count
            FROM sales 
            WHERE DATE(created_at) >= ?
            GROUP BY DATE(created_at)
            ORDER BY DATE(created_at) ASC
        """, (date_threshold,))

        # Créer un dictionnaire pour combler les jours à 0
        data_dict = {r["sale_date"]: r["daily_total"] for r in rows}
        dates = []
        totals = []
        for i in range(days):
            d = (datetime.datetime.now() - datetime.timedelta(days=days-1-i)).strftime("%Y-%m-%d")
            d_short = (datetime.datetime.now() - datetime.timedelta(days=days-1-i)).strftime("%d/%m")
            dates.append(d_short)
            totals.append(data_dict.get(d, 0.0))

        return dates, totals

    @staticmethod
    def get_top_selling_products(limit=5):
        """Top des produits les plus vendus en volume et valeur."""
        db = get_db()
        return db.execute_query("""
            SELECT 
                si.product_name,
                SUM(si.qty) as total_qty,
                SUM(si.total_line) as total_revenue,
                SUM(si.total_line - (si.qty * si.purchase_price)) as total_profit
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            GROUP BY si.product_id
            ORDER BY total_qty DESC
            LIMIT ?
        """, (limit,))

    @staticmethod
    def get_sales_by_category():
        """Répartition des ventes par catégorie cosmétique."""
        db = get_db()
        rows = db.execute_query("""
            SELECT 
                p.category,
                COALESCE(SUM(si.total_line), 0) as total_sales,
                COUNT(si.id) as items_sold
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            GROUP BY p.category
            ORDER BY total_sales DESC
        """)
        categories = [r["category"] for r in rows if r["total_sales"] > 0]
        values = [r["total_sales"] for r in rows if r["total_sales"] > 0]
        return categories, values

    @staticmethod
    def export_sales_to_excel(start_date=None, end_date=None):
        """Exporte l'historique complet des ventes en fichier Excel xlsx."""
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

        db = get_db()
        query = """
            SELECT 
                s.sale_code,
                s.created_at,
                s.customer_name,
                s.payment_method,
                s.total_ht,
                s.total_tva,
                s.discount_amount,
                s.total_ttc,
                u.full_name as cashier
            FROM sales s
            LEFT JOIN users u ON s.user_id = u.id
            WHERE 1=1
        """
        params = []
        if start_date:
            query += " AND DATE(s.created_at) >= ?"
            params.append(start_date)
        if end_date:
            query += " AND DATE(s.created_at) <= ?"
            params.append(end_date)
        query += " ORDER BY s.created_at DESC"

        sales = db.execute_query(query, params)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Journal des Ventes"

        # Styles
        header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
        regular_font = Font(name="Segoe UI", size=10)
        bold_font = Font(name="Segoe UI", size=10, bold=True)

        headers = ["N° Vente", "Date & Heure", "Client", "Paiement", "Total HT (DA)", "TVA (DA)", "Remise (DA)", "Total TTC (DA)", "Caissier"]
        ws.append(headers)

        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        row_idx = 2
        total_sum = 0.0
        for s in sales:
            ws.append([
                s["sale_code"],
                s["created_at"],
                s["customer_name"],
                s["payment_method"].capitalize(),
                round(s["total_ht"], 2),
                round(s["total_tva"], 2),
                round(s["discount_amount"], 2),
                round(s["total_ttc"], 2),
                s["cashier"]
            ])
            total_sum += s["total_ttc"]
            row_idx += 1

        # Ligne Total
        ws.append(["TOTAL GÉNÉRAL", "", "", "", "", "", "", round(total_sum, 2), ""])
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.font = bold_font
            cell.fill = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")

        # Ajuster largeurs
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = EXPORTS_DIR / f"Ventes_Export_{timestamp}.xlsx"
        wb.save(export_path)
        return str(export_path)
