import customtkinter as ctk
from ui.theme import FONTS, COLORS
from services.pos_service import POSService
from services.stock_service import StockService
from services.printer_service import PrinterService
from services.auth_service import AuthService
from ui.components.notification import ToastNotification
from ui.components.modal import BaseModal
from config import CATEGORIES

class POSView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.pos_service = POSService()
        self.current_category = "Toutes"
        self.current_search = ""
        self._search_after_id = None  # debounce timer

        # Layout 2 Colonnes : Gauche (Catalogue & Scan rapide) | Droite (Panier & Caisse)
        self.grid_columnconfigure(0, weight=6)
        self.grid_columnconfigure(1, weight=4)
        self.grid_rowconfigure(0, weight=1)

        # ---------------- GAUCHE : CATALOGUE & RECHERCHE ----------------
        self.left_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        self.left_panel.grid_rowconfigure(2, weight=1)
        self.left_panel.grid_columnconfigure(0, weight=1)

        # 1. Barcode Scanner Fast-Entry Bar
        self.scan_bar = ctk.CTkFrame(
            self.left_panel,
            corner_radius=12,
            fg_color=("#FFFFFF", "#1E293B"),
            border_width=2,
            border_color=COLORS["primary"],
            height=60
        )
        self.scan_bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.scan_bar.grid_propagate(False)

        ctk.CTkLabel(
            self.scan_bar,
            text="🔍 SCANNER DOUCHETTE :",
            font=FONTS["body_bold"],
            text_color=COLORS["primary"]
        ).pack(side="left", padx=(12, 6))

        # Qté Saisie rapide clavier
        qty_box = ctk.CTkFrame(self.scan_bar, fg_color=("#F1F5F9", "#0F172A"), corner_radius=8, height=36)
        qty_box.pack(side="left", padx=(0, 6), pady=6)
        qty_box.pack_propagate(False)

        ctk.CTkLabel(qty_box, text="Qté :", font=FONTS["caption_bold"], text_color=COLORS["primary"]).pack(side="left", padx=(6, 2))
        self.scan_qty_entry = ctk.CTkEntry(
            qty_box,
            width=45,
            height=28,
            font=FONTS["body_bold"],
            justify="center",
            border_width=0,
            fg_color="transparent"
        )
        self.scan_qty_entry.insert(0, "1")
        self.scan_qty_entry.pack(side="left", padx=(0, 4))

        self.barcode_entry = ctk.CTkEntry(
            self.scan_bar,
            font=FONTS["title_small"],
            placeholder_text="Scannez ou tapez (ex: 5*code-barres, nom...)...",
            border_width=0,
            fg_color="transparent"
        )
        self.barcode_entry.pack(side="left", fill="both", expand=True, padx=5, pady=8)
        self.barcode_entry.bind("<Return>", self._on_barcode_scanned)
        self.barcode_entry.bind("<KeyRelease>", self._schedule_search)
        self.barcode_entry.focus_set()

        # 2. Categories Filter Bar
        self.cat_scroll = ctk.CTkScrollableFrame(
            self.left_panel,
            orientation="horizontal",
            height=48,
            fg_color="transparent"
        )
        self.cat_scroll.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        self.cat_buttons = {}
        all_cats = ["Toutes"] + CATEGORIES
        for cat in all_cats:
            btn = ctk.CTkButton(
                self.cat_scroll,
                text=cat,
                font=FONTS["caption_bold"],
                height=32,
                corner_radius=8,
                fg_color=COLORS["primary"] if cat == "Toutes" else ("#E2E8F0", "#334155"),
                text_color="#FFFFFF" if cat == "Toutes" else ("#0F172A", "#F8FAFC"),
                hover_color=COLORS["primary_hover"],
                command=lambda c=cat: self._filter_category(c)
            )
            btn.pack(side="left", padx=4)
            self.cat_buttons[cat] = btn

        # 3. Product Cards Grid (Scrollable)
        self.products_grid = ctk.CTkScrollableFrame(
            self.left_panel,
            corner_radius=12,
            fg_color=("#FFFFFF", "#1E293B"),
            border_width=1,
            border_color=("#E2E8F0", "#334155")
        )
        self.products_grid.grid(row=2, column=0, sticky="nsew")
        self.products_grid.grid_columnconfigure((0, 1, 2), weight=1)

        # ---------------- DROITE : PANIER & ENCAISSEMENT ----------------
        self.right_panel = ctk.CTkFrame(
            self,
            corner_radius=14,
            fg_color=("#FFFFFF", "#1E293B"),
            border_width=1,
            border_color=("#E2E8F0", "#334155")
        )
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        self.right_panel.grid_rowconfigure(1, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)

        # Cart Header
        cart_header = ctk.CTkFrame(self.right_panel, fg_color="transparent", height=45)
        cart_header.grid(row=0, column=0, sticky="ew", padx=15, pady=(12, 6))
        
        ctk.CTkLabel(cart_header, text="🛒 Panier Actuel", font=FONTS["title_small"], text_color=("#0F172A", "#F8FAFC")).pack(side="left")
        
        self.clear_btn = ctk.CTkButton(
            cart_header,
            text="Vider",
            width=65,
            height=26,
            font=FONTS["caption_bold"],
            fg_color=("#F1F5F9", "#334155"),
            text_color=COLORS["danger"],
            hover_color=("#E2E8F0", "#475569"),
            command=self._clear_cart
        )
        self.clear_btn.pack(side="right")

        # Cart Items Scrollable List
        self.cart_scroll = ctk.CTkScrollableFrame(self.right_panel, fg_color="transparent")
        self.cart_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.cart_scroll.grid_columnconfigure(0, weight=1)

        # Cart Summary & Checkout Footer
        self.summary_frame = ctk.CTkFrame(
            self.right_panel,
            corner_radius=12,
            fg_color=("#F8FAFC", "#0F172A"),
            border_width=1,
            border_color=("#E2E8F0", "#334155")
        )
        self.summary_frame.grid(row=2, column=0, sticky="ew", padx=12, pady=12)

        # Totals Display
        self.subtotal_lbl = ctk.CTkLabel(self.summary_frame, text="Total Brut : 0.00 DA", font=FONTS["caption"], text_color=("#64748B", "#94A3B8"))
        self.subtotal_lbl.pack(anchor="w", padx=15, pady=(8, 2))

        self.discount_lbl = ctk.CTkLabel(self.summary_frame, text="Remises : 0.00 DA", font=FONTS["caption"], text_color=COLORS["emerald"])
        self.discount_lbl.pack(anchor="w", padx=15, pady=2)

        self.final_total_lbl = ctk.CTkLabel(self.summary_frame, text="TOTAL : 0.00 DA", font=FONTS["title_large"], text_color=COLORS["primary"])
        self.final_total_lbl.pack(anchor="w", padx=15, pady=(4, 10))

        # Checkout Big Action Button
        self.checkout_btn = ctk.CTkButton(
            self.summary_frame,
            text="⚡ ENCAISSER (F9)",
            height=48,
            font=FONTS["title_small"],
            fg_color=COLORS["emerald"],
            hover_color=COLORS["emerald_hover"],
            command=self._open_checkout_modal
        )
        self.checkout_btn.pack(fill="x", padx=12, pady=(0, 12))

        # Initial Load
        self._load_products()
        self._refresh_cart_ui()

    def _on_barcode_scanned(self, event=None):
        query = self.barcode_entry.get().strip()
        if not query:
            return

        # Support format "5*barcode" or just barcode
        qty_to_add = 1
        barcode_part = query
        if "*" in query:
            parts = query.split("*", 1)
            try:
                qty_to_add = int(parts[0].strip())
                barcode_part = parts[1].strip()
            except (ValueError, IndexError):
                pass
        else:
            # Read from qty entry field
            try:
                qty_to_add = max(1, int(self.scan_qty_entry.get() or 1))
            except (ValueError, AttributeError):
                qty_to_add = 1

        # 1. Tester si c'est un code-barre exact
        product = StockService.get_product_by_barcode(barcode_part)
        if product:
            success, msg = self.pos_service.add_product(dict(product), qty=qty_to_add)
            if success:
                qty_txt = f" x{qty_to_add}" if qty_to_add > 1 else ""
                ToastNotification.show(self, f"✅ Ajouté{qty_txt} : {product['name'][:28]}", "success", duration_ms=1500)
                self.barcode_entry.delete(0, "end")
                # Reset qty to 1 after scan
                self.scan_qty_entry.delete(0, "end")
                self.scan_qty_entry.insert(0, "1")
                self._refresh_cart_ui()
            else:
                ToastNotification.show(self, msg, "warning")
            return

        # 2. Sinon, filtrer les produits affichés par cette recherche
        self.current_search = query
        self._load_products()
        self.barcode_entry.delete(0, "end")


    def _filter_category(self, cat):
        self.current_category = cat
        for c, btn in self.cat_buttons.items():
            if c == cat:
                btn.configure(fg_color=COLORS["primary"], text_color="#FFFFFF")
            else:
                btn.configure(fg_color=("#E2E8F0", "#334155"), text_color=("#0F172A", "#F8FAFC"))
        self._load_products()

    def _schedule_search(self, event=None):
        """Debounce: wait 280ms after last keystroke before loading products."""
        if self._search_after_id:
            try:
                self.after_cancel(self._search_after_id)
            except Exception:
                pass
        self.current_search = self.barcode_entry.get().strip()
        self._search_after_id = self.after(280, self._load_products)

    def _load_products(self):
        for widget in self.products_grid.winfo_children():
            widget.destroy()

        products = StockService.get_products(
            search=self.current_search,
            category=self.current_category,
            active_only=True
        )

        if not products:
            lbl = ctk.CTkLabel(
                self.products_grid,
                text="Aucun produit cosmétique trouvé.",
                font=FONTS["body"],
                text_color=("#94A3B8", "#64748B")
            )
            lbl.grid(row=0, column=0, columnspan=3, pady=40)
            return

        cols = 3
        for idx, p in enumerate(products):
            r = idx // cols
            c = idx % cols
            card = self._create_product_card(dict(p))
            card.grid(row=r, column=c, padx=6, pady=6, sticky="nsew")

    def _create_product_card(self, product):
        is_out = product["stock_qty"] <= 0
        card = ctk.CTkFrame(
            self.products_grid,
            corner_radius=10,
            fg_color=("#F8FAFC", "#0F172A") if not is_out else ("#FEF2F2", "#2A1515"),
            border_width=1,
            border_color=("#E2E8F0", "#334155")
        )
        card.grid_columnconfigure(0, weight=1)

        # Name
        name_lbl = ctk.CTkLabel(
            card,
            text=product["name"],
            font=FONTS["body_bold"],
            text_color=("#0F172A", "#F8FAFC") if not is_out else COLORS["danger"],
            wraplength=160,
            justify="left",
            anchor="w"
        )
        name_lbl.pack(fill="x", padx=10, pady=(8, 2))

        # Brand / Category
        meta_text = f"{product.get('brand', '')} • {product['category']}"
        meta_lbl = ctk.CTkLabel(
            card,
            text=meta_text,
            font=FONTS["caption"],
            text_color=("#64748B", "#94A3B8"),
            anchor="w"
        )
        meta_lbl.pack(fill="x", padx=10, pady=(0, 4))

        # Price & Stock Footer
        footer = ctk.CTkFrame(card, fg_color="transparent")
        footer.pack(fill="x", padx=10, pady=(4, 8))

        price_lbl = ctk.CTkLabel(
            footer,
            text=f"{product['sale_price']:,.0f} DA".replace(",", " "),
            font=FONTS["title_small"],
            text_color=COLORS["primary"]
        )
        price_lbl.pack(side="left")

        stock_text = f"Stock: {product['stock_qty']}" if not is_out else "RUPTURE"
        stock_color = COLORS["danger"] if is_out else (COLORS["warning"] if product["stock_qty"] <= product["min_stock_alert"] else COLORS["emerald"])
        
        stock_lbl = ctk.CTkLabel(
            footer,
            text=stock_text,
            font=FONTS["caption_bold"],
            text_color=stock_color
        )
        stock_lbl.pack(side="right")

        # Click event to add to cart
        if not is_out:
            for w in [card, name_lbl, meta_lbl, footer, price_lbl, stock_lbl]:
                w.bind("<Button-1>", lambda e, prod=product: self._add_to_cart(prod))

        return card

    def _add_to_cart(self, product):
        success, msg = self.pos_service.add_product(product, qty=1)
        if success:
            self._refresh_cart_ui()
        else:
            ToastNotification.show(self, msg, "warning")

    def _refresh_cart_ui(self):
        for w in self.cart_scroll.winfo_children():
            w.destroy()

        if not self.pos_service.cart:
            empty_lbl = ctk.CTkLabel(
                self.cart_scroll,
                text="Le panier est vide\nScannez un article pour commencer",
                font=FONTS["body"],
                text_color=("#94A3B8", "#64748B"),
                justify="center"
            )
            empty_lbl.pack(pady=40)
        else:
            for idx, item in enumerate(self.pos_service.cart):
                self._create_cart_row(idx, item)

        # Update totals
        totals = self.pos_service.get_totals()
        self.subtotal_lbl.configure(text=f"Total Brut ({totals['total_items']} art.) : {totals['subtotal']:,.2f} DA")
        self.discount_lbl.configure(text=f"Remises Déduites : -{totals['discount_amount']:,.2f} DA")
        self.final_total_lbl.configure(text=f"TOTAL : {totals['final_total']:,.2f} DA")

    def _create_cart_row(self, idx, item):
        p = item["product"]
        row = ctk.CTkFrame(
            self.cart_scroll,
            corner_radius=8,
            fg_color=("#F8FAFC", "#0F172A"),
            border_width=1,
            border_color=("#E2E8F0", "#334155")
        )
        row.pack(fill="x", pady=3)
        row.grid_columnconfigure(0, weight=1)

        # Item Info
        info_frame = ctk.CTkFrame(row, fg_color="transparent")
        info_frame.pack(fill="x", padx=8, pady=(6, 2))

        ctk.CTkLabel(info_frame, text=p["name"][:24], font=FONTS["body_bold"], text_color=("#0F172A", "#F8FAFC"), anchor="w").pack(side="left")
        ctk.CTkLabel(info_frame, text=f"{item['total']:,.0f} DA", font=FONTS["body_bold"], text_color=COLORS["primary"]).pack(side="right")

        # Controls (+ / - / delete)
        ctrl_frame = ctk.CTkFrame(row, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=8, pady=(0, 6))

        ctk.CTkLabel(ctrl_frame, text=f"P.U : {item['unit_price']:,.0f} DA", font=FONTS["caption"], text_color=("#64748B", "#94A3B8")).pack(side="left")

        # Delete
        del_btn = ctk.CTkButton(ctrl_frame, text="✕", width=22, height=22, font=FONTS["caption_bold"], fg_color="transparent", text_color=COLORS["danger"], hover_color=("#FEF2F2", "#334155"), command=lambda i=idx: self._remove_item(i))
        del_btn.pack(side="right", padx=(4, 0))

        # Plus
        plus_btn = ctk.CTkButton(ctrl_frame, text="+", width=24, height=22, font=FONTS["caption_bold"], fg_color=("#E2E8F0", "#334155"), text_color=("#0F172A", "#F8FAFC"), hover_color=COLORS["primary"], command=lambda i=idx, q=item["qty"]+1: self._update_qty(i, q))
        plus_btn.pack(side="right", padx=2)

        # Qty editable entry (direct keyboard input)
        qty_entry = ctk.CTkEntry(ctrl_frame, width=38, height=22, font=FONTS["body_bold"], justify="center")
        qty_entry.insert(0, str(item["qty"]))
        qty_entry.pack(side="right", padx=2)

        def on_qty_entry_commit(event=None, i=idx, entry=qty_entry):
            try:
                new_q = int(entry.get() or 0)
                self._update_qty(i, new_q)
            except ValueError:
                self._refresh_cart_ui()
        qty_entry.bind("<Return>", on_qty_entry_commit)
        qty_entry.bind("<FocusOut>", on_qty_entry_commit)

        # Minus
        minus_btn = ctk.CTkButton(ctrl_frame, text="-", width=24, height=22, font=FONTS["caption_bold"], fg_color=("#E2E8F0", "#334155"), text_color=("#0F172A", "#F8FAFC"), hover_color=COLORS["primary"], command=lambda i=idx, q=item["qty"]-1: self._update_qty(i, q))
        minus_btn.pack(side="right", padx=2)


    def _update_qty(self, idx, new_qty):
        success, msg = self.pos_service.update_item_qty(idx, new_qty)
        if not success and msg:
            ToastNotification.show(self, msg, "warning")
        self._refresh_cart_ui()

    def _remove_item(self, idx):
        self.pos_service.remove_item(idx)
        self._refresh_cart_ui()

    def _clear_cart(self):
        self.pos_service.clear_cart()
        self._refresh_cart_ui()

    def _open_checkout_modal(self):
        if not self.pos_service.cart:
            ToastNotification.show(self, "Le panier est vide !", "warning")
            return

        totals = self.pos_service.get_totals()
        modal = BaseModal(self.winfo_toplevel(), "Règlement & Encaissement", width=520, height=540)
        
        # Montant Total en Grand
        tot_box = ctk.CTkFrame(modal.body, fg_color=("#F8FAFC", "#0F172A"), corner_radius=12, height=70)
        tot_box.pack(fill="x", pady=(0, 15))
        tot_box.pack_propagate(False)

        ctk.CTkLabel(tot_box, text="MONTANT À PAYER", font=FONTS["caption_bold"], text_color=("#64748B", "#94A3B8")).pack(pady=(8, 0))
        ctk.CTkLabel(tot_box, text=f"{totals['final_total']:,.2f} DA", font=FONTS["title_large"], text_color=COLORS["primary"]).pack(pady=(0, 8))

        # Mode de Paiement
        ctk.CTkLabel(modal.body, text="Mode de paiement :", font=FONTS["caption_bold"], text_color=("#475569", "#94A3B8")).pack(anchor="w", pady=(0, 4))
        pay_mode_var = ctk.StringVar(value="especes")
        
        pay_frame = ctk.CTkFrame(modal.body, fg_color="transparent")
        pay_frame.pack(fill="x", pady=(0, 12))
        
        for mode_val, mode_lbl in [("especes", "💵 Espèces"), ("carte", "💳 Carte CIB / Edahabia"), ("autre", "🔄 Autre")]:
            ctk.CTkRadioButton(
                pay_frame,
                text=mode_lbl,
                value=mode_val,
                variable=pay_mode_var,
                font=FONTS["body_bold"],
                fg_color=COLORS["primary"]
            ).pack(side="left", padx=8)

        # Montant Reçu
        ctk.CTkLabel(modal.body, text="Montant Reçu du Client (DA) :", font=FONTS["caption_bold"], text_color=("#475569", "#94A3B8")).pack(anchor="w", pady=(0, 4))
        rec_entry = ctk.CTkEntry(modal.body, font=FONTS["title_medium"], height=44)
        rec_entry.pack(fill="x", pady=(0, 8))
        rec_entry.insert(0, str(int(totals["final_total"])))

        # Billets rapides (Quick cash buttons)
        quick_frame = ctk.CTkFrame(modal.body, fg_color="transparent")
        quick_frame.pack(fill="x", pady=(0, 12))
        
        for val in [1000, 2000, 5000, 10000]:
            btn = ctk.CTkButton(
                quick_frame,
                text=f"{val} DA",
                width=65,
                height=30,
                font=FONTS["caption_bold"],
                fg_color=("#E2E8F0", "#334155"),
                text_color=("#0F172A", "#F8FAFC"),
                command=lambda v=val: (rec_entry.delete(0, "end"), rec_entry.insert(0, str(v)), update_change())
            )
            btn.pack(side="left", padx=3)

        # Monnaie à rendre Display
        change_box = ctk.CTkFrame(modal.body, fg_color=("#ECFDF5", "#064E3B"), corner_radius=10, height=45)
        change_box.pack(fill="x", pady=(0, 15))
        change_box.pack_propagate(False)

        change_lbl = ctk.CTkLabel(
            change_box,
            text="Monnaie à rendre : 0.00 DA",
            font=FONTS["body_bold"],
            text_color=COLORS["emerald"]
        )
        change_lbl.pack(pady=10)

        def update_change(*args):
            try:
                rec = float(rec_entry.get() or 0)
                chg = max(0.0, rec - totals["final_total"])
                change_lbl.configure(text=f"Monnaie à rendre : {chg:,.2f} DA")
            except ValueError:
                change_lbl.configure(text="Montant invalide")

        rec_entry.bind("<KeyRelease>", update_change)
        update_change()

        def confirm_checkout():
            try:
                rec_val = float(rec_entry.get() or 0)
            except ValueError:
                ToastNotification.show(modal, "Veuillez saisir un montant valide", "danger")
                return

            user = AuthService.get_current_user()
            user_id = user.id if user else 1

            success, result = self.pos_service.complete_sale(
                user_id=user_id,
                payment_method=pay_mode_var.get(),
                amount_received=rec_val,
                customer_name="Client Passant"
            )

            if success:
                modal.destroy()
                self._load_products()
                self._refresh_cart_ui()
                self._prompt_print_receipt(result)
            else:
                ToastNotification.show(modal, result, "danger")

        # Action Buttons
        act_frame = ctk.CTkFrame(modal.body, fg_color="transparent")
        act_frame.pack(fill="x", side="bottom", pady=10)

        ctk.CTkButton(
            act_frame,
            text="Annuler",
            width=120,
            height=40,
            font=FONTS["body_bold"],
            fg_color=("#E2E8F0", "#334155"),
            text_color=("#0F172A", "#F8FAFC"),
            command=modal.destroy
        ).pack(side="left")

        ctk.CTkButton(
            act_frame,
            text="VALIDER LE PAIEMENT",
            height=40,
            font=FONTS["body_bold"],
            fg_color=COLORS["emerald"],
            hover_color=COLORS["emerald_hover"],
            command=confirm_checkout
        ).pack(side="right", fill="x", expand=True, padx=(10, 0))

    def _prompt_print_receipt(self, sale_data):
        """Affiche une boîte de dialogue demandant au caissier s'il souhaite imprimer le ticket."""
        prompt = BaseModal(self.winfo_toplevel(), "Impression Ticket de Caisse", width=450, height=330)
        
        # En-tête / Détails de la vente
        info_frame = ctk.CTkFrame(prompt.body, fg_color=("#F1F5F9", "#1E293B"), corner_radius=10)
        info_frame.pack(fill="x", pady=(0, 12), padx=4)
        
        ctk.CTkLabel(
            info_frame,
            text=f"✅ Vente {sale_data.get('sale_code', '')} validée !",
            font=FONTS["title_medium"],
            text_color=COLORS["emerald"]
        ).pack(pady=(12, 4))
        
        totals = sale_data.get("totals", {})
        net = totals.get("final_total", 0.0)
        change = sale_data.get("change_given", 0.0)
        
        details_txt = f"Net payé : {net:,.2f} DA"
        if change > 0:
            details_txt += f"  •  Monnaie rendue : {change:,.2f} DA"
            
        ctk.CTkLabel(
            info_frame,
            text=details_txt,
            font=FONTS["caption_bold"],
            text_color=("#475569", "#94A3B8")
        ).pack(pady=(0, 12))
        
        # Question posée au caissier
        ctk.CTkLabel(
            prompt.body,
            text="Souhaitez-vous imprimer le ticket de caisse ?",
            font=FONTS["body_bold"],
            text_color=("#0F172A", "#F8FAFC")
        ).pack(pady=(6, 18))
        
        def do_print():
            prompt.destroy()
            PrinterService.print_ticket(sale_data)
            ToastNotification.show(self, f"Ticket {sale_data.get('sale_code', '')} imprimé !", "success")
            self.barcode_entry.focus_set()

        def do_skip():
            prompt.destroy()
            ToastNotification.show(self, f"Vente {sale_data.get('sale_code', '')} enregistrée (sans impression)", "info")
            self.barcode_entry.focus_set()

        # Boutons d'action
        btn_frame = ctk.CTkFrame(prompt.body, fg_color="transparent")
        btn_frame.pack(fill="x", side="bottom", pady=8)

        no_btn = ctk.CTkButton(
            btn_frame,
            text="❌ Non / Terminer",
            height=42,
            font=FONTS["body_bold"],
            fg_color=("#E2E8F0", "#334155"),
            text_color=("#0F172A", "#F8FAFC"),
            hover_color=("#CBD5E1", "#475569"),
            command=do_skip
        )
        no_btn.pack(side="left", padx=(0, 10), fill="x", expand=True)

        yes_btn = ctk.CTkButton(
            btn_frame,
            text="🖨️ Oui, Imprimer",
            height=42,
            font=FONTS["body_bold"],
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            command=do_print
        )
        yes_btn.pack(side="right", fill="x", expand=True)
        
        # Raccourcis clavier (Entrée pour imprimer, Échap pour passer)
        prompt.bind("<Return>", lambda e: do_print())
        prompt.bind("<KP_Enter>", lambda e: do_print())
        prompt.bind("<Escape>", lambda e: do_skip())
        
        yes_btn.focus_set()

