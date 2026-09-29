import customtkinter as ctk
from ui.theme import FONTS, COLORS
from services.stock_service import StockService
from services.supplier_service import SupplierService
from services.auth_service import AuthService
from ui.components.modern_table import ModernTable
from ui.components.modal import BaseModal
from ui.components.notification import ToastNotification


class AlertsView(ctk.CTkFrame):
    def __init__(self, parent, on_navigate=None):
        super().__init__(parent, fg_color="transparent")
        self.on_navigate = on_navigate

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        header_frame = ctk.CTkFrame(self, fg_color=("white", "#1E293B"), corner_radius=12, height=60)
        header_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        header_frame.pack_propagate(False)

        ctk.CTkLabel(
            header_frame,
            text="\U0001f6a8 Centre de Surveillance & Alertes Stocks",
            font=FONTS["title_medium"],
            text_color=COLORS["danger"]
        ).pack(side="left", padx=15)

        self.order_all_btn = ctk.CTkButton(
            header_frame,
            text="\U0001f4cb G\u00e9n\u00e9rer Bons de Commande (1-Clic)",
            height=36,
            font=FONTS["body_bold"],
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            command=self._open_supplier_selection_modal
        )
        self.order_all_btn.pack(side="right", padx=15)

        self.tabview = ctk.CTkTabview(self, corner_radius=12, fg_color=("white", "#1E293B"))
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))

        self.tab_out = self.tabview.add("\U0001f6a8 Ruptures (Stock = 0)")
        self.tab_low = self.tabview.add("\u26a0\ufe0f Stocks Bas (Sous Seuil)")
        self.tab_expiry = self.tabview.add("\u23f3 P\u00e9remptions Proches")

        self._setup_tables()
        self.load_alerts()

    def _setup_tables(self):
        self.tab_out.grid_columnconfigure(0, weight=1)
        self.tab_out.grid_rowconfigure(0, weight=1)
        cols_out = [
            ("Code-barres", 2, "w"),
            ("D\u00e9signation", 4, "w"),
            ("Marque", 2, "w"),
            ("Cat\u00e9gorie", 3, "w"),
            ("Seuil Alerte", 2, "center"),
            ("Fournisseur", 3, "w")
        ]
        self.table_out = ModernTable(self.tab_out, cols_out)
        self.table_out.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.tab_low.grid_columnconfigure(0, weight=1)
        self.tab_low.grid_rowconfigure(0, weight=1)
        cols_low = [
            ("Code-barres", 2, "w"),
            ("D\u00e9signation", 4, "w"),
            ("Marque", 2, "w"),
            ("Stock Actuel", 2, "center"),
            ("Seuil Alerte", 2, "center"),
            ("Fournisseur", 3, "w")
        ]
        self.table_low = ModernTable(self.tab_low, cols_low)
        self.table_low.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.tab_expiry.grid_columnconfigure(0, weight=1)
        self.tab_expiry.grid_rowconfigure(0, weight=1)
        cols_exp = [
            ("Code-barres", 2, "w"),
            ("D\u00e9signation", 4, "w"),
            ("Stock Restant", 2, "center"),
            ("Date d'Expiration", 3, "center"),
            ("Fournisseur", 3, "w")
        ]
        self.table_expiry = ModernTable(self.tab_expiry, cols_exp)
        self.table_expiry.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    def load_alerts(self):
        out_prods = StockService.get_out_of_stock_alerts()
        rows_out = []
        for p in out_prods:
            rows_out.append([
                p["barcode"], p["name"][:35], p["brand"] or "-",
                p["category"], f"{p['min_stock_alert']} u.",
                p["supplier_name"] or "Non assign\u00e9"
            ])
        self.table_out.set_data(rows_out)
        self.tabview._segmented_button._buttons_dict["\U0001f6a8 Ruptures (Stock = 0)"].configure(
            text=f"\U0001f6a8 Ruptures ({len(out_prods)})")

        low_prods = StockService.get_low_stock_alerts()
        rows_low = []
        for p in low_prods:
            rows_low.append([
                p["barcode"], p["name"][:35], p["brand"] or "-",
                f"{p['stock_qty']} u.", f"{p['min_stock_alert']} u.",
                p["supplier_name"] or "Non assign\u00e9"
            ])
        self.table_low.set_data(rows_low)
        self.tabview._segmented_button._buttons_dict["\u26a0\ufe0f Stocks Bas (Sous Seuil)"].configure(
            text=f"\u26a0\ufe0f Stocks Bas ({len(low_prods)})")

        exp_prods = StockService.get_expiring_alerts(days=90)
        rows_exp = []
        for p in exp_prods:
            rows_exp.append([
                p["barcode"], p["name"][:35], f"{p['stock_qty']} u.",
                p["expiry_date"] or "-", p["supplier_name"] or "Non assign\u00e9"
            ])
        self.table_expiry.set_data(rows_exp)
        self.tabview._segmented_button._buttons_dict["\u23f3 P\u00e9remptions Proches"].configure(
            text=f"\u23f3 P\u00e9remptions ({len(exp_prods)})")

    # ── STEP 1: Supplier selection modal ────────────────────────────────────
    def _open_supplier_selection_modal(self):
        from database.db_manager import get_db
        db = get_db()
        alert_suppliers = db.execute_query("""
            SELECT DISTINCT s.id, s.name, s.phone, COUNT(p.id) as alert_count
            FROM products p
            JOIN suppliers s ON p.supplier_id = s.id
            WHERE p.is_active = 1 AND p.stock_qty <= p.min_stock_alert
            GROUP BY s.id
            ORDER BY s.name ASC
        """)

        if not alert_suppliers:
            ToastNotification.show(self, "Aucun produit en alerte n\u00e9cessitant une commande.", "warning")
            return

        modal = BaseModal(self.winfo_toplevel(), "\U0001f4cb S\u00e9lectionner un Fournisseur", width=620, height=500)

        ctk.CTkLabel(
            modal.body,
            text="Choisissez le fournisseur pour g\u00e9n\u00e9rer un bon de commande ou r\u00e9ceptionner des marchandises :",
            font=FONTS["body"],
            wraplength=560,
            text_color=("gray30", "gray80")
        ).pack(anchor="w", pady=(0, 15))

        scroll = ctk.CTkScrollableFrame(modal.body, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        for sup in alert_suppliers:
            sup_dict = dict(sup)

            card = ctk.CTkFrame(scroll, fg_color=("white", "#1E293B"), corner_radius=10,
                                border_width=1, border_color=("gray80", "#334155"))
            card.pack(fill="x", pady=6, padx=4)

            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=15, pady=12)

            ctk.CTkLabel(info_frame, text=f"\U0001f3ed  {sup_dict['name']}", font=FONTS["body_bold"],
                         text_color=COLORS["primary"]).pack(anchor="w")
            ctk.CTkLabel(
                info_frame,
                text=f"\U0001f4e6 {sup_dict['alert_count']} produit(s) en alerte  \u2022  \U0001f4de {sup_dict['phone'] or 'Non renseign\u00e9'}",
                font=FONTS["caption"], text_color=("gray40", "gray60")
            ).pack(anchor="w", pady=(3, 0))

            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(side="right", padx=15, pady=12)

            ctk.CTkButton(
                btn_frame,
                text="\U0001f4cb G\u00e9n\u00e9rer BC",
                width=160,
                height=36,
                font=FONTS["caption_bold"],
                fg_color=COLORS["primary"],
                hover_color=COLORS["primary_hover"],
                command=lambda s=sup_dict, m=modal: self._generate_bc_for_supplier(s, m)
            ).pack(pady=(0, 6))

            ctk.CTkButton(
                btn_frame,
                text="\U0001f4e5 R\u00e9ception Marchandise",
                width=160,
                height=36,
                font=FONTS["caption_bold"],
                fg_color=COLORS["info"],
                hover_color=COLORS["info_hover"],
                command=lambda s=sup_dict, m=modal: self._open_reception_modal(s, m)
            ).pack()

    # ── Generate BC for one supplier — Interactive form ─────────────────────
    def _generate_bc_for_supplier(self, supplier, parent_modal):
        from database.db_manager import get_db
        db = get_db()
        alert_products = db.execute_query("""
            SELECT p.* FROM products p
            WHERE p.is_active = 1 AND p.stock_qty <= p.min_stock_alert
            AND p.supplier_id = ? ORDER BY p.name ASC
        """, (supplier["id"],))

        if not alert_products:
            ToastNotification.show(parent_modal, "Aucun produit en alerte pour ce fournisseur.", "warning")
            return
        parent_modal.destroy()

        bc_modal = BaseModal(self.winfo_toplevel(),
                             f"\U0001f4cb Créer Bon de Commande — {supplier['name']}",
                             width=820, height=680)

        # Header with supplier selector
        hdr = ctk.CTkFrame(bc_modal.body, fg_color=("white", "#1E293B"), corner_radius=8,
                           border_width=1, border_color=("gray80", "#334155"))
        hdr.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(hdr, text=f"\U0001f3ed  {supplier['name']}",
                     font=FONTS["body_bold"], text_color=COLORS["primary"]).pack(side="left", padx=15, pady=10)

        all_suppliers = SupplierService.get_suppliers()
        sup_names = [s["name"] for s in all_suppliers]
        sup_map = {s["name"]: s["id"] for s in all_suppliers}
        ctk.CTkLabel(hdr, text="Fournisseur :", font=FONTS["caption_bold"]).pack(side="right", padx=(0, 4), pady=10)
        sup_cb = ctk.CTkComboBox(hdr, values=sup_names, width=230, height=30, font=FONTS["body"])
        sup_cb.set(supplier["name"])
        sup_cb.pack(side="right", padx=(0, 15), pady=10)

        ctk.CTkLabel(bc_modal.body,
                     text="Ajustez les quantités à commander puis validez :",
                     font=FONTS["caption_bold"], text_color=("gray30", "gray80")).pack(anchor="w", pady=(0, 4))

        # Column headers
        col_hdr = ctk.CTkFrame(bc_modal.body, fg_color=("gray90", "#0F172A"), corner_radius=6, height=34)
        col_hdr.pack(fill="x", pady=(0, 4))
        col_hdr.pack_propagate(False)
        for ci, (txt, w) in enumerate([("Désignation", 4), ("Stock Actuel", 2), ("Qté à Commander", 2), ("Prix Achat DA", 2)]):
            col_hdr.grid_columnconfigure(ci, weight=w, uniform="bcc")
            ctk.CTkLabel(col_hdr, text=txt.upper(), font=FONTS["caption_bold"],
                         text_color=("gray40", "gray60")).grid(row=0, column=ci, padx=8, pady=6, sticky="ew")

        scroll = ctk.CTkScrollableFrame(bc_modal.body, fg_color="transparent")
        scroll.pack(fill="both", expand=True, pady=(0, 6))

        bc_entries = []
        for p in alert_products:
            prod = dict(p)
            suggested = max(10, (prod["min_stock_alert"] * 3) - prod["stock_qty"])
            row = ctk.CTkFrame(scroll, fg_color=("white", "#1A2333"), corner_radius=6, height=44)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)
            for ci, w in enumerate([4, 2, 2, 2]):
                row.grid_columnconfigure(ci, weight=w, uniform="bcc")
            ctk.CTkLabel(row, text=prod["name"][:36], font=FONTS["body"], anchor="w").grid(row=0, column=0, padx=8, pady=4, sticky="ew")
            sc = COLORS["danger"] if prod["stock_qty"] <= 0 else COLORS["warning"]
            ctk.CTkLabel(row, text=f"{prod['stock_qty']} u.", font=FONTS["body_bold"], text_color=sc).grid(row=0, column=1, padx=8, pady=4)
            qty_e = ctk.CTkEntry(row, height=32, font=FONTS["body_bold"], justify="center")
            qty_e.insert(0, str(suggested))
            qty_e.grid(row=0, column=2, padx=8, pady=4, sticky="ew")
            price_e = ctk.CTkEntry(row, height=32, font=FONTS["body"], justify="center")
            price_e.insert(0, str(int(prod["purchase_price"])))
            price_e.grid(row=0, column=3, padx=8, pady=4, sticky="ew")
            bc_entries.append((prod, qty_e, price_e))

        def confirm_bc():
            chosen_id = sup_map.get(sup_cb.get(), supplier["id"])
            items = []
            for prod, qe, pe in bc_entries:
                try:
                    q = int(qe.get() or 0)
                    pr = float(pe.get() or prod["purchase_price"])
                    if q > 0:
                        items.append({"product_id": prod["id"], "name": prod["name"],
                                      "barcode": prod["barcode"], "unit_cost": pr,
                                      "qty_ordered": q, "is_new_product": 0})
                except (ValueError, TypeError):
                    pass
            if not items:
                ToastNotification.show(bc_modal, "Aucune quantité saisie.", "warning")
                return
            ok, msg, oid, ocode = SupplierService.create_purchase_order(
                supplier_id=chosen_id, items=items, status="en_attente",
                notes="Généré depuis alertes stock")
            if ok:
                bc_modal.destroy()
                ToastNotification.show(self, f"✅ BC {ocode} créé — {len(items)} article(s)", "success")
                self.load_alerts()
                if self.on_navigate:
                    self.on_navigate("suppliers")
            else:
                ToastNotification.show(bc_modal, f"Erreur : {msg}", "danger")

        ctk.CTkButton(bc_modal.body, text="✅ CONFIRMER ET CRÉER LE BON DE COMMANDE",
                      height=44, font=FONTS["body_bold"],
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      command=confirm_bc).pack(fill="x", side="bottom", pady=(8, 0))

    # ── STEP 2: Reception modal ─────────────────────────────────────────────
    def _open_reception_modal(self, supplier, parent_modal):
        parent_modal.destroy()

        modal = BaseModal(
            self.winfo_toplevel(),
            f"\U0001f4e6 R\u00e9ception Marchandise \u2014 {supplier['name']}",
            width=760, height=660
        )

        sup_hdr = ctk.CTkFrame(modal.body, fg_color=("white", "#1E293B"), corner_radius=8,
                               border_width=1, border_color=("gray80", "#334155"))
        sup_hdr.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(sup_hdr, text=f"\U0001f3ed  Fournisseur : {supplier['name']}",
                     font=FONTS["body_bold"], text_color=COLORS["info"]).pack(side="left", padx=15, pady=10)

        ctk.CTkLabel(modal.body, text="V\u00e9rifiez et modifiez les quantit\u00e9s re\u00e7ues :",
                     font=FONTS["caption_bold"], text_color=("gray30", "gray80")).pack(anchor="w", pady=(0, 6))

        from database.db_manager import get_db
        db = get_db()
        alert_products = db.execute_query("""
            SELECT p.* FROM products p
            WHERE p.is_active = 1 AND p.stock_qty <= p.min_stock_alert
            AND p.supplier_id = ?
            ORDER BY p.name ASC
        """, (supplier["id"],))

        self._reception_entries = []

        scroll = ctk.CTkScrollableFrame(modal.body, fg_color="transparent", height=420)
        scroll.pack(fill="both", expand=True)

        if not alert_products:
            ctk.CTkLabel(scroll, text="Aucun produit en alerte pour ce fournisseur.",
                         font=FONTS["body"], text_color=COLORS["warning"]).pack(pady=20)
        else:
            hdr = ctk.CTkFrame(scroll, fg_color=("gray90", "#0F172A"), corner_radius=6, height=34)
            hdr.pack(fill="x", pady=(0, 4))
            hdr.pack_propagate(False)
            hdr.grid_columnconfigure(0, weight=4)
            hdr.grid_columnconfigure(1, weight=2)
            hdr.grid_columnconfigure(2, weight=2)
            hdr.grid_columnconfigure(3, weight=2)
            for ci, txt in enumerate(["D\u00e9signation", "Stock Actuel", "Qt\u00e9 \u00e0 Recevoir", "Prix Achat (DA)"]):
                ctk.CTkLabel(hdr, text=txt.upper(), font=FONTS["caption_bold"],
                             text_color=("gray40", "gray60")).grid(row=0, column=ci, padx=8, pady=6, sticky="ew")

            for p in alert_products:
                prod = dict(p)
                suggested_qty = max(10, (prod["min_stock_alert"] * 3) - prod["stock_qty"])

                row = ctk.CTkFrame(scroll, fg_color=("white", "#1A2333"), corner_radius=6, height=44)
                row.pack(fill="x", pady=2)
                row.pack_propagate(False)
                row.grid_columnconfigure(0, weight=4)
                row.grid_columnconfigure(1, weight=2)
                row.grid_columnconfigure(2, weight=2)
                row.grid_columnconfigure(3, weight=2)

                ctk.CTkLabel(row, text=prod["name"][:32], font=FONTS["body"],
                             anchor="w").grid(row=0, column=0, padx=8, pady=4, sticky="ew")

                stock_color = COLORS["danger"] if prod["stock_qty"] <= 0 else COLORS["warning"]
                ctk.CTkLabel(row, text=f"{prod['stock_qty']} u.", font=FONTS["body_bold"],
                             text_color=stock_color).grid(row=0, column=1, padx=8, pady=4)

                qty_entry = ctk.CTkEntry(row, height=32, font=FONTS["body"])
                qty_entry.insert(0, str(suggested_qty))
                qty_entry.grid(row=0, column=2, padx=8, pady=4, sticky="ew")

                price_entry = ctk.CTkEntry(row, height=32, font=FONTS["body"])
                price_entry.insert(0, str(int(prod["purchase_price"])))
                price_entry.grid(row=0, column=3, padx=8, pady=4, sticky="ew")

                self._reception_entries.append((prod, qty_entry, price_entry))

        def validate_reception():
            user = AuthService.get_current_user()
            user_id = user.id if user else 1
            success_count = 0
            errors = []
            for prod, qty_e, price_e in self._reception_entries:
                try:
                    qty = int(qty_e.get() or 0)
                    price = float(price_e.get() or 0)
                    if qty <= 0:
                        continue
                    ok, msg = StockService.add_reception(
                        product_id=prod["id"], qty=qty, purchase_price=price,
                        user_id=user_id, reason=f"R\u00e9ception fournisseur {supplier['name']}"
                    )
                    if ok:
                        success_count += 1
                    else:
                        errors.append(msg)
                except (ValueError, TypeError):
                    errors.append(f"Valeur invalide pour {prod['name']}")

            modal.destroy()
            if success_count > 0:
                ToastNotification.show(self, f"\u2705 {success_count} produit(s) r\u00e9ceptionn\u00e9(s) avec succ\u00e8s !", "success")
                self.load_alerts()
            if errors:
                ToastNotification.show(self, f"\u26a0\ufe0f {len(errors)} erreur(s) : {errors[0]}", "warning")

        ctk.CTkButton(
            modal.body,
            text="\u2705 VALIDER LA R\u00c9CEPTION EN STOCK",
            height=44,
            font=FONTS["body_bold"],
            fg_color=COLORS["emerald"],
            hover_color=COLORS["emerald_hover"],
            command=validate_reception
        ).pack(fill="x", side="bottom", pady=(10, 0))
