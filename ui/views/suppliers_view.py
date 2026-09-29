import customtkinter as ctk
from ui.theme import FONTS, COLORS
from services.supplier_service import SupplierService
from services.stock_service import StockService
from services.auth_service import AuthService
from services.barcode_service import BarcodeService
from config import CATEGORIES
from ui.components.modern_table import ModernTable
from ui.components.modal import BaseModal
from ui.components.notification import ToastNotification


class SuppliersView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self, corner_radius=12, fg_color=("white", "#1E293B"))
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)

        self.tab_suppliers = self.tabview.add("🏭 Répertoire Fournisseurs")
        self.tab_orders = self.tabview.add("📋 Bons de Commande & Réceptions")
        self.tab_traceability = self.tabview.add("🔍 Traçabilité Nouveaux Produits")

        self._setup_suppliers_tab()
        self._setup_orders_tab()
        self._setup_traceability_tab()

    # ══════════════════════════════════════════════════════════════════════════
    # 1. RÉPERTOIRE FOURNISSEURS
    # ══════════════════════════════════════════════════════════════════════════
    def _setup_suppliers_tab(self):
        self.tab_suppliers.grid_columnconfigure(0, weight=1)
        self.tab_suppliers.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(self.tab_suppliers, fg_color="transparent", height=45)
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        self.sup_search = ctk.CTkEntry(top, placeholder_text="🔍 Rechercher fournisseur...", width=280, height=36)
        self.sup_search.pack(side="left")
        self.sup_search.bind("<KeyRelease>", lambda e: self.load_suppliers())

        ctk.CTkButton(top, text="+ Nouveau Fournisseur", height=36, font=FONTS["body_bold"],
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      command=self._open_add_supplier_modal).pack(side="right")

        cols = [
            ("Fournisseur", 3, "w"),
            ("Contact", 3, "w"),
            ("Téléphone", 2, "w"),
            ("Email", 3, "w"),
            ("Adresse", 4, "w"),
            ("Produits Liés", 2, "center")
        ]
        self.sup_table = ModernTable(self.tab_suppliers, cols)
        self.sup_table.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.load_suppliers()

    def load_suppliers(self):
        search = self.sup_search.get().strip() if hasattr(self, 'sup_search') else ""
        suppliers = SupplierService.get_suppliers(search)
        rows = []
        for s in suppliers:
            s_dict = dict(s)
            rows.append([
                s_dict.get("name", "-"), s_dict.get("contact_person") or "-", s_dict.get("phone") or "-",
                s_dict.get("email") or "-", s_dict.get("address") or "-", f"{s_dict.get('product_count', 0)} réf."
            ])
        self.sup_table.set_data(rows)

    def _open_add_supplier_modal(self, on_created_callback=None):
        modal = BaseModal(self.winfo_toplevel(), "Nouveau Fournisseur Cosmétique", width=540, height=520)

        ctk.CTkLabel(modal.body, text="Nom de l'entreprise / Société *", font=FONTS["caption_bold"]).pack(anchor="w", pady=(0, 2))
        name_entry = ctk.CTkEntry(modal.body, height=36, font=FONTS["body"])
        name_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(modal.body, text="Personne de contact", font=FONTS["caption_bold"]).pack(anchor="w", pady=(0, 2))
        contact_entry = ctk.CTkEntry(modal.body, height=36, font=FONTS["body"])
        contact_entry.pack(fill="x", pady=(0, 10))

        grid = ctk.CTkFrame(modal.body, fg_color="transparent")
        grid.pack(fill="x", pady=(0, 10))
        grid.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkLabel(grid, text="Téléphone", font=FONTS["caption_bold"]).grid(row=0, column=0, sticky="w", padx=(0, 5))
        ctk.CTkLabel(grid, text="Email", font=FONTS["caption_bold"]).grid(row=0, column=1, sticky="w", padx=(5, 0))
        phone_entry = ctk.CTkEntry(grid, height=36, font=FONTS["body"])
        phone_entry.grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=(2, 0))
        email_entry = ctk.CTkEntry(grid, height=36, font=FONTS["body"])
        email_entry.grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=(2, 0))

        ctk.CTkLabel(modal.body, text="Adresse", font=FONTS["caption_bold"]).pack(anchor="w", pady=(0, 2))
        addr_entry = ctk.CTkEntry(modal.body, height=36, font=FONTS["body"])
        addr_entry.pack(fill="x", pady=(0, 15))

        def save():
            name = name_entry.get().strip()
            if not name:
                ToastNotification.show(modal, "Le nom du fournisseur est obligatoire", "warning")
                return
            success, msg, sid = SupplierService.add_supplier(
                name=name, contact_person=contact_entry.get().strip(),
                phone=phone_entry.get().strip(), email=email_entry.get().strip(),
                address=addr_entry.get().strip()
            )
            if success:
                modal.destroy()
                ToastNotification.show(self, msg, "success")
                self.load_suppliers()
                if on_created_callback:
                    on_created_callback(sid, name)
            else:
                ToastNotification.show(modal, msg, "danger")

        ctk.CTkButton(modal.body, text="ENREGISTRER FOURNISSEUR", height=42,
                      font=FONTS["body_bold"], fg_color=COLORS["primary"],
                      command=save).pack(fill="x", side="bottom")

    # ══════════════════════════════════════════════════════════════════════════
    # 2. BONS DE COMMANDE & RÉCEPTIONS
    # ══════════════════════════════════════════════════════════════════════════
    def _setup_orders_tab(self):
        self.tab_orders.grid_columnconfigure(0, weight=1)
        self.tab_orders.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(self.tab_orders, fg_color="transparent", height=45)
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        self.po_search = ctk.CTkEntry(top, placeholder_text="🔍 Rechercher N° Commande / Fournisseur...", width=260, height=36)
        self.po_search.pack(side="left", padx=(0, 10))
        self.po_search.bind("<KeyRelease>", lambda e: self.load_orders())

        ctk.CTkLabel(top, text="Filtrer :", font=FONTS["caption_bold"]).pack(side="left", padx=(0, 5))
        self.po_filter_menu = ctk.CTkOptionMenu(
            top, values=["Tous", "En attente", "Reçu complet", "Reçu partiel", "Brouillon"],
            width=140, height=36, font=FONTS["body"],
            command=lambda v: self.load_orders()
        )
        self.po_filter_menu.pack(side="left", padx=(0, 10))

        ctk.CTkButton(top, text="+ Nouveau Bon de Commande", height=36, font=FONTS["body_bold"],
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      command=self._open_create_po_modal).pack(side="right", padx=(5, 0))

        ctk.CTkButton(top, text="🔄 Actualiser", width=90, height=36,
                      font=FONTS["caption_bold"], fg_color=COLORS.get("card_hover", "#334155"),
                      command=self.load_orders).pack(side="right")

        cols = [
            ("N° Commande", 3, "w"),
            ("Fournisseur", 3, "w"),
            ("Date Création", 2, "w"),
            ("Total Estimé", 2, "e"),
            ("Avancement Réception", 3, "center"),
            ("Statut", 2, "center"),
            ("Actions", 4, "center")
        ]
        self.orders_table = ModernTable(self.tab_orders, cols)
        self.orders_table.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.load_orders()

    def load_orders(self):
        status = self.po_filter_menu.get() if hasattr(self, 'po_filter_menu') else "Tous"
        search = self.po_search.get().strip() if hasattr(self, 'po_search') else ""
        orders = SupplierService.get_purchase_orders(status_filter=status, search=search)
        rows = []
        for o in orders:
            o_dict = dict(o)

            status_map = {
                "en_attente": ("⏳ En attente", COLORS["warning"]),
                "brouillon": ("📝 Brouillon", "gray60"),
                "recu_complet": ("✅ Reçu complet", COLORS["emerald"]),
                "recu_partiel": ("🟠 Reçu partiel", "#F97316"),
                "annule": ("❌ Annulé", COLORS["danger"])
            }
            label_txt, color_txt = status_map.get(o_dict.get("status", "en_attente"), (o_dict.get("status", "en_attente"), "gray60"))

            def make_status_cell(parent, lt=label_txt, col=color_txt):
                f = ctk.CTkFrame(parent, fg_color="transparent")
                ctk.CTkLabel(f, text=lt, font=FONTS["caption_bold"], text_color=col).pack()
                return f

            tot_items = o_dict.get("items_count") or 0
            comp_items = o_dict.get("compliant_items_count") or 0
            progress_str = f"{comp_items}/{tot_items} art. reçus"

            def make_actions_btn(parent, order=o_dict):
                f = ctk.CTkFrame(parent, fg_color="transparent")

                if order.get("status") != "recu_complet":
                    ctk.CTkButton(
                        f, text="📥 Réception", width=85, height=26,
                        font=FONTS["caption_bold"],
                        fg_color=COLORS["emerald"], hover_color=COLORS["emerald_hover"],
                        command=lambda ord=order: self._open_reception_flow(ord)
                    ).pack(side="left", padx=2)

                ctk.CTkButton(
                    f, text="📄 PDF", width=60, height=26,
                    font=FONTS["caption_bold"],
                    fg_color=COLORS["info"], hover_color=COLORS["info_hover"],
                    command=lambda ord=order: self._open_order_pdf(ord)
                ).pack(side="left", padx=2)

                ctk.CTkButton(
                    f, text="🔍 Audit", width=60, height=26,
                    font=FONTS["caption_bold"],
                    fg_color=COLORS.get("card_hover", "#334155"), hover_color="#334155",
                    command=lambda ord=order: self._open_po_traceability_modal(ord)
                ).pack(side="left", padx=2)

                return f

            rows.append([
                o_dict.get("order_code", "-"),
                o_dict.get("supplier_name", "-"),
                o_dict.get("created_at", "")[:16] if o_dict.get("created_at") else "-",
                f"{o_dict.get('total_amount', 0):,.0f} DA".replace(",", " "),
                progress_str,
                make_status_cell,
                make_actions_btn
            ])
        self.orders_table.set_data(rows)

    def _open_order_pdf(self, order):
        order = dict(order)
        ToastNotification.show(self, "Génération du PDF en cours...", "info")
        self.after(100, lambda: self._do_generate_pdf(order))

    def _do_generate_pdf(self, order):
        order = dict(order)
        pdf_path, err = SupplierService.generate_order_pdf(order["id"])
        if pdf_path:
            try:
                from ui.components.pdf_viewer import PdfViewerModal
                PdfViewerModal(self.winfo_toplevel(), pdf_path, f"Bon de Commande — {order['order_code']}")
            except Exception as ex:
                ToastNotification.show(self, f"PDF généré : {pdf_path} (erreur visionneuse : {ex})", "success")
        else:
            ToastNotification.show(self, f"Erreur : {err}", "danger")

    # ══════════════════════════════════════════════════════════════════════════
    # ÉTAPE 1 : CRÉATION D'UN BON DE COMMANDE FOURNISSEUR
    # ══════════════════════════════════════════════════════════════════════════
    def _open_create_po_modal(self):
        modal = BaseModal(self.winfo_toplevel(), "📋 Nouveau Bon de Commande Fournisseur", width=860, height=680)

        sup_frame = ctk.CTkFrame(modal.body, fg_color=("white", "#1E293B"), corner_radius=10,
                                 border_width=1, border_color=("gray80", "#334155"))
        sup_frame.pack(fill="x", pady=(0, 10), padx=5)

        sup_hdr = ctk.CTkFrame(sup_frame, fg_color="transparent")
        sup_hdr.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(sup_hdr, text="Fournisseur :", font=FONTS["caption_bold"]).pack(side="left", padx=(0, 10))

        suppliers = SupplierService.get_suppliers()
        sup_dict_map = {s["name"]: s["id"] for s in suppliers}
        sup_names = list(sup_dict_map.keys())

        if not sup_names:
            sup_names = ["(Aucun fournisseur existant)"]

        sup_menu = ctk.CTkOptionMenu(sup_hdr, values=sup_names, width=280, height=36, font=FONTS["body"])
        sup_menu.pack(side="left", padx=(0, 10))

        def add_new_sup_inline():
            def on_created(sid, sname):
                suppliers_new = SupplierService.get_suppliers()
                sup_dict_map.clear()
                for s in suppliers_new:
                    sup_dict_map[s["name"]] = s["id"]
                sup_menu.configure(values=list(sup_dict_map.keys()))
                sup_menu.set(sname)
            self._open_add_supplier_modal(on_created_callback=on_created)

        ctk.CTkButton(sup_hdr, text="+ Nouveau Fournisseur", width=160, height=36,
                      font=FONTS["caption_bold"], fg_color=COLORS.get("card_hover", "#334155"),
                      command=add_new_sup_inline).pack(side="right")

        add_box = ctk.CTkFrame(modal.body, fg_color=("gray95", "#0F172A"), corner_radius=10,
                               border_width=1, border_color=("gray80", "#334155"))
        add_box.pack(fill="x", pady=(0, 10), padx=5)

        tab_type = ctk.CTkSegmentedButton(add_box, values=["💄 Produit du Catalogue", "✨ Nouveau Produit (Non Référencé)"])
        tab_type.set("💄 Produit du Catalogue")
        tab_type.pack(fill="x", padx=12, pady=(10, 8))

        inputs_container = ctk.CTkFrame(add_box, fg_color="transparent")
        inputs_container.pack(fill="x", padx=12, pady=(0, 10))

        order_items = []

        cat_search_frame = ctk.CTkFrame(inputs_container, fg_color="transparent")
        ctk.CTkLabel(cat_search_frame, text="Recherche ou Scan Code-barres :", font=FONTS["caption_bold"]).pack(anchor="w")
        cat_prod_entry = ctk.CTkEntry(cat_search_frame, placeholder_text="Scannez ou tapez nom du produit...", height=34, font=FONTS["body"])
        cat_prod_entry.pack(fill="x", pady=(2, 6))

        all_catalog_prods = [dict(p) for p in StockService.get_products()]
        prod_map = {f"{p['name']} ({p['barcode']}) - {p['purchase_price']:.0f} DA": p for p in all_catalog_prods}
        prod_choices = list(prod_map.keys()) if prod_map else ["(Catalogue vide)"]

        cat_prod_menu = ctk.CTkOptionMenu(cat_search_frame, values=prod_choices, height=34, font=FONTS["body"])
        cat_prod_menu.pack(fill="x", pady=(0, 6))

        def on_search_cat(e=None):
            q = cat_prod_entry.get().strip()
            if not q:
                return
            filtered = [p for p in all_catalog_prods if q.lower() in p['name'].lower() or q == p['barcode']]
            if filtered:
                new_choices = [f"{p['name']} ({p['barcode']}) - {p['purchase_price']:.0f} DA" for p in filtered]
                cat_prod_menu.configure(values=new_choices)
                cat_prod_menu.set(new_choices[0])
                cat_price_entry.delete(0, "end")
                cat_price_entry.insert(0, str(int(filtered[0]["purchase_price"])))

        cat_prod_entry.bind("<Return>", on_search_cat)
        cat_prod_entry.bind("<KeyRelease>", on_search_cat)

        all_cats = StockService.get_all_categories()

        def on_cat_select(choice):
            p = prod_map.get(choice)
            if p:
                cat_price_entry.delete(0, "end")
                cat_price_entry.insert(0, str(int(p["purchase_price"])))
                cat_cat_cb.set(p.get("category") or "Soins Visage")

        cat_prod_menu.configure(command=on_cat_select)

        cat_grid = ctk.CTkFrame(cat_search_frame, fg_color="transparent")
        cat_grid.pack(fill="x", pady=(4, 0))
        cat_grid.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(cat_grid, text="Quantité Commandée :", font=FONTS["caption_bold"]).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(cat_grid, text="Prix d'Achat Unitaire (DA) :", font=FONTS["caption_bold"]).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(cat_grid, text="Catégorie du Produit :", font=FONTS["caption_bold"]).grid(row=0, column=2, sticky="w")

        cat_qty_entry = ctk.CTkEntry(cat_grid, height=34, font=FONTS["body"])
        cat_qty_entry.insert(0, "10")
        cat_qty_entry.grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=(2, 0))

        cat_price_entry = ctk.CTkEntry(cat_grid, height=34, font=FONTS["body"])
        if all_catalog_prods:
            cat_price_entry.insert(0, str(int(all_catalog_prods[0]["purchase_price"])))
        cat_price_entry.grid(row=1, column=1, sticky="ew", padx=(5, 5), pady=(2, 0))

        cat_cat_cb = ctk.CTkComboBox(cat_grid, values=all_cats, height=34, font=FONTS["body"])
        if all_catalog_prods:
            cat_cat_cb.set(all_catalog_prods[0].get("category") or "Soins Visage")
        cat_cat_cb.grid(row=1, column=2, sticky="ew", padx=(5, 0), pady=(2, 0))

        new_prod_frame = ctk.CTkFrame(inputs_container, fg_color="transparent")
        
        np_g1 = ctk.CTkFrame(new_prod_frame, fg_color="transparent")
        np_g1.pack(fill="x", pady=(0, 4))
        np_g1.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(np_g1, text="Nom du Produit * :", font=FONTS["caption_bold"]).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(np_g1, text="Catégorie * (Choisir ou Saisir) :", font=FONTS["caption_bold"]).grid(row=0, column=1, sticky="w")

        np_name_entry = ctk.CTkEntry(np_g1, placeholder_text="Ex: Crème Anti-Rides 50ml", height=34, font=FONTS["body"])
        np_name_entry.grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=(2, 0))

        np_cat_cb = ctk.CTkComboBox(np_g1, values=all_cats, height=34, font=FONTS["body"])
        np_cat_cb.set("Soins Visage")
        np_cat_cb.grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=(2, 0))

        np_g2 = ctk.CTkFrame(new_prod_frame, fg_color="transparent")
        np_g2.pack(fill="x", pady=(4, 0))
        np_g2.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(np_g2, text="Code-barres (si connu) :", font=FONTS["caption_bold"]).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(np_g2, text="Prix Achat Prévisionnel (DA) :", font=FONTS["caption_bold"]).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(np_g2, text="Quantité Commandée :", font=FONTS["caption_bold"]).grid(row=0, column=2, sticky="w")

        np_bc_entry = ctk.CTkEntry(np_g2, placeholder_text="Code-barres ou vide", height=34, font=FONTS["body"])
        np_bc_entry.grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=(2, 0))

        np_price_entry = ctk.CTkEntry(np_g2, placeholder_text="Ex: 850", height=34, font=FONTS["body"])
        np_price_entry.insert(0, "500")
        np_price_entry.grid(row=1, column=1, sticky="ew", padx=(5, 5), pady=(2, 0))

        np_qty_entry = ctk.CTkEntry(np_g2, placeholder_text="Ex: 12", height=34, font=FONTS["body"])
        np_qty_entry.insert(0, "10")
        np_qty_entry.grid(row=1, column=2, sticky="ew", padx=(5, 0), pady=(2, 0))

        def toggle_tab(value):
            if "Catalogue" in value:
                new_prod_frame.pack_forget()
                cat_search_frame.pack(fill="x")
            else:
                cat_search_frame.pack_forget()
                new_prod_frame.pack(fill="x")

        tab_type.configure(command=toggle_tab)
        cat_search_frame.pack(fill="x")

        # Bottom footer packed FIRST so it's always visible and pinned to the bottom
        btn_row = ctk.CTkFrame(modal.body, fg_color="transparent")
        btn_row.pack(fill="x", side="bottom", pady=(8, 0))

        tot_row = ctk.CTkFrame(btn_row, fg_color="transparent")
        tot_row.pack(fill="x", pady=(0, 6))

        items_count_lbl = ctk.CTkLabel(tot_row, text="0 article(s) sélectionné(s)", font=FONTS["body"], text_color=COLORS["text_secondary"])
        items_count_lbl.pack(side="left")

        total_lbl = ctk.CTkLabel(tot_row, text="TOTAL ESTIMÉ : 0 DA", font=FONTS["title_small"], text_color=COLORS["primary"])
        total_lbl.pack(side="right")

        def save_purchase_order():
            sup_name = sup_menu.get()
            sid = sup_dict_map.get(sup_name)
            if not sid:
                ToastNotification.show(modal, "Veuillez choisir un fournisseur valide", "warning")
                return
            if not order_items:
                ToastNotification.show(modal, "Veuillez ajouter au moins un produit à commander", "warning")
                return

            ok, msg, order_id, order_code = SupplierService.create_purchase_order(
                supplier_id=sid,
                items=order_items,
                status="en_attente",
                notes=""
            )
            if ok:
                modal.destroy()
                ToastNotification.show(self, f"✅ Bon de commande {order_code} créé avec succès !", "success")
                self.load_orders()
            else:
                ToastNotification.show(modal, msg, "danger")

        ctk.CTkButton(btn_row, text="📋 VALIDER ET ENREGISTRER LE BON DE COMMANDE", height=46,
                      font=FONTS["body_bold"], fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      command=save_purchase_order).pack(fill="x")

        # Table in the center expanding to fill available space
        items_frame = ctk.CTkFrame(modal.body, fg_color="transparent")
        items_frame.pack(fill="both", expand=True, pady=(6, 6))

        cols = [
            ("Type", 1, "center"),
            ("Code-barres", 2, "w"),
            ("Désignation", 4, "w"),
            ("Catégorie", 2, "w"),
            ("Prix Unitaire", 2, "e"),
            ("Qté Cde", 2, "center"),
            ("Total Ligne", 2, "e"),
            ("Suppr", 1, "center")
        ]
        items_table = ModernTable(items_frame, cols)
        items_table.pack(fill="both", expand=True)

        def refresh_table_items():
            rows = []
            tot = 0.0
            for idx, item in enumerate(order_items):
                type_tag = "💄 Catalogue" if not item.get("is_new_product") else "✨ Nouveau"
                line_total = item["qty_ordered"] * item["unit_cost"]
                tot += line_total

                def make_del_btn(parent, index=idx):
                    f = ctk.CTkFrame(parent, fg_color="transparent")
                    ctk.CTkButton(f, text="✕", width=28, height=24, font=FONTS["caption_bold"],
                                  fg_color=COLORS["danger"], hover_color=COLORS["rose"],
                                  command=lambda: delete_item(index)).pack()
                    return f

                rows.append([
                    type_tag,
                    item.get("barcode") or "(Non défini)",
                    item["name"][:35],
                    item.get("category") or "Soins Visage",
                    f"{item['unit_cost']:,.0f} DA",
                    f"{item['qty_ordered']} u.",
                    f"{line_total:,.0f} DA",
                    make_del_btn
                ])
            items_table.set_data(rows)
            total_lbl.configure(text=f"TOTAL ESTIMÉ : {tot:,.0f} DA".replace(",", " "))
            items_count_lbl.configure(text=f"{len(order_items)} article(s) à commander")

        def delete_item(index):
            if 0 <= index < len(order_items):
                order_items.pop(index)
                refresh_table_items()

        def add_item_to_list():
            mode = tab_type.get()
            if "Catalogue" in mode:
                sel = cat_prod_menu.get()
                p = prod_map.get(sel)
                if not p:
                    ToastNotification.show(modal, "Veuillez sélectionner un produit du catalogue", "warning")
                    return
                try:
                    qty = int(cat_qty_entry.get() or 1)
                    price = float(cat_price_entry.get() or p["purchase_price"])
                    chosen_cat = cat_cat_cb.get().strip() or p.get("category") or "Soins Visage"
                    if qty <= 0:
                        ToastNotification.show(modal, "Quantité invalide", "warning")
                        return
                    order_items.append({
                        "product_id": p["id"],
                        "name": p["name"],
                        "barcode": p["barcode"],
                        "category": chosen_cat,
                        "unit_cost": price,
                        "qty_ordered": qty,
                        "is_new_product": 0
                    })
                    refresh_table_items()
                    ToastNotification.show(modal, f"Ajouté : {p['name'][:25]} ({chosen_cat})", "success")
                except ValueError:
                    ToastNotification.show(modal, "Veuillez saisir des valeurs numériques valides", "danger")
            else:
                name = np_name_entry.get().strip()
                if not name:
                    ToastNotification.show(modal, "Le nom du produit est obligatoire", "warning")
                    return
                try:
                    qty = int(np_qty_entry.get() or 1)
                    price = float(np_price_entry.get() or 0)
                    bc = np_bc_entry.get().strip() or None
                    chosen_cat = np_cat_cb.get().strip() or "Soins Visage"
                    if qty <= 0:
                        ToastNotification.show(modal, "Quantité invalide", "warning")
                        return
                    order_items.append({
                        "product_id": None,
                        "name": name,
                        "barcode": bc,
                        "category": chosen_cat,
                        "unit_cost": price,
                        "qty_ordered": qty,
                        "is_new_product": 1
                    })
                    refresh_table_items()
                    np_name_entry.delete(0, "end")
                    ToastNotification.show(modal, f"Nouveau produit ajouté : {name[:25]} ({chosen_cat})", "success")
                except ValueError:
                    ToastNotification.show(modal, "Veuillez saisir des valeurs numériques valides", "danger")


        ctk.CTkButton(inputs_container, text="➕ Ajouter au Bon de Commande", height=36,
                      font=FONTS["caption_bold"], fg_color=COLORS["info"], hover_color=COLORS["info_hover"],
                      command=add_item_to_list).pack(fill="x", pady=(8, 0))

    # ══════════════════════════════════════════════════════════════════════════
    # ÉTAPE 2 & 3 : RÉCEPTION MARCHANDISE VIA SCAN CODE-BARRES & VÉRIFICATION
    # ══════════════════════════════════════════════════════════════════════════
    def _open_reception_flow(self, order):
        """Ouvre l'interface de réception complète avec scanner douchette."""
        order = dict(order)
        modal = BaseModal(self.winfo_toplevel(), f"📥 Réception Marchandise — {order['order_code']}", width=940, height=720)

        hdr_box = ctk.CTkFrame(modal.body, fg_color=("white", "#1E293B"), corner_radius=10,
                               border_width=1, border_color=("gray80", "#334155"))
        hdr_box.pack(fill="x", pady=(0, 10))

        h_grid = ctk.CTkFrame(hdr_box, fg_color="transparent")
        h_grid.pack(fill="x", padx=15, pady=10)
        h_grid.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(h_grid, text=f"🏭 Fournisseur : {order.get('supplier_name', '-')}", font=FONTS["body_bold"], text_color=COLORS["info"]).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(h_grid, text=f"📋 N° BC : {order.get('order_code', '-')}", font=FONTS["body_bold"], text_color=COLORS["primary"]).grid(row=0, column=1)
        created_str = order.get("created_at", "")
        ctk.CTkLabel(h_grid, text=f"📅 Date : {created_str[:10] if created_str else '-'}", font=FONTS["body"]).grid(row=0, column=2, sticky="e")

        scan_box = ctk.CTkFrame(modal.body, fg_color=("gray95", "#0F172A"), corner_radius=10,
                                border_width=1, border_color=("gray80", "#334155"))
        scan_box.pack(fill="x", pady=(0, 10))

        s_inner = ctk.CTkFrame(scan_box, fg_color="transparent")
        s_inner.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(s_inner, text="⚡ Scan Code-barres Douchette :", font=FONTS["caption_bold"], text_color=COLORS["info"]).pack(side="left", padx=(0, 10))

        bc_entry = ctk.CTkEntry(s_inner, placeholder_text="Scannez ici ou tapez code-barres...", height=38, font=FONTS["title_small"])
        bc_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        bc_entry.focus_set()

        db_items = SupplierService.get_order_items(order["id"])
        all_cats = StockService.get_all_categories() or ["Soins Visage", "Parfumerie", "Maquillage", "Capillaire", "Hygiène", "Accessoires"]
        
        reception_data = []
        for itm in db_items:
            itm_dict = dict(itm)
            purchase = float(itm_dict.get("unit_cost", 0))
            sale_default = round(purchase * 1.4, 0) if purchase > 0 else 0.0
            reception_data.append({
                "item_id": itm_dict["id"],
                "product_id": itm_dict["product_id"],
                "name": itm_dict.get("display_name") or itm_dict.get("product_name") or "Produit",
                "barcode": itm_dict.get("display_barcode") or itm_dict.get("barcode") or "",
                "category": itm_dict.get("product_category") or "Soins Visage",
                "unit_cost": purchase,
                "purchase_price": purchase,
                "sale_price": float(itm_dict.get("current_sale_price") or itm_dict.get("sale_price") or sale_default),
                "current_catalog_price": float(itm_dict.get("current_catalog_price") or purchase),
                "qty_ordered": int(itm_dict.get("qty_ordered", 0)),
                "qty_received": int(itm_dict.get("qty_received") or 0),
                "is_new_product": bool(itm_dict.get("is_new_product")),
                "update_catalog_price": False,
                "widgets": {}
            })

        kpi_bar = ctk.CTkFrame(modal.body, fg_color="transparent")
        kpi_bar.pack(fill="x", pady=(0, 6))

        kpi_total_lbl = ctk.CTkLabel(kpi_bar, text="Total Articles : 0", font=FONTS["caption_bold"])
        kpi_total_lbl.pack(side="left", padx=10)

        kpi_conf_lbl = ctk.CTkLabel(kpi_bar, text="✅ Conformes : 0", font=FONTS["caption_bold"], text_color=COLORS["emerald"])
        kpi_conf_lbl.pack(side="left", padx=10)

        kpi_part_lbl = ctk.CTkLabel(kpi_bar, text="⏳ Partiels : 0", font=FONTS["caption_bold"], text_color="#F97316")
        kpi_part_lbl.pack(side="left", padx=10)

        kpi_sur_lbl = ctk.CTkLabel(kpi_bar, text="⚠️ Surnuméraires : 0", font=FONTS["caption_bold"], text_color=COLORS["info"])
        kpi_sur_lbl.pack(side="left", padx=10)

        def finalize_reception():
            for it in reception_data:
                if "bc_entry" in it["widgets"]:
                    it["barcode"] = it["widgets"]["bc_entry"].get().strip()
                if "qty_entry" in it["widgets"]:
                    try:
                        it["qty_received"] = int(it["widgets"]["qty_entry"].get() or 0)
                    except ValueError:
                        pass
                if "price_entry" in it["widgets"]:
                    try:
                        it["unit_cost"] = float(it["widgets"]["price_entry"].get() or 0)
                        it["purchase_price"] = it["unit_cost"]
                    except ValueError:
                        pass
                if "sale_price_entry" in it["widgets"]:
                    try:
                        it["sale_price"] = float(it["widgets"]["sale_price_entry"].get() or 0)
                    except ValueError:
                        pass
                if "cat_cb" in it["widgets"]:
                    it["category"] = it["widgets"]["cat_cb"].get().strip() or "Soins Visage"

            valid_items = [it for it in reception_data if it["qty_received"] > 0]
            if not valid_items:
                ToastNotification.show(modal, "Aucune quantité reçue à valider.", "warning")
                return

            user = AuthService.get_current_user()
            uid = user.id if user else 1

            ok, res = SupplierService.process_reception(
                order_id=order["id"],
                received_items=valid_items,
                user_id=uid,
                notes=""
            )

            if ok:
                modal.destroy()
                status_msg = "Reçu complet" if res["po_status"] == "recu_complet" else "Reçu partiel (Reliquat conservé)"
                ToastNotification.show(
                    self,
                    f"✅ Réception validée !\n• Statut : {status_msg}\n• {res['existing_updated']} produit(s) mis à jour\n• {res['new_products_created']} nouveau(x) produit(s) créé(s)",
                    "success"
                )
                self.load_orders()
                self.load_traceability()
            else:
                ToastNotification.show(modal, f"Erreur : {res}", "danger")

        # Bottom validation bar packed FIRST
        btn_val = ctk.CTkButton(
            modal.body,
            text="✅ VALIDER LA RÉCEPTION EN STOCK",
            height=46, font=FONTS["body_bold"],
            fg_color=COLORS["emerald"], hover_color=COLORS["emerald_hover"],
            command=finalize_reception
        )
        btn_val.pack(fill="x", side="bottom", pady=(8, 0))

        table_container = ctk.CTkFrame(modal.body, fg_color="transparent")
        table_container.pack(fill="both", expand=True, pady=(6, 6))

        cols = [
            ("Code-barres", 2, "w"),
            ("Désignation", 3, "w"),
            ("Catégorie", 2, "center"),
            ("Qté Cde", 1, "center"),
            ("Qté Reçue", 1, "center"),
            ("Prix Achat DA", 2, "center"),
            ("Prix Vente DA", 2, "center"),
            ("Conformité", 2, "center"),
            ("MAJ Prix", 1, "center")
        ]
        rec_table = ModernTable(table_container, cols, row_height=42)
        rec_table.pack(fill="both", expand=True)

        def update_kpis():
            tot = len(reception_data)
            conf = 0
            part = 0
            sur = 0
            for item in reception_data:
                q_rec = item["qty_received"]
                q_ord = item["qty_ordered"]
                if q_rec == q_ord and q_ord > 0:
                    conf += 1
                elif q_rec < q_ord:
                    part += 1
                elif q_rec > q_ord:
                    sur += 1
            kpi_total_lbl.configure(text=f"Total Articles : {tot}")
            kpi_conf_lbl.configure(text=f"✅ Conformes : {conf}")
            kpi_part_lbl.configure(text=f"⏳ Partiels : {part}")
            kpi_sur_lbl.configure(text=f"⚠️ Surnuméraires : {sur}")

        def render_reception_table():
            rows = []
            for item in reception_data:
                def make_barcode_cell(parent, it=item):
                    f = ctk.CTkFrame(parent, fg_color="transparent")
                    if it.get("barcode"):
                        lbl = ctk.CTkLabel(f, text=it["barcode"], font=FONTS["mono"])
                        lbl.pack(side="left", padx=4)
                        it["widgets"]["bc_lbl"] = lbl
                    else:
                        e = ctk.CTkEntry(f, placeholder_text="Code-barres...", width=110, height=28, font=FONTS["caption"])
                        def on_bc_change(event, target=it, entry=e):
                            target["barcode"] = entry.get().strip()
                        e.bind("<KeyRelease>", on_bc_change)
                        e.pack(side="left", padx=2)
                        it["widgets"]["bc_entry"] = e
                    return f

                def make_name_cell(parent, it=item):
                    f = ctk.CTkFrame(parent, fg_color="transparent")
                    name_text = it["name"]
                    if it.get("is_new_product"):
                        lbl = ctk.CTkLabel(f, text=f"✨ {name_text[:24]}", font=FONTS["body_bold"], text_color=COLORS["primary"], anchor="w")
                    else:
                        lbl = ctk.CTkLabel(f, text=name_text[:28], font=FONTS["body"], anchor="w")
                    lbl.pack(side="left", fill="x", expand=True, padx=4)
                    return f

                def make_cat_cell(parent, it=item):
                    f = ctk.CTkFrame(parent, fg_color="transparent")
                    cb = ctk.CTkComboBox(f, values=all_cats, width=125, height=28, font=FONTS["caption"])
                    cur_cat = it.get("category") or "Soins Visage"
                    if cur_cat not in all_cats:
                        cb.configure(values=[cur_cat] + all_cats)
                    cb.set(cur_cat)
                    def on_cat_change(choice, target=it):
                        target["category"] = choice
                    cb.configure(command=lambda c, t=it: on_cat_change(c, t))
                    cb.pack(padx=2)
                    it["widgets"]["cat_cb"] = cb
                    return f

                def make_qty_cde_cell(parent, it=item):
                    f = ctk.CTkFrame(parent, fg_color="transparent")
                    lbl = ctk.CTkLabel(f, text=f"{it['qty_ordered']} u.", font=FONTS["body"])
                    lbl.pack()
                    return f

                def make_qty_cell(parent, it=item):
                    f = ctk.CTkFrame(parent, fg_color="transparent")
                    e = ctk.CTkEntry(f, width=65, height=28, font=FONTS["body_bold"], justify="center")
                    e.insert(0, str(it["qty_received"]))
                    def on_qty_change(event, target=it, entry=e):
                        try:
                            val = int(entry.get() or 0)
                            target["qty_received"] = max(0, val)
                            update_kpis()
                            refresh_compliance_labels()
                        except ValueError:
                            pass
                    e.bind("<KeyRelease>", on_qty_change)
                    e.pack(padx=2)
                    it["widgets"]["qty_entry"] = e
                    return f

                def make_price_cell(parent, it=item):
                    f = ctk.CTkFrame(parent, fg_color="transparent")
                    e = ctk.CTkEntry(f, width=75, height=28, font=FONTS["mono"], justify="center")
                    e.insert(0, str(int(it["unit_cost"])))
                    def on_price_change(event, target=it, entry=e):
                        try:
                            val = float(entry.get() or 0)
                            target["unit_cost"] = val
                            target["purchase_price"] = val
                        except ValueError:
                            pass
                    e.bind("<KeyRelease>", on_price_change)
                    e.pack(padx=2)
                    it["widgets"]["price_entry"] = e
                    return f

                def make_sale_price_cell(parent, it=item):
                    f = ctk.CTkFrame(parent, fg_color="transparent")
                    e = ctk.CTkEntry(f, width=75, height=28, font=FONTS["mono"], justify="center",
                                     border_color=COLORS["primary"], border_width=1)
                    e.insert(0, str(int(it.get("sale_price", 0))))
                    def on_sale_change(event, target=it, entry=e):
                        try:
                            val = float(entry.get() or 0)
                            target["sale_price"] = val
                        except ValueError:
                            pass
                    e.bind("<KeyRelease>", on_sale_change)
                    e.pack(padx=2)
                    it["widgets"]["sale_price_entry"] = e
                    return f

                def make_conf_cell(parent, it=item):
                    f = ctk.CTkFrame(parent, fg_color="transparent")
                    lbl = ctk.CTkLabel(f, text="", font=FONTS["caption_bold"])
                    lbl.pack(padx=2)
                    it["widgets"]["conf_lbl"] = lbl
                    update_single_compliance_lbl(it)
                    return f

                def make_chk_cell(parent, it=item):
                    f = ctk.CTkFrame(parent, fg_color="transparent")
                    var = ctk.BooleanVar(value=it.get("update_catalog_price", False))
                    chk = ctk.CTkCheckBox(f, text="MAJ", variable=var, width=45, height=20,
                                          font=FONTS["caption"],
                                          command=lambda target=it, v=var: target.__setitem__("update_catalog_price", v.get()))
                    chk.pack(padx=2)
                    it["widgets"]["price_chk"] = var
                    return f

                rows.append([
                    make_barcode_cell,
                    make_name_cell,
                    make_cat_cell,
                    make_qty_cde_cell,
                    make_qty_cell,
                    make_price_cell,
                    make_sale_price_cell,
                    make_conf_cell,
                    make_chk_cell
                ])

            rec_table.set_data(rows)
            update_kpis()

        def update_single_compliance_lbl(it):
            lbl = it["widgets"].get("conf_lbl")
            if not lbl:
                return
            q_rec = it["qty_received"]
            q_ord = it["qty_ordered"]
            if q_ord == 0:
                lbl.configure(text="ℹ️ Hors Commande", text_color=COLORS["info"])
            elif q_rec == q_ord:
                lbl.configure(text="✅ Conforme", text_color=COLORS["emerald"])
            elif q_rec < q_ord:
                lbl.configure(text=f"⏳ Reliquat ({q_ord - q_rec})", text_color="#F97316")
            else:
                lbl.configure(text=f"⚠️ Surnuméraire (+{q_rec - q_ord})", text_color=COLORS["info"])

        def refresh_compliance_labels():
            for it in reception_data:
                update_single_compliance_lbl(it)

        def on_barcode_scan(event=None):
            bc = bc_entry.get().strip()
            if not bc:
                return

            bc_entry.delete(0, "end")
            bc_entry.focus_set()

            matched_item = None
            for itm in reception_data:
                if itm["barcode"] == bc:
                    matched_item = itm
                    break

            if matched_item:
                matched_item["qty_received"] += 1
                if "qty_entry" in matched_item["widgets"]:
                    matched_item["widgets"]["qty_entry"].delete(0, "end")
                    matched_item["widgets"]["qty_entry"].insert(0, str(matched_item["qty_received"]))
                update_kpis()
                refresh_compliance_labels()
                ToastNotification.show(modal, f"✅ Scanné (+1) : {matched_item['name'][:25]}", "success")
                return

            existing_prod = StockService.get_product_by_barcode(bc)
            if existing_prod:
                p_dict = dict(existing_prod)
                new_line = {
                    "item_id": None,
                    "product_id": p_dict["id"],
                    "name": p_dict["name"],
                    "barcode": p_dict["barcode"],
                    "category": p_dict["category"],
                    "unit_cost": float(p_dict["purchase_price"]),
                    "sale_price": float(p_dict.get("sale_price") or p_dict["purchase_price"] * 1.4),
                    "current_catalog_price": float(p_dict["purchase_price"]),
                    "qty_ordered": 0,
                    "qty_received": 1,
                    "is_new_product": False,
                    "update_catalog_price": False,
                    "widgets": {}
                }
                reception_data.append(new_line)
                render_reception_table()
                ToastNotification.show(modal, f"✅ Produit reconnu du catalogue (+1) : {p_dict['name'][:25]}", "success")
            else:
                self._open_new_scanned_product_form(
                    parent_modal=modal,
                    scanned_barcode=bc,
                    supplier_id=order["supplier_id"],
                    on_validated_callback=lambda np: on_new_product_added(np)
                )

        def on_new_product_added(new_prod_data):
            reception_data.append({
                "item_id": None,
                "product_id": None,
                "name": new_prod_data["name"],
                "brand": new_prod_data.get("brand", ""),
                "barcode": new_prod_data["barcode"],
                "category": new_prod_data["category"],
                "unit_cost": float(new_prod_data["purchase_price"]),
                "sale_price": float(new_prod_data["sale_price"]),
                "vat_rate": float(new_prod_data.get("vat_rate", 0)),
                "min_alert": int(new_prod_data.get("min_alert", 5)),
                "expiry_date": new_prod_data.get("expiry_date"),
                "current_catalog_price": float(new_prod_data["purchase_price"]),
                "qty_ordered": 0,
                "qty_received": int(new_prod_data.get("qty_received", 1)),
                "is_new_product": True,
                "update_catalog_price": False,
                "widgets": {}
            })
            render_reception_table()
            ToastNotification.show(modal, f"✨ Nouveau produit ajouté à la réception : {new_prod_data['name'][:25]}", "success")

        bc_entry.bind("<Return>", on_barcode_scan)
        ctk.CTkButton(s_inner, text="➕ Ajouter", width=90, height=38,
                      font=FONTS["caption_bold"], fg_color=COLORS["primary"],
                      command=on_barcode_scan).pack(side="right")

        render_reception_table()

    def _open_new_scanned_product_form(self, parent_modal, scanned_barcode, supplier_id, on_validated_callback):
        sub_modal = BaseModal(parent_modal, "✨ Détection Nouveau Produit — Fiche Article", width=620, height=580)

        ctk.CTkLabel(sub_modal.body, text=f"Le code-barres {scanned_barcode} n'existe pas dans le catalogue.\nComplétez les informations pour créer la fiche produit :",
                     font=FONTS["body"], text_color=COLORS["info"], wraplength=560).pack(anchor="w", pady=(0, 10))

        f_grid = ctk.CTkFrame(sub_modal.body, fg_color="transparent")
        f_grid.pack(fill="both", expand=True)
        f_grid.grid_columnconfigure((0, 1), weight=1)

        all_cats = StockService.get_all_categories()

        # Code-barres
        ctk.CTkLabel(f_grid, text="Code-barres *", font=FONTS["caption_bold"]).grid(row=0, column=0, sticky="w", pady=(0, 2))
        bc_e = ctk.CTkEntry(f_grid, height=34, font=FONTS["body"])
        bc_e.insert(0, scanned_barcode)
        bc_e.grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=(0, 8))

        # Catégorie
        ctk.CTkLabel(f_grid, text="Catégorie * (Choisir ou Saisir)", font=FONTS["caption_bold"]).grid(row=0, column=1, sticky="w", pady=(0, 2))
        cat_e = ctk.CTkComboBox(f_grid, values=all_cats, height=34, font=FONTS["body"])
        cat_e.set("Soins Visage")
        cat_e.grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=(0, 8))


        # Nom
        ctk.CTkLabel(f_grid, text="Désignation du Produit *", font=FONTS["caption_bold"]).grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 2))
        name_e = ctk.CTkEntry(f_grid, placeholder_text="Ex: Sérum Hydratant 30ml", height=34, font=FONTS["body"])
        name_e.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        name_e.focus_set()

        # Marque
        ctk.CTkLabel(f_grid, text="Marque / Fabricant", font=FONTS["caption_bold"]).grid(row=4, column=0, sticky="w", pady=(0, 2))
        brand_e = ctk.CTkEntry(f_grid, placeholder_text="Ex: L'Oréal, Nivea...", height=34, font=FONTS["body"])
        brand_e.grid(row=5, column=0, sticky="ew", padx=(0, 5), pady=(0, 8))

        # Date Péremption
        ctk.CTkLabel(f_grid, text="Date Péremption (AAAA-MM-JJ)", font=FONTS["caption_bold"]).grid(row=4, column=1, sticky="w", pady=(0, 2))
        exp_e = ctk.CTkEntry(f_grid, placeholder_text="Ex: 2027-12-31", height=34, font=FONTS["body"])
        exp_e.grid(row=5, column=1, sticky="ew", padx=(5, 0), pady=(0, 8))

        # Prix Achat & Prix Vente
        ctk.CTkLabel(f_grid, text="Prix d'Achat (DA) *", font=FONTS["caption_bold"]).grid(row=6, column=0, sticky="w", pady=(0, 2))
        ctk.CTkLabel(f_grid, text="Prix de Vente TTC (DA) *", font=FONTS["caption_bold"]).grid(row=6, column=1, sticky="w", pady=(0, 2))

        pa_e = ctk.CTkEntry(f_grid, height=34, font=FONTS["body"])
        pa_e.insert(0, "1000")
        pa_e.grid(row=7, column=0, sticky="ew", padx=(0, 5), pady=(0, 8))

        pv_e = ctk.CTkEntry(f_grid, height=34, font=FONTS["body"])
        pv_e.insert(0, "1500")
        pv_e.grid(row=7, column=1, sticky="ew", padx=(5, 0), pady=(0, 8))

        # Quantité reçue & Seuil Alerte
        ctk.CTkLabel(f_grid, text="Quantité Reçue *", font=FONTS["caption_bold"]).grid(row=8, column=0, sticky="w", pady=(0, 2))
        ctk.CTkLabel(f_grid, text="Seuil Alerte Stock", font=FONTS["caption_bold"]).grid(row=8, column=1, sticky="w", pady=(0, 2))

        qr_e = ctk.CTkEntry(f_grid, height=34, font=FONTS["body"])
        qr_e.insert(0, "1")
        qr_e.grid(row=9, column=0, sticky="ew", padx=(0, 5), pady=(0, 10))

        al_e = ctk.CTkEntry(f_grid, height=34, font=FONTS["body"])
        al_e.insert(0, "5")
        al_e.grid(row=9, column=1, sticky="ew", padx=(5, 0), pady=(0, 10))

        def confirm_new_prod():
            name = name_e.get().strip()
            bc = bc_e.get().strip()
            if not name or not bc:
                ToastNotification.show(sub_modal, "Nom et code-barres sont obligatoires.", "warning")
                return
            try:
                pa = float(pa_e.get() or 0)
                pv = float(pv_e.get() or 0)
                qr = int(qr_e.get() or 1)
                al = int(al_e.get() or 5)

                prod_payload = {
                    "name": name,
                    "brand": brand_e.get().strip(),
                    "barcode": bc,
                    "category": cat_e.get(),
                    "purchase_price": pa,
                    "sale_price": pv,
                    "vat_rate": 0.0,
                    "min_alert": al,
                    "expiry_date": exp_e.get().strip() or None,
                    "qty_received": qr
                }
                sub_modal.destroy()
                on_validated_callback(prod_payload)
            except ValueError:
                ToastNotification.show(sub_modal, "Veuillez saisir des nombres valides.", "danger")

        ctk.CTkButton(sub_modal.body, text="✨ CRÉER LA FICHE PRODUIT ET AJOUTER", height=42,
                      font=FONTS["body_bold"], fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      command=confirm_new_prod).pack(fill="x", side="bottom")

    # ══════════════════════════════════════════════════════════════════════════
    # ÉTAPE 4 : TRAÇABILITÉ & AUDIT PAR BON DE COMMANDE
    # ══════════════════════════════════════════════════════════════════════════
    def _setup_traceability_tab(self):
        self.tab_traceability.grid_columnconfigure(0, weight=1)
        self.tab_traceability.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(self.tab_traceability, fg_color="transparent", height=45)
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        ctk.CTkLabel(top, text="Catalogue de produits ajoutés via des Bons de Commande",
                     font=FONTS["title_small"]).pack(side="left")

        ctk.CTkButton(top, text="🔄 Actualiser", width=100, height=32,
                      font=FONTS["caption_bold"], command=self.load_traceability).pack(side="right")

        cols = [
            ("N° Bon Commande", 3, "w"),
            ("Fournisseur", 3, "w"),
            ("Code-barres", 2, "w"),
            ("Désignation Produit Créé", 4, "w"),
            ("Catégorie", 3, "w"),
            ("Stock Actuel", 2, "center"),
            ("Date Création", 2, "w")
        ]
        self.trace_table = ModernTable(self.tab_traceability, cols)
        self.trace_table.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.load_traceability()

    def load_traceability(self):
        prods = SupplierService.get_products_created_by_pos()
        rows = []
        for p in prods:
            p_dict = dict(p)
            rows.append([
                p_dict.get("order_code") or "-",
                p_dict.get("supplier_name") or "-",
                p_dict.get("barcode") or "-",
                p_dict.get("name") or "-",
                p_dict.get("category") or "-",
                f"{p_dict.get('stock_qty', 0)} u.",
                p_dict.get("po_created_at", "")[:16] if p_dict.get("po_created_at") else "-"
            ])
        self.trace_table.set_data(rows)

    def _open_po_traceability_modal(self, order):
        """Ouvre un modal d'audit détaillé pour un bon de commande spécifique."""
        order = dict(order)
        data = SupplierService.get_po_traceability(order["id"])
        if not data:
            ToastNotification.show(self, "Données de traçabilité introuvables", "warning")
            return

        modal = BaseModal(self.winfo_toplevel(), f"🔍 Journal d'Audit & Traçabilité — {order['order_code']}", width=880, height=680)

        mtab = ctk.CTkTabview(modal.body, fg_color="transparent")
        mtab.pack(fill="both", expand=True)

        t_items = mtab.add("📦 Articles & Écarts")
        t_new = mtab.add(f"✨ Nouveaux Produits ({len(data['new_products'])})")
        t_movs = mtab.add(f"📜 Mouvements de Stock ({len(data['movements'])})")

        cols_i = [
            ("Code-barres", 2, "w"),
            ("Désignation", 4, "w"),
            ("Qté Cde", 2, "center"),
            ("Qté Reçue", 2, "center"),
            ("Écart", 2, "center"),
            ("P.U. Achat", 2, "e"),
            ("État", 2, "center")
        ]
        table_i = ModernTable(t_items, cols_i)
        table_i.pack(fill="both", expand=True, padx=5, pady=5)
        rows_i = []
        for item in data["items"]:
            q_ord = item["qty_ordered"]
            q_rec = item["qty_received"] or 0
            diff = q_rec - q_ord
            diff_str = f"+{diff}" if diff > 0 else (str(diff) if diff < 0 else "0")
            st_str = "Conforme" if q_rec >= q_ord else "Partiel"
            rows_i.append([
                item["barcode"] or "-", item["product_name"][:32],
                f"{q_ord}", f"{q_rec}", diff_str,
                f"{item['unit_cost']:,.0f} DA", st_str
            ])
        table_i.set_data(rows_i)

        cols_n = [
            ("Code-barres", 2, "w"),
            ("Désignation", 4, "w"),
            ("Catégorie", 3, "w"),
            ("Prix Achat", 2, "e"),
            ("Prix Vente", 2, "e"),
            ("Stock Actuel", 2, "center")
        ]
        table_n = ModernTable(t_new, cols_n)
        table_n.pack(fill="both", expand=True, padx=5, pady=5)
        rows_n = []
        for p in data["new_products"]:
            rows_n.append([
                p["barcode"], p["name"], p["category"],
                f"{p['purchase_price']:,.0f} DA",
                f"{p['sale_price']:,.0f} DA",
                f"{p['stock_qty']} u."
            ])
        table_n.set_data(rows_n)

        cols_m = [
            ("Date & Heure", 2, "w"),
            ("Produit", 4, "w"),
            ("Quantité", 2, "center"),
            ("Stock Après", 2, "center"),
            ("Opérateur", 2, "w")
        ]
        table_m = ModernTable(t_movs, cols_m)
        table_m.pack(fill="both", expand=True, padx=5, pady=5)
        rows_m = []
        for m in data["movements"]:
            rows_m.append([
                m["created_at"], m["product_name"][:30],
                f"+{m['qty']}", f"{m['new_stock']} u.",
                m["operator_name"] or "Système"
            ])
        table_m.set_data(rows_m)
