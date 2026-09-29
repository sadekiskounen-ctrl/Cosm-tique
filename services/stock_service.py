from datetime import datetime, timedelta
from database.db_manager import get_db
from config import CATEGORIES

class StockService:
    @staticmethod
    def get_all_categories():
        """Retourne la liste fusionnée des catégories par défaut et personnalisées."""
        try:
            db = get_db()
            rows = db.execute_query("SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category != '' ORDER BY category ASC")
            existing = [r["category"] for r in rows if r["category"]]
            all_cats = list(dict.fromkeys(CATEGORIES + existing))
            return all_cats
        except Exception:
            return CATEGORIES


    @staticmethod
    def get_products(search="", category="Toutes", sort_by="name", active_only=True):
        """Récupère la liste des produits avec filtres."""
        db = get_db()
        query = """
            SELECT p.*, s.name as supplier_name 
            FROM products p
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE 1=1
        """
        params = []
        if active_only:
            query += " AND p.is_active = 1"
        if category and category != "Toutes":
            query += " AND p.category = ?"
            params.append(category)
        if search:
            query += " AND (p.name LIKE ? OR p.barcode LIKE ? OR p.brand LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
        
        # Tri
        sort_dict = {
            "name": "p.name ASC",
            "stock_asc": "p.stock_qty ASC",
            "stock_desc": "p.stock_qty DESC",
            "price_asc": "p.sale_price ASC",
            "price_desc": "p.sale_price DESC",
            "expiry": "p.expiry_date ASC"
        }
        order_clause = sort_dict.get(sort_by, "p.name ASC")
        query += f" ORDER BY {order_clause}"
        
        return db.execute_query(query, params)

    @staticmethod
    def get_product_by_id(product_id):
        db = get_db()
        rows = db.execute_query("""
            SELECT p.*, s.name as supplier_name 
            FROM products p
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE p.id = ?
        """, (product_id,))
        return rows[0] if rows else None

    @staticmethod
    def get_product_by_barcode(barcode):
        db = get_db()
        rows = db.execute_query("""
            SELECT p.*, s.name as supplier_name 
            FROM products p
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE p.barcode = ? AND p.is_active = 1
        """, (barcode.strip(),))
        return rows[0] if rows else None

    @staticmethod
    def add_product(barcode, name, brand, category, purchase_price, sale_price, vat_rate, initial_stock, min_alert, expiry_date, supplier_id, user_id=1):
        """Ajoute un nouveau produit et enregistre le mouvement initial."""
        db = get_db()
        try:
            pid = db.execute_query("""
                INSERT INTO products (barcode, name, brand, category, purchase_price, sale_price, vat_rate, stock_qty, min_stock_alert, expiry_date, supplier_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (barcode.strip(), name.strip(), brand.strip() if brand else "", category, float(purchase_price), float(sale_price), float(vat_rate or 0), int(initial_stock), int(min_alert), expiry_date or None, supplier_id or None), commit=True)
            
            if initial_stock > 0:
                db.execute_query("""
                    INSERT INTO stock_movements (product_id, movement_type, qty, old_stock, new_stock, unit_price, reason, user_id)
                    VALUES (?, 'reception', ?, 0, ?, ?, 'Stock Initial', ?)
                """, (pid, int(initial_stock), int(initial_stock), float(purchase_price), user_id), commit=True)
            return True, "Produit ajouté avec succès"
        except Exception as e:
            return False, f"Erreur : Le code-barre existe peut-être déjà ({e})"

    @staticmethod
    def update_product(product_id, barcode, name, brand, category, purchase_price, sale_price, vat_rate, min_alert, expiry_date, supplier_id):
        db = get_db()
        try:
            db.execute_query("""
                UPDATE products 
                SET barcode = ?, name = ?, brand = ?, category = ?, purchase_price = ?, sale_price = ?, vat_rate = ?, min_stock_alert = ?, expiry_date = ?, supplier_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (barcode.strip(), name.strip(), brand.strip() if brand else "", category, float(purchase_price), float(sale_price), float(vat_rate or 0), int(min_alert), expiry_date or None, supplier_id or None, product_id), commit=True)
            return True, "Produit mis à jour avec succès"
        except Exception as e:
            return False, f"Erreur lors de la modification : {e}"

    @staticmethod
    def delete_product(product_id):
        db = get_db()
        db.execute_query("UPDATE products SET is_active = 0 WHERE id = ?", (product_id,), commit=True)
        return True, "Produit désactivé"

    @staticmethod
    def add_reception(product_id, qty, purchase_price, user_id=1, reason="Réception Fournisseur"):
        """Enregistre une entrée de stock avec mise à jour du prix d'achat."""
        db = get_db()
        product = StockService.get_product_by_id(product_id)
        if not product:
            return False, "Produit non trouvé"

        old_stock = product["stock_qty"]
        new_stock = old_stock + int(qty)

        # Mettre à jour produit
        db.execute_query("""
            UPDATE products 
            SET stock_qty = ?, purchase_price = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (new_stock, float(purchase_price), product_id), commit=True)

        # Mouvement de stock
        db.execute_query("""
            INSERT INTO stock_movements (product_id, movement_type, qty, old_stock, new_stock, unit_price, reason, user_id)
            VALUES (?, 'reception', ?, ?, ?, ?, ?, ?)
        """, (product_id, int(qty), old_stock, new_stock, float(purchase_price), reason, user_id), commit=True)

        return True, f"Stock mis à jour (+{qty}). Nouveau stock : {new_stock}"

    @staticmethod
    def adjust_stock(product_id, new_quantity, reason, user_id=1):
        """Ajuste manuellement le stock pour correction ou casse."""
        db = get_db()
        product = StockService.get_product_by_id(product_id)
        if not product:
            return False, "Produit introuvable"

        old_stock = product["stock_qty"]
        new_qty = int(new_quantity)
        diff = new_qty - old_stock

        movement_type = "inventaire" if "inventaire" in reason.lower() else ("perte_casse" if diff < 0 else "ajustement")

        db.execute_query("UPDATE products SET stock_qty = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_qty, product_id), commit=True)
        db.execute_query("""
            INSERT INTO stock_movements (product_id, movement_type, qty, old_stock, new_stock, unit_price, reason, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (product_id, movement_type, diff, old_stock, new_qty, product["purchase_price"], reason, user_id), commit=True)

        return True, "Ajustement enregistré avec succès"

    @staticmethod
    def get_stock_movements(product_id=None, limit=100):
        db = get_db()
        if product_id:
            query = """
                SELECT m.*, p.name as product_name, p.barcode, u.full_name as user_name
                FROM stock_movements m
                JOIN products p ON m.product_id = p.id
                LEFT JOIN users u ON m.user_id = u.id
                WHERE m.product_id = ?
                ORDER BY m.created_at DESC LIMIT ?
            """
            return db.execute_query(query, (product_id, limit))
        else:
            query = """
                SELECT m.*, p.name as product_name, p.barcode, u.full_name as user_name
                FROM stock_movements m
                JOIN products p ON m.product_id = p.id
                LEFT JOIN users u ON m.user_id = u.id
                ORDER BY m.created_at DESC LIMIT ?
            """
            return db.execute_query(query, (limit,))

    # Alertes de Stock
    @staticmethod
    def get_low_stock_alerts():
        """Produits dont le stock est <= seuil d'alerte et > 0."""
        db = get_db()
        return db.execute_query("""
            SELECT p.*, s.name as supplier_name 
            FROM products p
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE p.is_active = 1 AND p.stock_qty <= p.min_stock_alert AND p.stock_qty > 0
            ORDER BY p.stock_qty ASC
        """)

    @staticmethod
    def get_out_of_stock_alerts():
        """Produits en rupture complète de stock (<= 0)."""
        db = get_db()
        return db.execute_query("""
            SELECT p.*, s.name as supplier_name 
            FROM products p
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE p.is_active = 1 AND p.stock_qty <= 0
            ORDER BY p.name ASC
        """)

    @staticmethod
    def get_expiring_alerts(days=90):
        """Produits qui expirent dans les N jours ou déjà expirés."""
        db = get_db()
        threshold_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        return db.execute_query("""
            SELECT p.*, s.name as supplier_name 
            FROM products p
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE p.is_active = 1 AND p.expiry_date IS NOT NULL AND p.expiry_date <= ? AND p.stock_qty > 0
            ORDER BY p.expiry_date ASC
        """, (threshold_date,))

    @staticmethod
    def get_total_alerts_count():
        low = len(StockService.get_low_stock_alerts())
        out = len(StockService.get_out_of_stock_alerts())
        exp = len(StockService.get_expiring_alerts(60))
        return low + out + exp, low, out, exp
