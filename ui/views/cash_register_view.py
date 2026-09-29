import customtkinter as ctk
from ui.theme import FONTS, COLORS
from services.pos_service import POSService
from services.auth_service import AuthService
from database.db_manager import get_db
from ui.components.modern_table import ModernTable
from ui.components.modal import BaseModal
from ui.components.notification import ToastNotification

class CashRegisterView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # 1. Active Session Card
        self.session_card = ctk.CTkFrame(self, corner_radius=14, fg_color=("#FFFFFF", "#1E293B"), border_width=1, border_color=("#E2E8F0", "#334155"))
        self.session_card.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))

        self.session_info_frame = ctk.CTkFrame(self.session_card, fg_color="transparent")
        self.session_info_frame.pack(fill="x", padx=20, pady=15)

        self.status_title = ctk.CTkLabel(self.session_info_frame, text="État de la Caisse : En attente", font=FONTS["title_medium"])
        self.status_title.pack(side="left")

        self.session_action_btn = ctk.CTkButton(
            self.session_info_frame,
            text="Ouvrir la Caisse",
            height=38,
            font=FONTS["body_bold"],
            fg_color=COLORS["emerald"],
            hover_color=COLORS["emerald_hover"],
            command=self._handle_session_action
        )
        self.session_action_btn.pack(side="right")

        self.session_details_lbl = ctk.CTkLabel(self.session_card, text="", font=FONTS["body"], text_color=("#64748B", "#94A3B8"), justify="left")
        self.session_details_lbl.pack(fill="x", padx=20, pady=(0, 15))

        # 2. History of Cash Sessions
        ctk.CTkLabel(self, text="Historique des Clôtures de Caisse Journalières", font=FONTS["title_small"]).grid(row=1, column=0, sticky="w", padx=18, pady=(10, 4))

        cols = [
            ("Session N°", 2, "center"),
            ("Ouverture", 3, "w"),
            ("Clôture", 3, "w"),
            ("Fond Initial", 2, "e"),
            ("Ventes Espèces", 2, "e"),
            ("Total Réel Compté", 2, "e"),
            ("Écart Caisse", 2, "center"),
            ("Statut", 2, "center")
        ]
        self.sessions_table = ModernTable(self, cols)
        self.sessions_table.grid(row=2, column=0, sticky="nsew", padx=15, pady=(0, 15))

        self.refresh_session_ui()

    def refresh_session_ui(self):
        user = AuthService.get_current_user()
        user_id = user.id if user else 1
        
        current = POSService.get_current_session(user_id=None)
        
        if current and current["status"] == "open":
            self.status_title.configure(text="🟢 Session de Caisse OUVERTE", text_color=COLORS["emerald"])
            self.session_action_btn.configure(text="🔒 Clôturer la Caisse (Fin de Journée)", fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"])
            
            # Calcul ventes courantes
            db = get_db()
            stats = db.execute_query("""
                SELECT COUNT(*) as c, COALESCE(SUM(total_ttc), 0) as tot, COALESCE(SUM(CASE WHEN payment_method='especes' THEN total_ttc ELSE 0 END), 0) as cash
                FROM sales WHERE session_id = ?
            """, (current["id"],))[0]

            self.session_details_lbl.configure(
                text=f"Ouverte le : {current['opening_date']} | Fond initial : {current['opening_amount']:,.2f} DA\nVentes session : {stats['c']} transactions ({stats['tot']:,.2f} DA dont {stats['cash']:,.2f} DA en espèces)\nEspèces théoriques en tiroir : {current['opening_amount'] + stats['cash']:,.2f} DA"
            )
            self.current_session = current
        else:
            self.status_title.configure(text="🔴 Caisse FERMÉE", text_color=COLORS["danger"])
            self.session_action_btn.configure(text="🔓 Ouvrir la Caisse (Fond de Caisse)", fg_color=COLORS["emerald"], hover_color=COLORS["emerald_hover"])
            self.session_details_lbl.configure(text="Aucune session de caisse active. Veuillez ouvrir la caisse pour enregistrer le fond initial.")
            self.current_session = None

        self._load_sessions_history()

    def _load_sessions_history(self):
        db = get_db()
        user = AuthService.get_current_user()
        if user and user.role != "admin":
            rows = db.execute_query("SELECT * FROM cash_sessions WHERE user_id = ? ORDER BY id DESC LIMIT 50", (user.id,))
        else:
            rows = db.execute_query("SELECT * FROM cash_sessions ORDER BY id DESC LIMIT 50")
        table_rows = []
        for s in rows:
            diff = s["cash_difference"] or 0.0
            diff_text = f"+{diff:,.2f} DA" if diff > 0 else (f"{diff:,.2f} DA" if diff < 0 else "0.00 DA (Exact)")
            
            table_rows.append([
                f"#{s['id']}",
                s["opening_date"][:16] if s["opening_date"] else "-",
                s["closing_date"][:16] if s["closing_date"] else "En cours",
                f"{s['opening_amount']:,.0f} DA",
                f"{(s['theoretical_cash'] - s['opening_amount']):,.0f} DA",
                f"{s['real_cash']:,.0f} DA" if s["status"] == "closed" else "-",
                diff_text if s["status"] == "closed" else "-",
                "🟢 Ouverte" if s["status"] == "open" else "🔒 Clôturée"
            ])
        self.sessions_table.set_data(table_rows)

    def _handle_session_action(self):
        if self.current_session:
            self._open_close_session_modal()
        else:
            self._open_open_session_modal()

    def _open_open_session_modal(self):
        modal = BaseModal(self.winfo_toplevel(), "Ouverture de Caisse - Fond Initial", width=460, height=300)

        ctk.CTkLabel(modal.body, text="Montant du fond de caisse initial (DA) :", font=FONTS["body_bold"]).pack(anchor="w", pady=(10, 6))
        
        amount_entry = ctk.CTkEntry(modal.body, font=FONTS["title_medium"], height=44)
        amount_entry.pack(fill="x", pady=(0, 20))
        amount_entry.insert(0, "5000")

        def confirm():
            try:
                amt = float(amount_entry.get() or 0)
            except ValueError:
                ToastNotification.show(modal, "Montant invalide", "danger")
                return

            user = AuthService.get_current_user()
            user_id = user.id if user else 1

            success, res = POSService.open_cash_session(user_id, amt)
            if success:
                modal.destroy()
                ToastNotification.show(self, f"Session de caisse #{res} ouverte avec succès !", "success")
                self.refresh_session_ui()
            else:
                ToastNotification.show(modal, res, "danger")

        ctk.CTkButton(modal.body, text="VALIDER L'OUVERTURE", height=42, font=FONTS["body_bold"], fg_color=COLORS["emerald"], command=confirm).pack(fill="x", side="bottom")

    def _open_close_session_modal(self):
        modal = BaseModal(self.winfo_toplevel(), "Clôture Journalière de Caisse", width=520, height=480)

        db = get_db()
        stats = db.execute_query("""
            SELECT COUNT(*) as c, COALESCE(SUM(total_ttc), 0) as tot, COALESCE(SUM(CASE WHEN payment_method='especes' THEN total_ttc ELSE 0 END), 0) as cash
            FROM sales WHERE session_id = ?
        """, (self.current_session["id"],))[0]

        theo_cash = self.current_session["opening_amount"] + stats["cash"]

        info_box = ctk.CTkFrame(modal.body, fg_color=("#F8FAFC", "#0F172A"), corner_radius=10)
        info_box.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(info_box, text=f"Fond initial : {self.current_session['opening_amount']:,.2f} DA", font=FONTS["caption"]).pack(anchor="w", padx=15, pady=(8, 2))
        ctk.CTkLabel(info_box, text=f"Total Ventes Espèces : {stats['cash']:,.2f} DA", font=FONTS["caption"]).pack(anchor="w", padx=15, pady=2)
        ctk.CTkLabel(info_box, text=f"Espèces Théoriques Attendues : {theo_cash:,.2f} DA", font=FONTS["body_bold"], text_color=COLORS["primary"]).pack(anchor="w", padx=15, pady=(2, 8))

        ctk.CTkLabel(modal.body, text="Montant Réel Compté dans le Tiroir-Caisse (DA) :", font=FONTS["caption_bold"]).pack(anchor="w", pady=(0, 4))
        real_entry = ctk.CTkEntry(modal.body, font=FONTS["title_medium"], height=42)
        real_entry.pack(fill="x", pady=(0, 10))
        real_entry.insert(0, str(int(theo_cash)))

        diff_lbl = ctk.CTkLabel(modal.body, text="Écart calculé : 0.00 DA (Conforme)", font=FONTS["body_bold"], text_color=COLORS["success"])
        diff_lbl.pack(anchor="w", pady=(0, 10))

        def update_diff(*args):
            try:
                r = float(real_entry.get() or 0)
                d = r - theo_cash
                if d == 0:
                    diff_lbl.configure(text="Écart calculé : 0.00 DA (Exact)", text_color=COLORS["success"])
                elif d > 0:
                    diff_lbl.configure(text=f"Écart calculé : +{d:,.2f} DA (Surplus de caisse)", text_color=COLORS["info"])
                else:
                    diff_lbl.configure(text=f"Écart calculé : {d:,.2f} DA (Manquant de caisse)", text_color=COLORS["danger"])
            except ValueError:
                diff_lbl.configure(text="Montant invalide")

        real_entry.bind("<KeyRelease>", update_diff)

        ctk.CTkLabel(modal.body, text="Notes / Justifications d'écart :", font=FONTS["caption_bold"]).pack(anchor="w", pady=(0, 4))
        notes_entry = ctk.CTkEntry(modal.body, height=36, font=FONTS["body"], placeholder_text="Optionnel...")
        notes_entry.pack(fill="x", pady=(0, 15))

        def confirm_close():
            try:
                r = float(real_entry.get() or 0)
            except ValueError:
                ToastNotification.show(modal, "Montant invalide", "danger")
                return

            success, res = POSService.close_cash_session(
                session_id=self.current_session["id"],
                real_cash=r,
                notes=notes_entry.get().strip()
            )

            if success:
                modal.destroy()
                ToastNotification.show(self, "Caisse clôturée avec succès !", "success")
                self.refresh_session_ui()
            else:
                ToastNotification.show(modal, res, "danger")

        ctk.CTkButton(modal.body, text="CONFIRMER LA CLÔTURE DE CAISSE", height=44, font=FONTS["body_bold"], fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"], command=confirm_close).pack(fill="x", side="bottom")
