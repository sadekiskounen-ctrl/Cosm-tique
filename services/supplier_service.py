import datetime
import random
import logging
from database.db_manager import get_db

logger = logging.getLogger("SUPPLIER_SERVICE")

class SupplierService:
    @staticmethod
    def get_suppliers(search=""):
        db = get_db()
        if search:
            return db.execute_query("""
                SELECT s.*, COUNT(p.id) as product_count 
                FROM suppliers s
                LEFT JOIN products p ON s.id = p.supplier_id AND p.is_active = 1
                WHERE s.name LIKE ? OR s.contact_person LIKE ? OR s.phone LIKE ?
                GROUP BY s.id
                ORDER BY s.name ASC
            """, (f"%{search}%", f"%{search}%", f"%{search}%"))
        else:
            return db.execute_query("""
                SELECT s.*, COUNT(p.id) as product_count 
                FROM suppliers s
                LEFT JOIN products p ON s.id = p.supplier_id AND p.is_active = 1
                GROUP BY s.id
                ORDER BY s.name ASC
            """)

    @staticmethod
    def get_supplier_by_id(supplier_id):
        db = get_db()
        rows = db.execute_query("SELECT * FROM suppliers WHERE id = ?", (supplier_id,))
        return rows[0] if rows else None

    @staticmethod
    def add_supplier(name, contact_person="", phone="", email="", address="", notes=""):
        db = get_db()
        try:
            sid = db.execute_query("""
                INSERT INTO suppliers (name, contact_person, phone, email, address, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name.strip(), contact_person.strip(), phone.strip(), email.strip(), address.strip(), notes.strip()), commit=True)
            return True, "Fournisseur ajouté avec succès", sid
        except Exception as e:
            return False, f"Erreur : {e}", None

    @staticmethod
    def update_supplier(supplier_id, name, contact_person="", phone="", email="", address="", notes=""):
        db = get_db()
        try:
            db.execute_query("""
                UPDATE suppliers 
                SET name = ?, contact_person = ?, phone = ?, email = ?, address = ?, notes = ?
                WHERE id = ?
            """, (name.strip(), contact_person.strip(), phone.strip(), email.strip(), address.strip(), notes.strip(), supplier_id), commit=True)
            return True, "Fournisseur mis à jour avec succès"
        except Exception as e:
            return False, f"Erreur : {e}"

    @staticmethod
    def delete_supplier(supplier_id):
        db = get_db()
        try:
            db.execute_query("DELETE FROM suppliers WHERE id = ?", (supplier_id,), commit=True)
            return True, "Fournisseur supprimé"
        except Exception as e:
            return False, f"Erreur : {e}"

    # ── BONS DE COMMANDE (PURCHASE ORDERS) ────────────────────────────────────

    @staticmethod
    def get_purchase_orders(status_filter="Tous", search=""):
        db = get_db()
        query = """
            SELECT po.*, s.name as supplier_name, s.phone as supplier_phone, 
                   COUNT(poi.id) as items_count,
                   SUM(CASE WHEN poi.qty_received >= poi.qty_ordered THEN 1 ELSE 0 END) as compliant_items_count,
                   SUM(poi.qty_ordered) as total_qty_ordered,
                   SUM(poi.qty_received) as total_qty_received
            FROM purchase_orders po
            JOIN suppliers s ON po.supplier_id = s.id
            LEFT JOIN purchase_order_items poi ON po.id = poi.order_id
            WHERE 1=1
        """
        params = []
        if status_filter != "Tous":
            s_map = {
                "en attente": "en_attente",
                "en_attente": "en_attente",
                "brouillon": "brouillon",
                "reçu complet": "recu_complet",
                "recu_complet": "recu_complet",
                "reçu partiel": "recu_partiel",
                "recu_partiel": "recu_partiel",
                "annulé": "annule",
                "annule": "annule"
            }
            mapped = s_map.get(status_filter.lower(), status_filter.lower())
            query += " AND po.status = ?"
            params.append(mapped)

        if search:
            query += " AND (po.order_code LIKE ? OR s.name LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])

        query += " GROUP BY po.id ORDER BY po.created_at DESC"
        return db.execute_query(query, params)

    @staticmethod
    def get_purchase_order_by_id(order_id):
        db = get_db()
        rows = db.execute_query("""
            SELECT po.*, s.name as supplier_name, s.phone as supplier_phone,
                   s.email as supplier_email, s.address as supplier_address, s.contact_person
            FROM purchase_orders po
            JOIN suppliers s ON po.supplier_id = s.id
            WHERE po.id = ?
        """, (order_id,))
        return rows[0] if rows else None

    @staticmethod
    def get_order_items(order_id):
        """Récupère les lignes d'un bon de commande avec informations produits actuelles."""
        db = get_db()
        return db.execute_query("""
            SELECT poi.*, 
                   COALESCE(p.name, poi.product_name) as display_name,
                   COALESCE(p.barcode, poi.barcode) as display_barcode,
                   p.stock_qty as current_stock,
                   p.purchase_price as current_catalog_price,
                   p.category as product_category
            FROM purchase_order_items poi
            LEFT JOIN products p ON poi.product_id = p.id
            WHERE poi.order_id = ?
            ORDER BY poi.id ASC
        """, (order_id,))

    @staticmethod
    def generate_po_code(supplier_id):
        now = datetime.datetime.now().strftime("%Y%m%d")
        rnd = random.randint(100, 999)
        return f"BC-{now}-{supplier_id}-{rnd}"

    @staticmethod
    def create_purchase_order(supplier_id, items, status="en_attente", notes=""):
        """
        Crée un nouveau bon de commande.
        items: list of dict:
          - product_id (int or None if new)
          - name (str)
          - barcode (str, optional)
          - category (str, optional)
          - unit_cost (float)
          - qty_ordered (int)
          - is_new_product (bool/int)
        """
        db = get_db()
        try:
            order_code = SupplierService.generate_po_code(supplier_id)
            total_amount = sum(float(item.get("unit_cost", 0)) * int(item.get("qty_ordered", 1)) for item in items)

            order_id = db.execute_query("""
                INSERT INTO purchase_orders (order_code, supplier_id, status, total_amount, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (order_code, supplier_id, status, total_amount, notes.strip()), commit=True)

            for item in items:
                pid = item.get("product_id")
                pname = item.get("name", "").strip()
                pbc = item.get("barcode", "").strip() if item.get("barcode") else None
                is_new = 1 if item.get("is_new_product") or not pid else 0
                qty_ord = int(item.get("qty_ordered", 1))
                unit_c = float(item.get("unit_cost", 0.0))
                tot_c = qty_ord * unit_c

                db.execute_query("""
                    INSERT INTO purchase_order_items (order_id, product_id, product_name, barcode, qty_ordered, qty_received, unit_cost, total_cost, is_new_product, status)
                    VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, 'en_attente')
                """, (order_id, pid, pname, pbc, qty_ord, unit_c, tot_c, is_new), commit=True)

            return True, "Bon de commande créé avec succès.", order_id, order_code
        except Exception as e:
            logger.error(f"Erreur création bon de commande: {e}")
            return False, f"Erreur : {e}", None, None

    @staticmethod
    def create_purchase_order_from_alerts(supplier_id=None):
        """Génère automatiquement un bon de commande à partir des alertes de stock bas."""
        db = get_db()
        query = """
            SELECT p.*, s.name as supplier_name 
            FROM products p
            JOIN suppliers s ON p.supplier_id = s.id
            WHERE p.is_active = 1 AND p.stock_qty <= p.min_stock_alert
        """
        params = []
        if supplier_id:
            query += " AND p.supplier_id = ?"
            params.append(supplier_id)

        alert_products = db.execute_query(query, params)
        if not alert_products:
            return False, "Aucun produit en alerte nécessitant une commande."

        grouped = {}
        for p in alert_products:
            sid = p["supplier_id"]
            if sid not in grouped:
                grouped[sid] = []
            grouped[sid].append(p)

        orders_created = 0
        for sid, prods in grouped.items():
            order_items = []
            for p in prods:
                suggested_qty = max(10, (p["min_stock_alert"] * 3) - p["stock_qty"])
                order_items.append({
                    "product_id": p["id"],
                    "name": p["name"],
                    "barcode": p["barcode"],
                    "unit_cost": p["purchase_price"],
                    "qty_ordered": suggested_qty,
                    "is_new_product": 0
                })
            ok, msg, oid, ocode = SupplierService.create_purchase_order(
                supplier_id=sid,
                items=order_items,
                status="en_attente",
                notes="Génération automatique à partir des alertes de stock bas"
            )
            if ok:
                orders_created += 1

        return True, f"{orders_created} bon(s) de commande généré(s) avec succès."

    # ── RÉCEPTION DE MARCHANDISE VIA SCAN CODE-BARRES ─────────────────────────

    @staticmethod
    def process_reception(order_id, received_items, user_id=1, notes=""):
        """
        Valide la réception de marchandise pour un bon de commande:
        - Vérifie si chaque produit est nouveau ou existant
        - Si nouveau : crée la fiche produit dans `products` avec `created_via_po_id = order_id`
        - Si existant : incrémente le stock (`stock_qty = stock_qty + qty_received`)
        - Met à jour le prix d'achat si demandé
        - Enregistre un mouvement de stock "reception" par ligne, horodaté et lié au BC
        - Compare quantités reçues vs commandées -> statut "recu_complet" ou "recu_partiel"
        - Met à jour le statut du BC et la date de réception
        - Triggers sync D:
        """
        db = get_db()
        order = SupplierService.get_purchase_order_by_id(order_id)
        if not order:
            return False, "Bon de commande introuvable."

        try:
            new_products_created = 0
            existing_updated = 0
            stock_movements_logged = 0

            # 1. Traiter chaque article reçu
            for item in received_items:
                barcode = str(item.get("barcode", "")).strip()
                qty_rec = int(item.get("qty_received", 0))
                if qty_rec <= 0:
                    continue

                unit_price = float(item.get("purchase_price", item.get("unit_cost", 0.0)))
                update_price = item.get("update_catalog_price", False)
                item_id = item.get("item_id")  # ID in purchase_order_items if existing line

                # Vérifier si produit existe par barcode
                existing_p = None
                if barcode:
                    p_rows = db.execute_query("SELECT * FROM products WHERE barcode = ? AND is_active = 1", (barcode,))
                    if p_rows:
                        existing_p = dict(p_rows[0])

                if not existing_p and item.get("product_id"):
                    p_rows = db.execute_query("SELECT * FROM products WHERE id = ?", (item["product_id"],))
                    if p_rows:
                        existing_p = dict(p_rows[0])

                sale_price = float(item.get("sale_price") or 0.0)

                if existing_p:
                    # ── Produit Existant ──
                    pid = existing_p["id"]
                    old_stock = existing_p["stock_qty"]
                    new_stock = old_stock + qty_rec

                    if sale_price <= 0:
                        sale_price = float(existing_p.get("sale_price", 0.0))

                    # Mise à jour prix d'achat, prix de vente et catégorie
                    cat_val = item.get("category") or existing_p.get("category") or "Soins Visage"
                    if update_price:
                        db.execute_query("""
                            UPDATE products 
                            SET stock_qty = ?, purchase_price = ?, sale_price = ?, category = ?, supplier_id = COALESCE(supplier_id, ?), updated_at = CURRENT_TIMESTAMP 
                            WHERE id = ?
                        """, (new_stock, unit_price, sale_price, cat_val, order["supplier_id"], pid), commit=True)
                    else:
                        db.execute_query("""
                            UPDATE products 
                            SET stock_qty = ?, sale_price = ?, category = ?, supplier_id = COALESCE(supplier_id, ?), updated_at = CURRENT_TIMESTAMP 
                            WHERE id = ?
                        """, (new_stock, sale_price, cat_val, order["supplier_id"], pid), commit=True)

                    existing_updated += 1


                else:
                    # ── Nouveau Produit (Non existant dans le catalogue) ──
                    name = item.get("name", "Nouveau Produit").strip()
                    brand = item.get("brand", "").strip()
                    category = item.get("category", "Soins Visage")
                    sale_price = float(item.get("sale_price", unit_price * 1.4))
                    vat_rate = float(item.get("vat_rate", 0.0))
                    min_alert = int(item.get("min_alert", 5))
                    expiry_date = item.get("expiry_date") or None

                    old_stock = 0
                    new_stock = qty_rec

                    pid = db.execute_query("""
                        INSERT INTO products (
                            barcode, name, brand, category, purchase_price, sale_price,
                            vat_rate, stock_qty, min_stock_alert, expiry_date,
                            supplier_id, is_active, created_via_po_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """, (barcode, name, brand, category, unit_price, sale_price, vat_rate, new_stock, min_alert, expiry_date, order["supplier_id"], order_id), commit=True)

                    new_products_created += 1

                # ── Enregistrer mouvement de stock ──
                reason_str = f"Réception Bon de Commande {order['order_code']}"
                db.execute_query("""
                    INSERT INTO stock_movements (product_id, movement_type, qty, old_stock, new_stock, unit_price, reason, user_id)
                    VALUES (?, 'reception', ?, ?, ?, ?, ?, ?)
                """, (pid, qty_rec, old_stock, new_stock, unit_price, reason_str, user_id), commit=True)
                stock_movements_logged += 1

                # ── Mettre à jour purchase_order_items ──
                matched_poi = None
                if item_id:
                    poi_rows = db.execute_query("SELECT * FROM purchase_order_items WHERE id = ? AND order_id = ?", (item_id, order_id))
                    if poi_rows:
                        matched_poi = dict(poi_rows[0])
                
                if not matched_poi:
                    # Chercher par product_id, barcode ou nom dans ce BC
                    if pid:
                        poi_rows = db.execute_query("SELECT * FROM purchase_order_items WHERE order_id = ? AND product_id = ?", (order_id, pid))
                        if poi_rows:
                            matched_poi = dict(poi_rows[0])
                    if not matched_poi and barcode:
                        poi_rows = db.execute_query("SELECT * FROM purchase_order_items WHERE order_id = ? AND barcode = ?", (order_id, barcode))
                        if poi_rows:
                            matched_poi = dict(poi_rows[0])
                    if not matched_poi and item.get("name"):
                        poi_rows = db.execute_query("SELECT * FROM purchase_order_items WHERE order_id = ? AND product_name LIKE ?", (order_id, item["name"].strip()))
                        if poi_rows:
                            matched_poi = dict(poi_rows[0])

                if matched_poi:
                    curr_qty_rec = matched_poi.get("qty_received") or 0
                    total_rec = curr_qty_rec + qty_rec
                    qty_ord = matched_poi.get("qty_ordered", 0)

                    if total_rec == qty_ord:
                        line_status = "conforme"
                    elif total_rec < qty_ord:
                        line_status = "partiel"
                    else:
                        line_status = "surnumeraire"

                    db.execute_query("""
                        UPDATE purchase_order_items 
                        SET product_id = COALESCE(product_id, ?), barcode = COALESCE(barcode, ?), qty_received = ?, status = ?
                        WHERE id = ?
                    """, (pid, barcode, total_rec, line_status, matched_poi["id"]), commit=True)
                else:
                    # Article ajouté à la volée pendant la réception
                    line_status = "surnumeraire" if qty_rec > 0 else "conforme"
                    db.execute_query("""
                        INSERT INTO purchase_order_items (order_id, product_id, product_name, barcode, qty_ordered, qty_received, unit_cost, total_cost, is_new_product, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (order_id, pid, item.get("name"), barcode, 0, qty_rec, unit_price, qty_rec * unit_price, 1 if not existing_p else 0, line_status), commit=True)

            # ── Déterminer statut final du Bon de Commande ──
            all_items = db.execute_query("SELECT * FROM purchase_order_items WHERE order_id = ?", (order_id,))
            has_pending = False
            has_received_anything = False

            for itm in all_items:
                ord_q = itm["qty_ordered"]
                rec_q = itm["qty_received"] or 0
                if rec_q > 0:
                    has_received_anything = True
                if rec_q < ord_q:
                    has_pending = True

            if has_pending:
                new_po_status = "recu_partiel"
            else:
                new_po_status = "recu_complet"

            # Mise à jour purchase_orders
            db.execute_query("""
                UPDATE purchase_orders 
                SET status = ?, received_at = CURRENT_TIMESTAMP, notes = COALESCE(notes, '') || ?
                WHERE id = ?
            """, (new_po_status, f"\n[Réception le {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}: {stock_movements_logged} lignes traitées]", order_id), commit=True)

            return True, {
                "po_status": new_po_status,
                "new_products_created": new_products_created,
                "existing_updated": existing_updated,
                "movements_logged": stock_movements_logged
            }

        except Exception as e:
            logger.error(f"Erreur validation réception: {e}")
            return False, f"Erreur lors de la validation : {e}"

    # ── TRAÇABILITÉ & AUDIT ────────────────────────────────────────────────────

    @staticmethod
    def get_po_traceability(order_id):
        """Retourne l'historique complet, produits créés et mouvements liés au bon de commande."""
        db = get_db()
        order = SupplierService.get_purchase_order_by_id(order_id)
        if not order:
            return None

        # Articles du BC avec conformité
        items = db.execute_query("""
            SELECT poi.*, 
                   COALESCE(p.name, poi.product_name) as product_name,
                   COALESCE(p.barcode, poi.barcode) as barcode,
                   p.created_via_po_id,
                   p.stock_qty as current_stock,
                   (poi.qty_received - poi.qty_ordered) as difference_qty
            FROM purchase_order_items poi
            LEFT JOIN products p ON poi.product_id = p.id
            WHERE poi.order_id = ?
            ORDER BY poi.id ASC
        """, (order_id,))

        # Nouveaux produits créés spécifiquement via ce BC
        new_prods = db.execute_query("""
            SELECT p.*, s.name as supplier_name
            FROM products p
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE p.created_via_po_id = ?
            ORDER BY p.name ASC
        """, (order_id,))

        # Mouvements de stock liés
        movs = db.execute_query("""
            SELECT sm.*, p.name as product_name, p.barcode, u.full_name as operator_name
            FROM stock_movements sm
            JOIN products p ON sm.product_id = p.id
            LEFT JOIN users u ON sm.user_id = u.id
            WHERE sm.reason LIKE ?
            ORDER BY sm.created_at DESC
        """, (f"%{order['order_code']}%",))

        return {
            "order": dict(order),
            "items": [dict(r) for r in items],
            "new_products": [dict(r) for r in new_prods],
            "movements": [dict(r) for r in movs]
        }

    @staticmethod
    def get_products_created_by_pos():
        """Retourne tous les produits ajoutés au catalogue via des bons de commande."""
        db = get_db()
        return db.execute_query("""
            SELECT p.*, po.order_code, po.created_at as po_created_at, po.received_at as po_received_at, s.name as supplier_name
            FROM products p
            JOIN purchase_orders po ON p.created_via_po_id = po.id
            JOIN suppliers s ON po.supplier_id = s.id
            ORDER BY po.created_at DESC, p.name ASC
        """)

    # ── GÉNÉRATION PDF DU BON DE COMMANDE ────────────────────────────────────

    @staticmethod
    def generate_order_pdf(order_id):
        """Génère un PDF professionnel, moderne et élégant au standard international pour le bon de commande."""
        import os
        import datetime
        from config import REPORTS_DIR

        db = get_db()
        order_rows = db.execute_query("""
            SELECT po.*, s.name as supplier_name, s.phone as supplier_phone,
                   s.email as supplier_email, s.address as supplier_address, s.contact_person
            FROM purchase_orders po
            JOIN suppliers s ON po.supplier_id = s.id
            WHERE po.id = ?
        """, (order_id,))
        if not order_rows:
            return None, "Bon de commande introuvable"

        order = dict(order_rows[0])
        items = db.execute_query("""
            SELECT poi.*, 
                   COALESCE(p.name, poi.product_name) as product_name,
                   COALESCE(p.barcode, poi.barcode) as barcode
            FROM purchase_order_items poi
            LEFT JOIN products p ON poi.product_id = p.id
            WHERE poi.order_id = ?
        """, (order_id,))

        settings_rows = db.execute_query("SELECT key, value FROM settings")
        settings = {r["key"]: r["value"] for r in settings_rows}
        store_name = settings.get("store_name", "Élégance & Beauté Cosmétique")
        store_phone = settings.get("store_phone", "0550 12 34 56")
        store_address = settings.get("store_address", "12 Boulevard Didouche Mourad, Alger")
        store_nif = settings.get("store_nif", "001234567890123")

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import mm
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, HRFlowable
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.colors import HexColor, white
            from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT

            pdf_dir = REPORTS_DIR / "bons_commande"
            pdf_dir.mkdir(parents=True, exist_ok=True)
            pdf_path = pdf_dir / f"{order['order_code']}.pdf"

            # Page A4: 210mm x 297mm. Marges 14mm -> Largeur utile = 182mm (516 pt)
            doc = SimpleDocTemplate(
                str(pdf_path),
                pagesize=A4,
                rightMargin=14*mm,
                leftMargin=14*mm,
                topMargin=12*mm,
                bottomMargin=12*mm
            )

            # Palette Couleurs International Corporate
            C_NAVY_DARK = HexColor('#0F172A')   # Slate 900
            C_HEADER_BG = HexColor('#1E293B')   # Slate 800
            C_BRAND_BLUE= HexColor('#2563EB')   # Corporate Blue
            C_ACCENT    = HexColor('#4F46E5')   # Indigo Accent
            C_TEXT_DARK = HexColor('#0F172A')   # Main Text
            C_TEXT_MUTED= HexColor('#475569')   # Slate 600
            C_TEXT_LIGHT= HexColor('#94A3B8')   # Slate 400
            C_BG_CARD   = HexColor('#F8FAFC')   # Slate 50
            C_CARD_HEAD = HexColor('#F1F5F9')   # Slate 100
            C_BORDER    = HexColor('#CBD5E1')   # Slate 300
            C_BORDER_LIGHT= HexColor('#E2E8F0') # Slate 200
            C_ROW_ALT   = HexColor('#F8FAFC')   # Row alternate
            C_GREEN_BG  = HexColor('#DCFCE7')   # Soft Green
            C_GREEN_TXT = HexColor('#15803D')   # Dark Green
            C_AMBER_BG  = HexColor('#FEF3C7')   # Soft Amber
            C_AMBER_TXT = HexColor('#B45309')   # Dark Amber

            # Styles Typographiques
            p_comp_name = ParagraphStyle('comp_name', fontSize=15, fontName='Helvetica-Bold', textColor=C_NAVY_DARK, leading=18)
            p_comp_sub  = ParagraphStyle('comp_sub', fontSize=7.5, fontName='Helvetica-Bold', textColor=C_BRAND_BLUE, leading=10, spaceAfter=4)
            p_comp_info = ParagraphStyle('comp_info', fontSize=8, fontName='Helvetica', textColor=C_TEXT_MUTED, leading=11)
            
            p_doc_title = ParagraphStyle('doc_title', fontSize=17, fontName='Helvetica-Bold', textColor=C_NAVY_DARK, alignment=TA_RIGHT, leading=20)
            p_doc_ref   = ParagraphStyle('doc_ref', fontSize=11, fontName='Helvetica-Bold', textColor=C_BRAND_BLUE, alignment=TA_RIGHT, leading=14)
            p_doc_date  = ParagraphStyle('doc_date', fontSize=8, fontName='Helvetica', textColor=C_TEXT_MUTED, alignment=TA_RIGHT, leading=11)

            p_card_title= ParagraphStyle('card_title', fontSize=8, fontName='Helvetica-Bold', textColor=C_HEADER_BG, spaceAfter=2)
            p_card_bold = ParagraphStyle('card_bold', fontSize=9, fontName='Helvetica-Bold', textColor=C_TEXT_DARK, leading=12)
            p_card_val  = ParagraphStyle('card_val', fontSize=8.5, fontName='Helvetica', textColor=C_TEXT_MUTED, leading=11)

            p_sec_title = ParagraphStyle('sec_title', fontSize=9.5, fontName='Helvetica-Bold', textColor=C_NAVY_DARK, spaceAfter=2)
            
            p_cell_left  = ParagraphStyle('c_left', fontSize=8, fontName='Helvetica', textColor=C_TEXT_DARK, leading=10)
            p_cell_center= ParagraphStyle('c_center', fontSize=8, fontName='Helvetica', textColor=C_TEXT_DARK, alignment=TA_CENTER, leading=10)
            p_cell_right = ParagraphStyle('c_right', fontSize=8, fontName='Helvetica', textColor=C_TEXT_DARK, alignment=TA_RIGHT, leading=10)

            p_terms_title= ParagraphStyle('tt', fontSize=8, fontName='Helvetica-Bold', textColor=C_TEXT_DARK, spaceAfter=2)
            p_terms_body = ParagraphStyle('tb', fontSize=7, fontName='Helvetica', textColor=C_TEXT_MUTED, leading=9.5)

            p_total_lbl = ParagraphStyle('tl', fontSize=8.5, fontName='Helvetica-Bold', textColor=C_TEXT_MUTED, alignment=TA_LEFT)
            p_total_v   = ParagraphStyle('tv', fontSize=8.5, fontName='Helvetica-Bold', textColor=C_TEXT_DARK, alignment=TA_RIGHT)
            p_big_lbl   = ParagraphStyle('bl', fontSize=10, fontName='Helvetica-Bold', textColor=white, alignment=TA_LEFT)
            p_big_v     = ParagraphStyle('bv', fontSize=12, fontName='Helvetica-Bold', textColor=white, alignment=TA_RIGHT)

            p_sig_title = ParagraphStyle('st', fontSize=8, fontName='Helvetica-Bold', textColor=C_NAVY_DARK, alignment=TA_CENTER)
            p_sig_hint  = ParagraphStyle('sh', fontSize=7, fontName='Helvetica', textColor=C_TEXT_LIGHT, alignment=TA_CENTER)
            p_footer    = ParagraphStyle('ft', fontSize=7.5, fontName='Helvetica', textColor=C_TEXT_LIGHT)

            story = []

            # 1. Barre d'accentuation supérieure
            story.append(HRFlowable(width="100%", thickness=2.5, color=C_BRAND_BLUE, spaceBefore=0, spaceAfter=8))

            # 2. En-tête Moderne Entreprise (182 mm)
            header_table = Table([[
                [
                    Paragraph(store_name, p_comp_name),
                    Paragraph("COMMERCE & DISTRIBUTION COSMÉTIQUE", p_comp_sub),
                    Paragraph(f"<b>Adresse :</b> {store_address}", p_comp_info),
                    Paragraph(f"<b>Tél :</b> {store_phone}  |  <b>NIF :</b> {store_nif}", p_comp_info),
                ],
                [
                    Paragraph("BON DE COMMANDE", p_doc_title),
                    Paragraph(f"N° {order['order_code']}", p_doc_ref),
                    Paragraph(f"Émis le : {order.get('created_at', '')[:16]}", p_doc_date),
                ]
            ]], colWidths=[102*mm, 80*mm])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('PADDING', (0, 0), (-1, -1), 0),
            ]))
            story.append(header_table)
            story.append(Spacer(1, 5*mm))

            # 3. Cartes d'Informations Fournisseur & Métadonnées (89mm + 4mm + 89mm = 182mm)
            status_labels = {
                "en_attente": "En attente de livraison",
                "brouillon": "Brouillon",
                "recu_complet": "Réception conforme & complète",
                "recu_partiel": "Réception partielle",
                "annule": "Commande annulée"
            }
            st_text = status_labels.get(order.get('status', 'en_attente'), order.get('status', ''))
            rec_date_str = order.get('received_at', '')[:16] if order.get('received_at') else "Non réceptionné"

            supplier_cell = [
                Paragraph("<b>FOURNISSEUR BÉNÉFICIAIRE</b>", p_card_title),
                Spacer(1, 1*mm),
                Paragraph(f"<b>{order['supplier_name']}</b>", p_card_bold),
                Paragraph(f"Contact : {order.get('contact_person') or 'Direction Commerciale'}", p_card_val),
                Paragraph(f"Téléphone : {order.get('supplier_phone') or '-'}", p_card_val),
                Paragraph(f"Email : {order.get('supplier_email') or '-'}", p_card_val),
                Paragraph(f"Adresse : {order.get('supplier_address') or '-'}", p_card_val),
            ]

            order_meta_cell = [
                Paragraph("<b>DÉTAILS & ÉTAT DU DOCUMENT</b>", p_card_title),
                Spacer(1, 1*mm),
                Paragraph(f"<b>Statut actuel :</b> {st_text}", p_card_bold),
                Paragraph(f"Date de création : {order.get('created_at', '')[:16] or '-'}", p_card_val),
                Paragraph(f"Date de réception : {rec_date_str}", p_card_val),
                Paragraph(f"Code Document : {order['order_code']}", p_card_val),
                Paragraph("Devise : Dinar Algérien (DZD / DA)", p_card_val),
            ]

            info_cards_table = Table([[
                supplier_cell,
                "",  # spacer col
                order_meta_cell
            ]], colWidths=[89*mm, 4*mm, 89*mm])
            info_cards_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), C_BG_CARD),
                ('BACKGROUND', (2, 0), (2, 0), C_BG_CARD),
                ('BOX', (0, 0), (0, 0), 0.5, C_BORDER_LIGHT),
                ('BOX', (2, 0), (2, 0), 0.5, C_BORDER_LIGHT),
                ('PADDING', (0, 0), (0, 0), 7),
                ('PADDING', (2, 0), (2, 0), 7),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(info_cards_table)
            story.append(Spacer(1, 5*mm))

            # 4. Titre de section
            story.append(Paragraph("ARTICLES COMMANDÉS & CONDITIONS DE TARIFICATION", p_sec_title))
            story.append(Spacer(1, 1*mm))

            # 5. Tableau des articles avec largeurs calculées au millimètre près (Total = 182 mm)
            is_received = order.get('status') in ('recu_complet', 'recu_partiel')
            total_qty_ordered = 0
            total_qty_received = 0

            if is_received:
                # 7 colonnes : 28 + 56 + 16 + 16 + 20 + 24 + 22 = 182 mm
                col_w = [28*mm, 56*mm, 16*mm, 16*mm, 20*mm, 24*mm, 22*mm]
                headers = [
                    Paragraph("<b>Code-barres</b>", ParagraphStyle('th_c', fontSize=8, fontName='Helvetica-Bold', textColor=white, alignment=TA_CENTER)),
                    Paragraph("<b>Désignation Article</b>", ParagraphStyle('th_l', fontSize=8, fontName='Helvetica-Bold', textColor=white, alignment=TA_LEFT)),
                    Paragraph("<b>Qté Cde</b>", ParagraphStyle('th_c2', fontSize=8, fontName='Helvetica-Bold', textColor=white, alignment=TA_CENTER)),
                    Paragraph("<b>Qté Reçue</b>", ParagraphStyle('th_c3', fontSize=8, fontName='Helvetica-Bold', textColor=white, alignment=TA_CENTER)),
                    Paragraph("<b>P.U. (DA)</b>", ParagraphStyle('th_r', fontSize=8, fontName='Helvetica-Bold', textColor=white, alignment=TA_RIGHT)),
                    Paragraph("<b>Total (DA)</b>", ParagraphStyle('th_r2', fontSize=8, fontName='Helvetica-Bold', textColor=white, alignment=TA_RIGHT)),
                    Paragraph("<b>Conformité</b>", ParagraphStyle('th_c4', fontSize=8, fontName='Helvetica-Bold', textColor=white, alignment=TA_CENTER)),
                ]
            else:
                # 6 colonnes : 8 + 30 + 74 + 20 + 25 + 25 = 182 mm
                col_w = [8*mm, 30*mm, 74*mm, 20*mm, 25*mm, 25*mm]
                headers = [
                    Paragraph("<b>N°</b>", ParagraphStyle('th_n', fontSize=8, fontName='Helvetica-Bold', textColor=white, alignment=TA_CENTER)),
                    Paragraph("<b>Code-barres</b>", ParagraphStyle('th_bc', fontSize=8, fontName='Helvetica-Bold', textColor=white, alignment=TA_CENTER)),
                    Paragraph("<b>Désignation du Produit</b>", ParagraphStyle('th_ds', fontSize=8, fontName='Helvetica-Bold', textColor=white, alignment=TA_LEFT)),
                    Paragraph("<b>Qté Cde</b>", ParagraphStyle('th_qt', fontSize=8, fontName='Helvetica-Bold', textColor=white, alignment=TA_CENTER)),
                    Paragraph("<b>P.U. HT (DA)</b>", ParagraphStyle('th_pu', fontSize=8, fontName='Helvetica-Bold', textColor=white, alignment=TA_RIGHT)),
                    Paragraph("<b>Total Ligne (DA)</b>", ParagraphStyle('th_tot', fontSize=8, fontName='Helvetica-Bold', textColor=white, alignment=TA_RIGHT)),
                ]

            table_data = [headers]
            for idx, item in enumerate(items, 1):
                item = dict(item)
                bc = str(item.get("barcode") or "-")
                name = str(item.get("product_name") or "-")
                q_ord = int(item.get("qty_ordered", 0) or 0)
                q_rec = int(item.get("qty_received", 0) or 0)
                cost = float(item.get("unit_cost", 0.0) or 0.0)
                tot = float(item.get("total_cost", q_ord * cost) or (q_ord * cost))

                total_qty_ordered += q_ord
                total_qty_received += q_rec

                cost_formatted = f"{cost:,.2f}".replace(",", " ").replace(".00", "")
                tot_formatted  = f"{tot:,.2f}".replace(",", " ").replace(".00", "")

                if is_received:
                    if q_rec >= q_ord:
                        st_pill = "Conforme"
                    elif q_rec > 0:
                        st_pill = f"Partiel ({q_rec}/{q_ord})"
                    else:
                        st_pill = "Non reçu"

                    table_data.append([
                        Paragraph(bc, p_cell_center),
                        Paragraph(name[:36], p_cell_left),
                        Paragraph(str(q_ord), p_cell_center),
                        Paragraph(str(q_rec), p_cell_center),
                        Paragraph(cost_formatted, p_cell_right),
                        Paragraph(tot_formatted, p_cell_right),
                        Paragraph(st_pill, p_cell_center),
                    ])
                else:
                    table_data.append([
                        Paragraph(str(idx), p_cell_center),
                        Paragraph(bc, p_cell_center),
                        Paragraph(name[:42], p_cell_left),
                        Paragraph(str(q_ord), p_cell_center),
                        Paragraph(cost_formatted, p_cell_right),
                        Paragraph(tot_formatted, p_cell_right),
                    ])

            items_table = Table(table_data, colWidths=col_w, repeatRows=1)
            t_style = [
                ('BACKGROUND', (0, 0), (-1, 0), C_HEADER_BG),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 4.5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4.5),
                ('GRID', (0, 0), (-1, -1), 0.5, C_BORDER_LIGHT),
            ]
            # Lignes alternées
            for r_idx in range(1, len(table_data)):
                bg = white if r_idx % 2 == 1 else C_ROW_ALT
                t_style.append(('BACKGROUND', (0, r_idx), (-1, r_idx), bg))

            items_table.setStyle(TableStyle(t_style))
            story.append(items_table)
            story.append(Spacer(1, 4*mm))

            # 6. Bloc Récapitulatif Financier & Conditions (102 mm conditions + 80 mm totaux = 182 mm)
            total_net_amount = float(order.get('total_amount', 0.0) or 0.0)
            total_net_formatted = f"{total_net_amount:,.2f}".replace(",", " ").replace(".00", "") + " DA"

            conditions_content = [
                Paragraph("<b>CONDITIONS & MODALITÉS DE LIVRAISON :</b>", p_terms_title),
                Paragraph("1. Le présent bon de commande doit être obligatoirement joint à la facture et au bon de livraison.", p_terms_body),
                Paragraph("2. Les marchandises livrées doivent correspondre strictement aux références et quantités indiquées.", p_terms_body),
                Paragraph("3. Tout produit présentant une anomalie, avarie ou date limite courte sera refusé.", p_terms_body),
                Paragraph("4. Modalités de règlement : Conformément aux accords commerciaux convenus.", p_terms_body),
            ]

            summary_rows = [
                [
                    Paragraph("Nombre de Références :", p_total_lbl),
                    Paragraph(f"{len(items)} article(s)", p_total_v)
                ],
                [
                    Paragraph("Total Unités Commandées :", p_total_lbl),
                    Paragraph(f"{total_qty_ordered} unités", p_total_v)
                ],
                [
                    Paragraph("TOTAL GÉNÉRAL NET :", p_big_lbl),
                    Paragraph(total_net_formatted, p_big_v)
                ],
            ]

            totals_table = Table(summary_rows, colWidths=[42*mm, 36*mm])
            totals_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('PADDING', (0, 0), (-1, -2), 3),
                ('BACKGROUND', (0, -1), (-1, -1), C_NAVY_DARK),
                ('BOX', (0, -1), (-1, -1), 1, C_NAVY_DARK),
                ('PADDING', (0, -1), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -2), 0.5, C_BORDER_LIGHT),
            ]))

            bottom_block = Table([[
                conditions_content,
                totals_table
            ]], colWidths=[102*mm, 80*mm])
            bottom_block.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('PADDING', (0, 0), (-1, -1), 2),
            ]))
            story.append(bottom_block)
            story.append(Spacer(1, 6*mm))

            # 7. Cadres de Visa & Signatures (88 mm + 6 mm + 88 mm = 182 mm)
            sig_table = Table([[
                [
                    Paragraph("<b>POUR LE FOURNISSEUR</b>", p_sig_title),
                    Paragraph("Date, Nom & Cachet de réception", p_sig_hint),
                    Spacer(1, 14*mm)
                ],
                "",  # spacer
                [
                    Paragraph("<b>POUR L'ÉTABLISSEMENT</b>", p_sig_title),
                    Paragraph("Service Achats & Direction Commerciale", p_sig_hint),
                    Spacer(1, 14*mm)
                ]
            ]], colWidths=[88*mm, 6*mm, 88*mm])
            sig_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), C_BG_CARD),
                ('BACKGROUND', (2, 0), (2, 0), C_BG_CARD),
                ('BOX', (0, 0), (0, 0), 0.5, C_BORDER),
                ('BOX', (2, 0), (2, 0), 0.5, C_BORDER),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(sig_table)
            story.append(Spacer(1, 4*mm))

            # 8. Bas de page discret et épuré
            story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER_LIGHT, spaceBefore=2, spaceAfter=2))
            story.append(Table([[
                Paragraph("CosmétiquePro \u2014 Solution de Gestion Commerciale & Point de Vente", p_footer),
                Paragraph(f"Généré le {datetime.datetime.now().strftime('%d/%m/%Y à %H:%M')} \u2014 Page 1 / 1", ParagraphStyle('ft_r', parent=p_footer, alignment=TA_RIGHT))
            ]], colWidths=[110*mm, 72*mm]))

            doc.build(story)
            return str(pdf_path), None
        except Exception as e:
            logger.error(f"Erreur PDF: {e}")
            return None, f"Erreur génération PDF : {e}"

