import customtkinter as ctk
from ui.theme import FONTS, COLORS
from services.stock_service import StockService
from services.supplier_service import SupplierService
from services.auth_service import AuthService
from services.barcode_service import BarcodeService
from config import CATEGORIES
from ui.components.modern_table import ModernTable
from ui.components.modal import BaseModal
from ui.components.notification import ToastNotification


class StockView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.tabview = ctk.CTkTabview(self, corner_radius=12, fg_color=("white", "#1E293B"))
        self.tabview.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=15, pady=15)

        self.tab_history = self.tabview.add("\U0001f4dc Historique des Mouvements")
        self.tab_reception = self.tabview.add("\U0001f4e6 R\u00e9ception Marchandise (Scanner)")
        self.tab_inventory = self.tabview.add("\U0001f50d Inventaire Physique Douchette")

        self._setup_history_tab()
        self._setup_reception_tab()
        self._setup_inventory_tab()

    # ── 1. HISTORIQUE ────────────────────────────────────────────────────────
    def _setup_history_tab(self):
        self.tab_history.grid_columnconfigure(0, weight=1)
        self.tab_history.grid_rowconfigure(1, weight=1)

        ctrl_frame = ctk.CTkFrame(self.tab_history, fg_color="transparent", height=45)
        ctrl_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        ctk.CTkLabel(ctrl_frame, text="Journal d'audit de tous les mouvements de stock",
                     font=FONTS["title_small"]).pack(side="left")
        ctk.CTkButton(ctrl_frame, text="\U0001f504 Actualiser", width=100, height=32,
                      font=FONTS["caption_bold"], command=self.load_movements).pack(side="right")

        cols = [
            ("Date & Heure", 2, "w"),
            ("Type Mouvement", 2, "w"),
            ("Code-barres", 2, "w"),
            ("Produit", 3, "w"),
            ("Variation", 1, "center"),
            ("Ancien -> Nouveau", 2, "center"),
            ("Motif / R\u00e9f", 3, "w"),
            ("Op\u00e9rateur", 2, "w")
        ]
        self.history_table = ModernTable(self.tab_history, cols)
        self.history_table.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.load_movements()

    def load_movements(self):
        movements = StockService.get_stock_movements(limit=100)
        rows = []
        for m in movements:
            type_text = {
                "reception": "\U0001f4e5 R\u00e9ception",
                "vente": "\U0001f6d2 Vente",
                "ajustement": "\u2696\ufe0f Ajustement",
                "inventaire": "\U0001f50d Inventaire",
                "perte_casse": "\u26a0\ufe0f Perte/Casse"
            }.get(m["movement_type"], m["movement_type"])
            qty_str = f"+{m['qty']}" if m["qty"] > 0 else f"{m['qty']}"
            rows.append([
                m["created_at"], type_text, m["barcode"], m["product_name"][:30],
                qty_str, f"{m['old_stock']} \u2192 {m['new_stock']}",
                m["reason"] or "-", m["user_name"] or "Syst\u00e8me"
            ])
        self.history_table.set_data(rows)

    # ── 2. RÉCEPTION MARCHANDISE (Scanner + Saisie Qté + Validation Globale) ──
    def _setup_reception_tab(self):
        self.tab_reception.grid_columnconfigure(0, weight=1)
        self.tab_reception.grid_rowconfigure(2, weight=1)

        # ─ Fournisseur sélection ──────────────────────────────────────────────
        sup_bar = ctk.CTkFrame(self.tab_reception, fg_color=("white", "#1E293B"), corner_radius=10,
                               border_width=1, border_color=("gray80", "#334155"))
        sup_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))

        ctk.CTkLabel(sup_bar, text="Fournisseur :", font=FONTS["caption_bold"]).pack(side="left", padx=12, pady=10)
        suppliers = SupplierService.get_suppliers()
        sup_names = ["(Aucun / Divers)"] + [s["name"] for s in suppliers]
        self._suppliers_list = suppliers

        self.rec_sup_menu = ctk.CTkOptionMenu(sup_bar, values=sup_names, width=260, height=34, font=FONTS["body"])
        self.rec_sup_menu.pack(side="left", padx=8, pady=10)

        # ─ Scan & Saisie Rapide Bar ────────────────────────────────────────────
        scan_box = ctk.CTkFrame(self.tab_reception, fg_color=("gray98", "#0F172A"), corner_radius=10,
                                border_width=1, border_color=("gray80", "#334155"))
        scan_box.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 6))

        ctk.CTkLabel(scan_box, text="🔍 Scanner un code-barres :",
                     font=FONTS["caption_bold"], text_color=COLORS["info"]).pack(side="left", padx=(12, 4), pady=10)
        
        self.rec_bc_entry = ctk.CTkEntry(scan_box, height=36, font=FONTS["title_small"],
                                          placeholder_text="Scannez ici ou saisissez le code-barres...")
        self.rec_bc_entry.pack(side="left", fill="x", expand=True, padx=4, pady=8)
        self.rec_bc_entry.bind("<Return>", self._on_reception_scan)

        ctk.CTkLabel(scan_box, text="Qté :", font=FONTS["caption_bold"]).pack(side="left", padx=(8, 2), pady=10)
        self.rec_qty_entry = ctk.CTkEntry(scan_box, width=65, height=36, font=FONTS["title_small"], justify="center")
        self.rec_qty_entry.insert(0, "1")
        self.rec_qty_entry.pack(side="left", padx=2, pady=8)
        self.rec_qty_entry.bind("<Return>", self._on_reception_scan)

        ctk.CTkLabel(scan_box, text="P. Achat (DA) :", font=FONTS["caption_bold"]).pack(side="left", padx=(8, 2), pady=10)
        self.rec_price_entry = ctk.CTkEntry(scan_box, width=105, height=36, font=FONTS["body"], placeholder_text="Auto / DA")
        self.rec_price_entry.pack(side="left", padx=2, pady=8)
        self.rec_price_entry.bind("<Return>", self._on_reception_scan)

        ctk.CTkButton(scan_box, text="➕ Ajouter", width=100, height=36,
                      font=FONTS["caption_bold"], fg_color=COLORS["primary"],
                      hover_color=COLORS["primary_hover"],
                      command=self._on_reception_scan).pack(side="right", padx=10, pady=8)

        # ─ Table des produits en cours de réception ─────────────────────────
        cols = [
            ("Code-barres", 2, "w"),
            ("Désignation", 4, "w"),
            ("Stock Actuel", 2, "center"),
            ("Qté Reçue", 3, "center"),
            ("Prix Achat (DA)", 2, "center"),
            ("Total Ligne (DA)", 2, "e"),
            ("Actions", 1, "center")
        ]
        self.rec_table = ModernTable(self.tab_reception, cols)
        self.rec_table.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 6))

        # ─ Barre de résumé et validation globale ─────────────────────────────
        footer_frame = ctk.CTkFrame(self.tab_reception, fg_color="transparent")
        footer_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))

        self.rec_summary_lbl = ctk.CTkLabel(
            footer_frame,
            text="📦 0 article(s)  •  Total unités : 0 u.  •  Montant Total : 0.00 DA",
            font=FONTS["body_bold"],
            text_color=("#475569", "#94A3B8")
        )
        self.rec_summary_lbl.pack(side="left", padx=5)

        self.rec_clear_btn = ctk.CTkButton(
            footer_frame,
            text="🗑️ Tout Vider",
            width=110,
            height=40,
            font=FONTS["caption_bold"],
            fg_color=("#E2E8F0", "#334155"),
            text_color=("#0F172A", "#F8FAFC"),
            hover_color=COLORS["danger"],
            command=self._clear_pending_queue
        )
        self.rec_clear_btn.pack(side="right", padx=(10, 0))

        self.rec_submit_btn = ctk.CTkButton(
            footer_frame,
            text="📥 VALIDER TOUTE LA RÉCEPTION EN STOCK",
            height=40,
            font=FONTS["body_bold"],
            fg_color=COLORS["emerald"],
            hover_color=COLORS["emerald_hover"],
            command=self._confirm_all_receptions
        )
        self.rec_submit_btn.pack(side="right", fill="x", expand=True)

        # Stockage des lignes: {barcode: {"product": dict, "qty": int, "price": float}}
        self._pending_receptions = {}

    def _on_reception_scan(self, event=None):
        bc = self.rec_bc_entry.get().strip()
        if not bc:
            ToastNotification.show(self, "Veuillez scanner ou saisir un code-barres", "warning")
            self.rec_bc_entry.focus_set()
            return

        try:
            qty = int(self.rec_qty_entry.get() or 1)
            if qty <= 0:
                qty = 1
        except ValueError:
            ToastNotification.show(self, "Quantité invalide (nombre entier requis)", "danger")
            return

        prod = StockService.get_product_by_barcode(bc)
        if prod:
            prod_dict = dict(prod)
            # Vérifier si un prix d'achat personnalisé a été renseigné
            custom_price_str = self.rec_price_entry.get().strip()
            if custom_price_str:
                try:
                    price = float(custom_price_str)
                except ValueError:
                    price = float(prod_dict.get("purchase_price", 0.0))
            else:
                price = float(prod_dict.get("purchase_price", 0.0))

            if bc in self._pending_receptions:
                self._pending_receptions[bc]["qty"] += qty
                if custom_price_str:
                    self._pending_receptions[bc]["price"] = price
                ToastNotification.show(
                    self,
                    f"✅ +{qty} pour {prod_dict['name'][:25]} (Total : {self._pending_receptions[bc]['qty']} u.)",
                    "info"
                )
            else:
                self._pending_receptions[bc] = {
                    "product": prod_dict,
                    "qty": qty,
                    "price": price
                }
                ToastNotification.show(
                    self,
                    f"✅ {prod_dict['name'][:25]} ajouté ({qty} u. à {price:,.0f} DA)",
                    "success"
                )

            self._refresh_reception_table()
        else:
            ToastNotification.show(self, f"❌ Code-barre inconnu ({bc}). Créez d'abord le produit dans le catalogue.", "danger")

        # Réinitialiser les champs de scan pour le prochain produit
        self.rec_bc_entry.delete(0, "end")
        self.rec_qty_entry.delete(0, "end")
        self.rec_qty_entry.insert(0, "1")
        self.rec_price_entry.delete(0, "end")
        self.rec_bc_entry.focus_set()

    def _refresh_reception_table(self):
        rows = []
        for bc, entry in list(self._pending_receptions.items()):
            prod = entry["product"]
            qty = entry["qty"]
            price = entry["price"]
            line_total = qty * price

            # Cellule interactive pour la Quantité: [-] [ QTE ] [+]
            def make_qty_cell(parent, barcode=bc):
                f = ctk.CTkFrame(parent, fg_color="transparent")
                
                def decr():
                    if self._pending_receptions.get(barcode, {}).get("qty", 0) > 1:
                        self._pending_receptions[barcode]["qty"] -= 1
                        self._refresh_reception_table()

                def incr():
                    if barcode in self._pending_receptions:
                        self._pending_receptions[barcode]["qty"] += 1
                        self._refresh_reception_table()

                def on_edit(event=None):
                    try:
                        val = int(q_entry.get().strip() or 1)
                        if val > 0 and barcode in self._pending_receptions:
                            self._pending_receptions[barcode]["qty"] = val
                            self._update_summary_totals()
                    except ValueError:
                        pass

                ctk.CTkButton(
                    f, text="−", width=26, height=26, font=FONTS["body_bold"],
                    fg_color=("#E2E8F0", "#334155"), text_color=("#0F172A", "#F8FAFC"),
                    hover_color=COLORS["primary"], command=decr
                ).pack(side="left", padx=2)

                q_entry = ctk.CTkEntry(f, width=50, height=26, font=FONTS["body_bold"], justify="center")
                q_entry.insert(0, str(self._pending_receptions[barcode]["qty"]))
                q_entry.bind("<KeyRelease>", on_edit)
                q_entry.bind("<FocusOut>", lambda e: self._refresh_reception_table())
                q_entry.pack(side="left", padx=2)

                ctk.CTkButton(
                    f, text="+", width=26, height=26, font=FONTS["body_bold"],
                    fg_color=("#E2E8F0", "#334155"), text_color=("#0F172A", "#F8FAFC"),
                    hover_color=COLORS["primary"], command=incr
                ).pack(side="left", padx=2)

                return f

            # Cellule interactive pour le Prix d'Achat
            def make_price_cell(parent, barcode=bc):
                f = ctk.CTkFrame(parent, fg_color="transparent")
                p_entry = ctk.CTkEntry(f, width=80, height=26, font=FONTS["body"], justify="center")
                p_entry.insert(0, str(int(self._pending_receptions[barcode]["price"])))

                def on_price_edit(event=None):
                    try:
                        val = float(p_entry.get().strip() or 0)
                        if val >= 0 and barcode in self._pending_receptions:
                            self._pending_receptions[barcode]["price"] = val
                            self._update_summary_totals()
                    except ValueError:
                        pass

                p_entry.bind("<KeyRelease>", on_price_edit)
                p_entry.bind("<FocusOut>", lambda e: self._refresh_reception_table())
                p_entry.pack(side="left", padx=2)
                return f

            # Cellule de suppression
            def make_del_btn(parent, barcode=bc):
                f = ctk.CTkFrame(parent, fg_color="transparent")
                ctk.CTkButton(
                    f, text="🗑️", width=30, height=26,
                    fg_color=("gray90", "#334155"), text_color=("gray10", "gray90"),
                    hover_color=COLORS["danger"],
                    command=lambda b=barcode: self._remove_from_queue(b)
                ).pack()
                return f

            rows.append([
                prod["barcode"],
                prod["name"][:32],
                f"{prod['stock_qty']} u.",
                make_qty_cell,
                make_price_cell,
                f"{line_total:,.2f} DA",
                make_del_btn
            ])

        self.rec_table.set_data(rows)
        self._update_summary_totals()

    def _update_summary_totals(self):
        total_units = sum(entry["qty"] for entry in self._pending_receptions.values())
        total_amount = sum(entry["qty"] * entry["price"] for entry in self._pending_receptions.values())
        count = len(self._pending_receptions)

        self.rec_summary_lbl.configure(
            text=f"📦 {count} référence(s)  •  Total unités : {total_units} u.  •  Montant Total : {total_amount:,.2f} DA"
        )
        self.rec_submit_btn.configure(
            text=f"📥 VALIDER TOUTE LA RÉCEPTION EN STOCK ({total_units} unités - {total_amount:,.2f} DA)"
        )

    def _remove_from_queue(self, barcode):
        if barcode in self._pending_receptions:
            del self._pending_receptions[barcode]
            self._refresh_reception_table()

    def _clear_pending_queue(self):
        if not self._pending_receptions:
            return
        self._pending_receptions.clear()
        self._refresh_reception_table()
        ToastNotification.show(self, "Liste de réception vidée", "info")

    def _confirm_all_receptions(self):
        if not self._pending_receptions:
            ToastNotification.show(self, "Aucun produit en attente de réception", "warning")
            return

        user = AuthService.get_current_user()
        user_id = user.id if user else 1
        sup_name = self.rec_sup_menu.get()
        reason = f"Réception fournisseur {sup_name}" if sup_name != "(Aucun / Divers)" else "Réception marchandise"

        success_count = 0
        total_units = 0
        errors = []
        for bc, entry in list(self._pending_receptions.items()):
            qty = int(entry["qty"])
            price = float(entry["price"])
            ok, msg = StockService.add_reception(
                product_id=entry["product"]["id"],
                qty=qty,
                purchase_price=price,
                user_id=user_id,
                reason=reason
            )
            if ok:
                success_count += 1
                total_units += qty
            else:
                errors.append(msg)

        self._pending_receptions.clear()
        self._refresh_reception_table()
        self.load_movements()

        if success_count > 0:
            ToastNotification.show(
                self,
                f"✅ Réception validée : {success_count} référence(s) ({total_units} unités ajoutées en stock) !",
                "success"
            )
        if errors:
            ToastNotification.show(self, f"⚠️ {len(errors)} erreur(s) : {errors[0]}", "warning")


    # ── 3. INVENTAIRE PHYSIQUE DOUCHETTE ─────────────────────────────────────
    def _setup_inventory_tab(self):
        self.tab_inventory.grid_columnconfigure(0, weight=1)
        self.tab_inventory.grid_rowconfigure(2, weight=1)

        top_bar = ctk.CTkFrame(self.tab_inventory, fg_color=("gray98", "#0F172A"), corner_radius=10, height=55)
        top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        top_bar.pack_propagate(False)

        ctk.CTkLabel(top_bar, text="\U0001f50d SCANNER INVENTAIRE :", font=FONTS["body_bold"],
                     text_color=COLORS["info"]).pack(side="left", padx=(15, 10))
        self.inv_scan_entry = ctk.CTkEntry(
            top_bar,
            placeholder_text="Scannez chaque article en rayon (chaque scan incr\u00e9mente +1)...",
            font=FONTS["body"]
        )
        self.inv_scan_entry.pack(side="left", fill="both", expand=True, padx=5, pady=8)
        self.inv_scan_entry.bind("<Return>", self._on_inventory_scan)

        self.inv_counts = {}

        actions_bar = ctk.CTkFrame(self.tab_inventory, fg_color="transparent")
        actions_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

        self.inv_status_lbl = ctk.CTkLabel(actions_bar, text="Articles compt\u00e9s : 0 r\u00e9f\u00e9rence(s)", font=FONTS["body_bold"])
        self.inv_status_lbl.pack(side="left")

        ctk.CTkButton(actions_bar, text="\u2696\ufe0f Appliquer les Ajustements d'Inventaire",
                      font=FONTS["body_bold"], fg_color=COLORS["warning"], hover_color=COLORS["warning_hover"],
                      command=self._apply_inventory_reconciliation).pack(side="right", padx=(5, 0))

        ctk.CTkButton(actions_bar, text="R\u00e9initialiser Comptage",
                      font=FONTS["caption_bold"], fg_color=("gray85", "#334155"),
                      text_color=("gray10", "gray90"),
                      command=self._reset_inventory).pack(side="right")

        cols = [
            ("Code-barres", 2, "w"),
            ("D\u00e9signation", 4, "w"),
            ("Stock Th\u00e9orique", 2, "center"),
            ("Comptage R\u00e9el", 2, "center"),
            ("\u00c9cart", 2, "center"),
            ("Statut", 2, "center")
        ]
        self.inv_table = ModernTable(self.tab_inventory, cols)
        self.inv_table.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def _on_inventory_scan(self, event=None):
        bc = self.inv_scan_entry.get().strip()
        if not bc:
            return
        prod = StockService.get_product_by_barcode(bc)
        if prod:
            pid = prod["id"]
            if pid not in self.inv_counts:
                self.inv_counts[pid] = {"product": dict(prod), "counted": 1}
            else:
                self.inv_counts[pid]["counted"] += 1
            self._refresh_inventory_table()
            self.inv_scan_entry.delete(0, "end")
        else:
            ToastNotification.show(self, f"Code-barre inconnu ({bc})", "danger")

    def _refresh_inventory_table(self):
        rows = []
        for pid, data in self.inv_counts.items():
            p = data["product"]
            counted = data["counted"]
            theo = p["stock_qty"]
            diff = counted - theo
            diff_str = f"+{diff}" if diff > 0 else str(diff)
            status_str = "\u2705 Conforme" if diff == 0 else ("\u26a0\ufe0f Surplus" if diff > 0 else "\U0001f6a8 Manquant")
            rows.append([p["barcode"], p["name"][:35], f"{theo} u.", f"{counted} u.", diff_str, status_str])
        self.inv_table.set_data(rows)
        self.inv_status_lbl.configure(text=f"Articles compt\u00e9s : {len(self.inv_counts)} r\u00e9f\u00e9rence(s)")

    def _reset_inventory(self):
        self.inv_counts.clear()
        self._refresh_inventory_table()

    def _apply_inventory_reconciliation(self):
        if not self.inv_counts:
            ToastNotification.show(self, "Aucun article compt\u00e9", "warning")
            return
        user = AuthService.get_current_user()
        user_id = user.id if user else 1
        adjusted = 0
        for pid, data in self.inv_counts.items():
            counted = data["counted"]
            p = data["product"]
            if counted != p["stock_qty"]:
                StockService.adjust_stock(product_id=pid, new_quantity=counted,
                                          reason="R\u00e9gularisation Inventaire Physique Douchette", user_id=user_id)
                adjusted += 1
        ToastNotification.show(self, f"Inventaire appliqu\u00e9 ! {adjusted} produit(s) ajust\u00e9(s).", "success")
        self._reset_inventory()
        self.load_movements()
