import datetime
from database.db_manager import get_db

class POSService:
    def __init__(self):
        self.cart = []  # List of dicts: {'product': product_dict, 'qty': int, 'unit_price': float, 'discount_pct': float, 'total': float}
        self.global_discount_pct = 0.0

    def add_product_by_barcode(self, barcode):
        """Scanne un code-barre et l'ajoute au panier ou incrémente la quantité."""
        db = get_db()
        rows = db.execute_query("SELECT * FROM products WHERE barcode = ? AND is_active = 1", (barcode.strip(),))
        if not rows:
            return False, "Produit non trouvé ou code-barre inconnu"
        
        product = dict(rows[0])
        return self.add_product(product, qty=1)

    def add_product(self, product, qty=1):
        """Ajoute un produit au panier ou incrémente sa quantité."""
        product_id = product["id"]
        # Vérifier si déjà dans le panier
        for item in self.cart:
            if item["product"]["id"] == product_id:
                if item["qty"] + qty > product["stock_qty"]:
                    return False, f"Stock insuffisant (Disponible : {product['stock_qty']})"
                item["qty"] += qty
                self._recalculate_item(item)
                return True, "Quantité incrémentée"

        # Vérifier stock disponible
        if qty > product["stock_qty"]:
            return False, f"Stock insuffisant (Disponible : {product['stock_qty']})"

        new_item = {
            "product": product,
            "qty": qty,
            "unit_price": product["sale_price"],
            "discount_pct": 0.0,
            "total": product["sale_price"] * qty
        }
        self.cart.append(new_item)
        return True, "Produit ajouté au panier"

    def update_item_qty(self, index, new_qty):
        if 0 <= index < len(self.cart):
            if new_qty <= 0:
                self.cart.pop(index)
                return True, "Article supprimé"
            item = self.cart[index]
            if new_qty > item["product"]["stock_qty"]:
                return False, f"Stock insuffisant (Disponible : {item['product']['stock_qty']})"
            item["qty"] = new_qty
            self._recalculate_item(item)
            return True, "Quantité mise à jour"
        return False, "Index invalide"

    def update_item_price(self, index, new_price):
        if 0 <= index < len(self.cart):
            self.cart[index]["unit_price"] = float(new_price)
            self._recalculate_item(self.cart[index])
            return True, "Prix mis à jour"
        return False, "Index invalide"

    def update_item_discount(self, index, discount_pct):
        if 0 <= index < len(self.cart):
            self.cart[index]["discount_pct"] = float(discount_pct)
            self._recalculate_item(self.cart[index])
            return True, "Remise appliquée"
        return False, "Index invalide"

    def remove_item(self, index):
        if 0 <= index < len(self.cart):
            self.cart.pop(index)
            return True, "Article retiré"
        return False, "Index invalide"

    def clear_cart(self):
        self.cart.clear()
        self.global_discount_pct = 0.0

    def _recalculate_item(self, item):
        raw = item["qty"] * item["unit_price"]
        item["total"] = raw * (1 - (item["discount_pct"] / 100.0))

    def get_totals(self):
        """Retourne (Total Brut, Total Remises, Total Net TTC, Total TVA, Total Articles)."""
        subtotal = sum(item["qty"] * item["unit_price"] for item in self.cart)
        lines_total = sum(item["total"] for item in self.cart)
        
        # Remise globale
        discount_amount = (subtotal - lines_total) + (lines_total * (self.global_discount_pct / 100.0))
        final_total = max(0.0, lines_total * (1 - (self.global_discount_pct / 100.0)))
        
        # Estimation TVA moyenne
        tva_total = sum(item["total"] * (item["product"].get("vat_rate", 0) / 100.0) for item in self.cart)
        ht_total = final_total - tva_total
        total_items = sum(item["qty"] for item in self.cart)

        return {
            "subtotal": round(subtotal, 2),
            "discount_amount": round(discount_amount, 2),
            "final_total": round(final_total, 2),
            "ht_total": round(ht_total, 2),
            "tva_total": round(tva_total, 2),
            "total_items": total_items
        }

    # Session de Caisse (Fond de caisse, clôture journalière)
    @staticmethod
    def get_current_session(user_id=None):
        db = get_db()
        query = "SELECT * FROM cash_sessions WHERE status = 'open'"
        params = []
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        query += " ORDER BY id DESC LIMIT 1"
        rows = db.execute_query(query, params)
        return rows[0] if rows else None

    @staticmethod
    def open_cash_session(user_id, opening_amount):
        """Ouvre une nouvelle session de caisse avec un fond de caisse."""
        db = get_db()
        # Vérifier si une session est déjà ouverte
        current = POSService.get_current_session(user_id)
        if current:
            return False, "Une session de caisse est déjà ouverte pour cet utilisateur."
        
        try:
            session_id = db.execute_query("""
                INSERT INTO cash_sessions (user_id, opening_amount, theoretical_cash, status)
                VALUES (?, ?, ?, 'open')
            """, (user_id, float(opening_amount), float(opening_amount)), commit=True)
            return True, session_id
        except Exception as e:
            return False, f"Erreur lors de l'ouverture de caisse : {e}"

    @staticmethod
    def close_cash_session(session_id, real_cash, notes=""):
        """Clôture la caisse journalière avec calcul des écarts."""
        db = get_db()
        rows = db.execute_query("SELECT * FROM cash_sessions WHERE id = ?", (session_id,))
        if not rows:
            return False, "Session introuvable"
        
        session = rows[0]
        # Calculer le total des ventes en espèces de la session
        sales_rows = db.execute_query("""
            SELECT 
                COUNT(*) as sales_count,
                COALESCE(SUM(total_ttc), 0) as total_sales,
                COALESCE(SUM(CASE WHEN payment_method = 'especes' THEN total_ttc ELSE 0 END), 0) as cash_sales
            FROM sales 
            WHERE session_id = ?
        """, (session_id,))
        
        stats = sales_rows[0]
        theoretical_cash = session["opening_amount"] + stats["cash_sales"]
        real_amount = float(real_cash)
        diff = real_amount - theoretical_cash

        db.execute_query("""
            UPDATE cash_sessions 
            SET closing_date = CURRENT_TIMESTAMP,
                theoretical_cash = ?,
                real_cash = ?,
                cash_difference = ?,
                total_sales_amount = ?,
                total_sales_count = ?,
                status = 'closed',
                notes = ?
            WHERE id = ?
        """, (theoretical_cash, real_amount, diff, stats["total_sales"], stats["sales_count"], notes, session_id), commit=True)

        return True, {
            "session_id": session_id,
            "opening_amount": session["opening_amount"],
            "total_sales": stats["total_sales"],
            "cash_sales": stats["cash_sales"],
            "theoretical_cash": theoretical_cash,
            "real_cash": real_amount,
            "difference": diff,
            "sales_count": stats["sales_count"]
        }

    # Finalisation de la vente
    def complete_sale(self, user_id, payment_method="especes", amount_received=0.0, customer_name="Client Passant"):
        """Valide la vente, décrémente les stocks atomiquement et enregistre les lignes."""
        if not self.cart:
            return False, "Le panier est vide"

        totals = self.get_totals()
        final_total = totals["final_total"]
        
        if payment_method == "especes" and amount_received < final_total:
            return False, f"Montant reçu insuffisant ({amount_received} < {final_total} DA)"

        change_given = max(0.0, amount_received - final_total) if payment_method == "especes" else 0.0

        db = get_db()
        session = self.get_current_session(user_id)
        session_id = session["id"] if session else None

        sale_code = f"VTE-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

        try:
            # 1. Enregistrer l'en-tête de vente
            sale_id = db.execute_query("""
                INSERT INTO sales (sale_code, session_id, user_id, total_ht, total_tva, discount_amount, total_ttc, payment_method, amount_received, change_given, customer_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (sale_code, session_id, user_id, totals["ht_total"], totals["tva_total"], totals["discount_amount"], final_total, payment_method, float(amount_received), change_given, customer_name), commit=True)

            # 2. Enregistrer chaque ligne et déduire le stock
            for item in self.cart:
                p = item["product"]
                qty = item["qty"]
                unit_price = item["unit_price"]
                line_total = item["total"]
                purchase_price = p.get("purchase_price", 0.0)

                # Ligne de vente
                db.execute_query("""
                    INSERT INTO sale_items (sale_id, product_id, product_name, barcode, unit_price, purchase_price, qty, discount_pct, total_line)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (sale_id, p["id"], p["name"], p["barcode"], unit_price, purchase_price, qty, item["discount_pct"], line_total), commit=True)

                # Mise à jour stock produit
                old_stock = p["stock_qty"]
                new_stock = old_stock - qty
                db.execute_query("UPDATE products SET stock_qty = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_stock, p["id"]), commit=True)

                # Mouvement de stock audit
                db.execute_query("""
                    INSERT INTO stock_movements (product_id, movement_type, qty, old_stock, new_stock, unit_price, reason, user_id)
                    VALUES (?, 'vente', ?, ?, ?, ?, ?, ?)
                """, (p["id"], -qty, old_stock, new_stock, unit_price, f"Vente {sale_code}", user_id), commit=True)

            sale_details = {
                "sale_id": sale_id,
                "sale_code": sale_code,
                "date": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "cart": list(self.cart),
                "totals": totals,
                "payment_method": payment_method,
                "amount_received": amount_received,
                "change_given": change_given,
                "customer_name": customer_name
            }

            self.clear_cart()
            return True, sale_details

        except Exception as e:
            return False, f"Erreur lors de l'enregistrement de la vente : {e}"
