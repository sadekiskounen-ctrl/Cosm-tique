import customtkinter as ctk
from PIL import ImageTk
from ui.theme import FONTS, COLORS
from config import CATEGORIES
from services.stock_service import StockService
from services.supplier_service import SupplierService
from services.barcode_service import BarcodeService
from ui.components.modern_table import ModernTable
from ui.components.modal import BaseModal
from ui.components.notification import ToastNotification


class ProductsView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ── Top Action Bar ───────────────────────────────────────────────────
        self.top_bar = ctk.CTkFrame(self, fg_color=("white", "#1E293B"), corner_radius=12, height=60)
        self.top_bar.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        self.top_bar.pack_propagate(False)

        self.search_entry = ctk.CTkEntry(
            self.top_bar,
            placeholder_text="\U0001f50d Rechercher par nom, code-barre, marque...",
            width=280, height=36, font=FONTS["body"]
        )
        self.search_entry.pack(side="left", padx=15, pady=12)
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_products())

        self.cat_filter = ctk.CTkOptionMenu(
            self.top_bar,
            values=["Toutes les cat\u00e9gories"] + CATEGORIES,
            width=200, height=36, font=FONTS["body"],
            command=lambda c: self.load_products()
        )
        self.cat_filter.pack(side="left", padx=5)

        self.add_btn = ctk.CTkButton(
            self.top_bar,
            text="+ Nouveau Produit",
            height=36, font=FONTS["body_bold"],
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            command=self.open_add_product_modal
        )
        self.add_btn.pack(side="right", padx=15)

        # ── Products Table (photo 2: colonnes bien alignées) ──────────────────
        # Photo 2 fix: utilise "e" pour prix/stock pour un alignement numérique cohérent
        self.columns = [
            ("Code-barres",  2, "w"),
            ("D\u00e9signation",    4, "w"),
            ("Marque",       2, "w"),
            ("Cat\u00e9gorie",      3, "w"),
            ("P. Achat",     2, "e"),
            ("P. Vente",     2, "e"),
            ("Stock",        1, "center"),
            ("P\u00e9remption",    2, "center"),
            ("Actions",      2, "center")
        ]
        self.table = ModernTable(self, self.columns)
        self.table.grid(row=2, column=0, sticky="nsew", padx=15, pady=(0, 15))

        self.load_products()

    def load_products(self):
        search = self.search_entry.get().strip()
        cat = self.cat_filter.get()
        category_param = None if cat == "Toutes les cat\u00e9gories" else cat

        products = StockService.get_products(search=search, category=category_param or "Toutes", active_only=True)

        table_rows = []
        for p in products:
            p_dict = dict(p)

            def make_actions_cell(parent_frame, prod=p_dict):
                action_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
                btn_edit = ctk.CTkButton(
                    action_frame, text="\u270f\ufe0f", width=28, height=24,
                    fg_color=("gray90", "#334155"), text_color=("gray10", "gray90"),
                    hover_color=COLORS["primary"],
                    command=lambda: self.open_edit_product_modal(prod)
                )
                btn_edit.pack(side="left", padx=2)
                btn_label = ctk.CTkButton(
                    action_frame, text="\U0001f3f7\ufe0f", width=28, height=24,
                    fg_color=("gray90", "#334155"), text_color=("gray10", "gray90"),
                    hover_color=COLORS["info"],
                    command=lambda: self.open_print_barcode_modal(prod)
                )
                btn_label.pack(side="left", padx=2)
                return action_frame

            table_rows.append([
                p["barcode"],
                p["name"][:35],
                p["brand"] or "-",
                p["category"],
                f"{p['purchase_price']:,.0f} DA",
                f"{p['sale_price']:,.0f} DA",
                f"{p['stock_qty']} u.",
                p["expiry_date"] or "-",
                make_actions_cell
            ])

        self.table.set_data(table_rows)

    # ── Ajouter un produit ────────────────────────────────────────────────────
    # ── Ajouter un produit ────────────────────────────────────────────────────
    def open_add_product_modal(self):
        modal = BaseModal(self.winfo_toplevel(), "Ajouter un Nouveau Produit Cosmétique", width=620, height=590)

        scroll = ctk.CTkScrollableFrame(modal.body, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(scroll, text="Code-barres (EAN-13 / Code128) *", font=FONTS["caption_bold"]).pack(anchor="w", pady=(0, 2))
        bc_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        bc_frame.pack(fill="x", pady=(0, 10))

        bc_entry = ctk.CTkEntry(bc_frame, height=36, font=FONTS["body"])
        bc_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        def generate_bc():
            new_code = BarcodeService.generate_random_ean13()
            bc_entry.delete(0, "end")
            bc_entry.insert(0, new_code)

        ctk.CTkButton(bc_frame, text="⚡ Générer EAN-13", font=FONTS["caption_bold"],
                      width=130, height=36, command=generate_bc).pack(side="right")

        ctk.CTkLabel(scroll, text="Désignation du Produit *", font=FONTS["caption_bold"]).pack(anchor="w", pady=(0, 2))
        name_entry = ctk.CTkEntry(scroll, height=36, font=FONTS["body"], placeholder_text="ex: Crème de Jour Éclat 50ml")
        name_entry.pack(fill="x", pady=(0, 10))

        grid1 = ctk.CTkFrame(scroll, fg_color="transparent")
        grid1.pack(fill="x", pady=(0, 10))
        grid1.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkLabel(grid1, text="Marque", font=FONTS["caption_bold"]).grid(row=0, column=0, sticky="w", padx=(0, 5))
        ctk.CTkLabel(grid1, text="Catégorie *", font=FONTS["caption_bold"]).grid(row=0, column=1, sticky="w", padx=(5, 0))
        brand_entry = ctk.CTkEntry(grid1, height=36, font=FONTS["body"], placeholder_text="ex: L'Oréal, Nivea...")
        brand_entry.grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=(2, 0))
        
        all_cats = StockService.get_all_categories()
        cat_menu = ctk.CTkComboBox(grid1, values=all_cats, height=36, font=FONTS["body"])
        cat_menu.set(all_cats[0] if all_cats else "Soins Visage")
        cat_menu.grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=(2, 0))

        grid2 = ctk.CTkFrame(scroll, fg_color="transparent")
        grid2.pack(fill="x", pady=(0, 10))
        grid2.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkLabel(grid2, text="Prix d'Achat (DA) *", font=FONTS["caption_bold"]).grid(row=0, column=0, sticky="w", padx=(0, 5))
        ctk.CTkLabel(grid2, text="Prix de Vente (DA) *", font=FONTS["caption_bold"]).grid(row=0, column=1, sticky="w", padx=(5, 0))
        pa_entry = ctk.CTkEntry(grid2, height=36, font=FONTS["body"])
        pa_entry.grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=(2, 0))
        pa_entry.insert(0, "1000")
        pv_entry = ctk.CTkEntry(grid2, height=36, font=FONTS["body"])
        pv_entry.grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=(2, 0))
        pv_entry.insert(0, "1500")

        grid3 = ctk.CTkFrame(scroll, fg_color="transparent")
        grid3.pack(fill="x", pady=(0, 10))
        grid3.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkLabel(grid3, text="Stock Initial (Unités)", font=FONTS["caption_bold"]).grid(row=0, column=0, sticky="w", padx=(0, 5))
        ctk.CTkLabel(grid3, text="Seuil d'Alerte Minimum", font=FONTS["caption_bold"]).grid(row=0, column=1, sticky="w", padx=(5, 0))
        stock_entry = ctk.CTkEntry(grid3, height=36, font=FONTS["body"])
        stock_entry.grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=(2, 0))
        stock_entry.insert(0, "10")
        alert_entry = ctk.CTkEntry(grid3, height=36, font=FONTS["body"])
        alert_entry.grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=(2, 0))
        alert_entry.insert(0, "5")

        grid4 = ctk.CTkFrame(scroll, fg_color="transparent")
        grid4.pack(fill="x", pady=(0, 15))
        grid4.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkLabel(grid4, text="Date Péremption (AAAA-MM-JJ)", font=FONTS["caption_bold"]).grid(row=0, column=0, sticky="w", padx=(0, 5))
        ctk.CTkLabel(grid4, text="Fournisseur", font=FONTS["caption_bold"]).grid(row=0, column=1, sticky="w", padx=(5, 0))
        expiry_entry = ctk.CTkEntry(grid4, height=36, font=FONTS["body"], placeholder_text="2027-12-31")
        expiry_entry.grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=(2, 0))
        suppliers = SupplierService.get_suppliers()
        sup_names = ["Aucun"] + [s["name"] for s in suppliers]
        sup_menu = ctk.CTkOptionMenu(grid4, values=sup_names, height=36, font=FONTS["body"])
        sup_menu.grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=(2, 0))

        def save():
            bc = bc_entry.get().strip()
            name = name_entry.get().strip()
            if not bc or not name:
                ToastNotification.show(modal, "Veuillez remplir le code-barre et la désignation", "warning")
                return
            try:
                pa = float(pa_entry.get() or 0)
                pv = float(pv_entry.get() or 0)
                stock = int(stock_entry.get() or 0)
                alert = int(alert_entry.get() or 5)
            except ValueError:
                ToastNotification.show(modal, "Prix ou stock invalides", "danger")
                return
            sel_sup = sup_menu.get()
            sup_id = next((s["id"] for s in suppliers if s["name"] == sel_sup), None) if sel_sup != "Aucun" else None
            success, msg = StockService.add_product(
                barcode=bc, name=name, brand=brand_entry.get().strip(), category=cat_menu.get().strip(),
                purchase_price=pa, sale_price=pv, vat_rate=0.0, initial_stock=stock,
                min_alert=alert, expiry_date=expiry_entry.get().strip() or None, supplier_id=sup_id
            )
            if success:
                modal.destroy()
                ToastNotification.show(self, msg, "success")
                self.load_products()
            else:
                ToastNotification.show(modal, msg, "danger")

        ctk.CTkButton(modal.body, text="ENREGISTRER LE PRODUIT", height=42,
                      font=FONTS["body_bold"], fg_color=COLORS["primary"],
                      hover_color=COLORS["primary_hover"], command=save).pack(fill="x", side="bottom")

    # ── Modifier un produit ────────────────────────────────────────────────────
    def open_edit_product_modal(self, product):
        modal = BaseModal(self.winfo_toplevel(), f"Modifier : {product['name']}", width=640, height=600)
        scroll = ctk.CTkScrollableFrame(modal.body, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(scroll, text="Code-barres", font=FONTS["caption_bold"]).pack(anchor="w", pady=(0, 2))
        bc_entry = ctk.CTkEntry(scroll, height=36, font=FONTS["body"])
        bc_entry.pack(fill="x", pady=(0, 10))
        bc_entry.insert(0, product["barcode"])

        ctk.CTkLabel(scroll, text="Désignation", font=FONTS["caption_bold"]).pack(anchor="w", pady=(0, 2))
        name_entry = ctk.CTkEntry(scroll, height=36, font=FONTS["body"])
        name_entry.pack(fill="x", pady=(0, 10))
        name_entry.insert(0, product["name"])

        # ── Marque et Catégorie (modifiables) ──
        grid_cat = ctk.CTkFrame(scroll, fg_color="transparent")
        grid_cat.pack(fill="x", pady=(0, 10))
        grid_cat.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkLabel(grid_cat, text="Marque", font=FONTS["caption_bold"]).grid(row=0, column=0, sticky="w", padx=(0, 5))
        ctk.CTkLabel(grid_cat, text="Catégorie * (Choisir ou Saisir)", font=FONTS["caption_bold"]).grid(row=0, column=1, sticky="w", padx=(5, 0))
        
        brand_entry = ctk.CTkEntry(grid_cat, height=36, font=FONTS["body"])
        brand_entry.insert(0, product.get("brand") or "")
        brand_entry.grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=(2, 0))

        all_cats = StockService.get_all_categories()
        cat_cb = ctk.CTkComboBox(grid_cat, values=all_cats, height=36, font=FONTS["body"])
        curr_cat = product.get("category") or "Soins Visage"
        cat_cb.set(curr_cat)
        cat_cb.grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=(2, 0))

        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="x", pady=(0, 10))
        grid.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkLabel(grid, text="Prix d'Achat (DA)", font=FONTS["caption_bold"]).grid(row=0, column=0, sticky="w", padx=(0, 5))
        ctk.CTkLabel(grid, text="Prix de Vente (DA)", font=FONTS["caption_bold"]).grid(row=0, column=1, sticky="w", padx=(5, 0))
        pa_entry = ctk.CTkEntry(grid, height=36, font=FONTS["body"])
        pa_entry.grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=(2, 0))
        pa_entry.insert(0, str(product["purchase_price"]))
        pv_entry = ctk.CTkEntry(grid, height=36, font=FONTS["body"])
        pv_entry.grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=(2, 0))
        pv_entry.insert(0, str(product["sale_price"]))

        grid_extra = ctk.CTkFrame(scroll, fg_color="transparent")
        grid_extra.pack(fill="x", pady=(0, 10))
        grid_extra.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(grid_extra, text="Seuil Alerte Stock", font=FONTS["caption_bold"]).grid(row=0, column=0, sticky="w", padx=(0, 5))
        ctk.CTkLabel(grid_extra, text="Date Péremption (AAAA-MM-JJ)", font=FONTS["caption_bold"]).grid(row=0, column=1, sticky="w", padx=(5, 0))

        alert_entry = ctk.CTkEntry(grid_extra, height=36, font=FONTS["body"])
        alert_entry.insert(0, str(product["min_stock_alert"]))
        alert_entry.grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=(2, 0))

        expiry_entry = ctk.CTkEntry(grid_extra, height=36, font=FONTS["body"])
        expiry_entry.insert(0, product["expiry_date"] or "")
        expiry_entry.grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=(2, 0))

        # Fournisseur
        ctk.CTkLabel(scroll, text="Fournisseur Associé", font=FONTS["caption_bold"]).pack(anchor="w", pady=(5, 2))
        suppliers = SupplierService.get_suppliers()
        sup_dict = {s["name"]: s["id"] for s in suppliers}
        sup_names = ["(Aucun)"] + list(sup_dict.keys())
        current_sup_name = "(Aucun)"
        if product.get("supplier_id"):
            for s in suppliers:
                if s["id"] == product["supplier_id"]:
                    current_sup_name = s["name"]
                    break
        sup_menu = ctk.CTkOptionMenu(scroll, values=sup_names, height=36, font=FONTS["body"])
        sup_menu.set(current_sup_name)
        sup_menu.pack(fill="x", pady=(0, 15))

        def update():
            sel_sup = sup_menu.get()
            sup_id = sup_dict.get(sel_sup) if sel_sup != "(Aucun)" else None
            chosen_cat = cat_cb.get().strip() or "Soins Visage"
            success, msg = StockService.update_product(
                product_id=product["id"], barcode=bc_entry.get().strip(),
                name=name_entry.get().strip(), brand=brand_entry.get().strip(),
                category=chosen_cat, purchase_price=float(pa_entry.get() or 0),
                sale_price=float(pv_entry.get() or 0), vat_rate=0.0,
                min_alert=int(alert_entry.get() or 5), expiry_date=expiry_entry.get().strip() or None,
                supplier_id=sup_id
            )
            if success:
                modal.destroy()
                ToastNotification.show(self, msg, "success")
                self.load_products()
            else:
                ToastNotification.show(modal, msg, "danger")

        ctk.CTkButton(modal.body, text="METTRE À JOUR", height=42, font=FONTS["body_bold"],
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], command=update).pack(fill="x", side="bottom")


    # ── Photo 3 : Étiquette code-barres améliorée avec PDF ─────────────────
    def open_print_barcode_modal(self, product):
        modal = BaseModal(self.winfo_toplevel(),
                          f"\U0001f3f7\ufe0f \u00c9tiquette : {product['name'][:40]}", width=520, height=500)

        ctk.CTkLabel(modal.body, text="Aper\u00e7u de l'\u00e9tiquette produit :",
                     font=FONTS["caption_bold"]).pack(anchor="w", pady=(0, 8))

        # Aperçu image (avec code-barres visible et numéro)
        pil_img = BarcodeService.create_product_sticker(
            product["name"], product["sale_price"], product["barcode"]
        )
        # Redimensionner pour l'aperçu
        preview_w, preview_h = 440, 275
        pil_preview = pil_img.resize((preview_w, preview_h))
        ctk_img = ctk.CTkImage(light_image=pil_preview, dark_image=pil_preview, size=(preview_w, preview_h))

        preview_box = ctk.CTkLabel(modal.body, image=ctk_img, text="",
                                   fg_color=("gray95", "gray15"), corner_radius=8)
        preview_box.image = ctk_img
        preview_box.pack(pady=8, fill="x")
        preview_box.configure(height=preview_h)

        # Afficher le numéro sous l'aperçu
        ctk.CTkLabel(modal.body, text=f"Code-barres : {product['barcode']}",
                     font=FONTS["body_bold"], text_color=COLORS["info"]).pack(pady=(4, 0))

        # Boutons
        btn_frame = ctk.CTkFrame(modal.body, fg_color="transparent")
        btn_frame.pack(fill="x", side="bottom", pady=10)
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        def open_pdf():
            pdf_path, err = BarcodeService.save_sticker_to_pdf(
                product["name"], product["sale_price"], product["barcode"]
            )
            if pdf_path:
                opened = BarcodeService.open_pdf_viewer(pdf_path)
                if opened:
                    ToastNotification.show(modal, "PDF ouvert dans le lecteur syst\u00e8me !", "success")
                else:
                    ToastNotification.show(modal, f"PDF g\u00e9n\u00e9r\u00e9 : {pdf_path}", "success")
            else:
                ToastNotification.show(modal, f"Erreur : {err}", "danger")

        def save_image():
            saved_path = BarcodeService.save_sticker_to_file(
                product["name"], product["sale_price"], product["barcode"]
            )
            ToastNotification.show(modal, f"\u00c9tiquette enregistr\u00e9e : {saved_path}", "success")

        ctk.CTkButton(
            btn_frame, text="\U0001f5a8\ufe0f Imprimer / Ouvrir PDF",
            height=42, font=FONTS["body_bold"],
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            command=open_pdf
        ).grid(row=0, column=0, sticky="ew", padx=(0, 5))

        ctk.CTkButton(
            btn_frame, text="\U0001f4be Enregistrer Image",
            height=42, font=FONTS["body_bold"],
            fg_color=COLORS["emerald"], hover_color=COLORS["emerald_hover"],
            command=save_image
        ).grid(row=0, column=1, sticky="ew", padx=(5, 0))
