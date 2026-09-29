import customtkinter as ctk
from ui.theme import FONTS, COLORS
from database.db_manager import get_db
from services.backup_service import BackupService
from services.auth_service import AuthService
from ui.components.modern_table import ModernTable
from ui.components.modal import BaseModal
from ui.components.notification import ToastNotification

class SettingsView(ctk.CTkFrame):
    def __init__(self, parent, on_theme_change=None):
        super().__init__(parent, fg_color="transparent")
        self.on_theme_change = on_theme_change

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self, corner_radius=12, fg_color=("#FFFFFF", "#1E293B"))
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)

        self.tab_store = self.tabview.add("🏬 Paramètres Magasin & Ticket")
        self.tab_backup = self.tabview.add("💾 Redondance & Sauvegarde C/D")
        self.tab_users = self.tabview.add("👥 Gestion des Utilisateurs")
        self.tab_theme = self.tabview.add("🎨 Apparence & Thème")

        self._setup_store_tab()
        self._setup_backup_tab()
        self._setup_users_tab()
        self._setup_theme_tab()

    # ---------------- 1. PARAMÈTRES MAGASIN ----------------
    def _setup_store_tab(self):
        scroll = ctk.CTkScrollableFrame(self.tab_store, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=15)

        db = get_db()
        rows = db.execute_query("SELECT key, value FROM settings")
        settings = {r["key"]: r["value"] for r in rows}

        ctk.CTkLabel(scroll, text="Informations du Commerce de Cosmétique", font=FONTS["title_small"], text_color=COLORS["primary"]).pack(anchor="w", pady=(0, 15))

        # Store Name
        ctk.CTkLabel(scroll, text="Nom de l'enseigne / Parfumerie :", font=FONTS["caption_bold"]).pack(anchor="w", pady=(0, 2))
        self.name_entry = ctk.CTkEntry(scroll, height=36, font=FONTS["body"])
        self.name_entry.pack(fill="x", pady=(0, 10))
        self.name_entry.insert(0, settings.get("store_name", "Élégance & Beauté Cosmétique"))

        # Phone & NIF
        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="x", pady=(0, 10))
        grid.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(grid, text="Téléphone :", font=FONTS["caption_bold"]).grid(row=0, column=0, sticky="w", padx=(0, 5))
        ctk.CTkLabel(grid, text="NIF / RC :", font=FONTS["caption_bold"]).grid(row=0, column=1, sticky="w", padx=(5, 0))

        self.phone_entry = ctk.CTkEntry(grid, height=36, font=FONTS["body"])
        self.phone_entry.grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=(2, 0))
        self.phone_entry.insert(0, settings.get("store_phone", "0550 12 34 56"))

        self.nif_entry = ctk.CTkEntry(grid, height=36, font=FONTS["body"])
        self.nif_entry.grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=(2, 0))
        self.nif_entry.insert(0, settings.get("store_nif", "001234567890123"))

        # Address
        ctk.CTkLabel(scroll, text="Adresse complète :", font=FONTS["caption_bold"]).pack(anchor="w", pady=(0, 2))
        self.addr_entry = ctk.CTkEntry(scroll, height=36, font=FONTS["body"])
        self.addr_entry.pack(fill="x", pady=(0, 10))
        self.addr_entry.insert(0, settings.get("store_address", "12 Boulevard Didouche Mourad, Alger"))

        # Ticket Footer
        ctk.CTkLabel(scroll, text="Message de bas de ticket (Pied de page) :", font=FONTS["caption_bold"]).pack(anchor="w", pady=(0, 2))
        self.footer_entry = ctk.CTkEntry(scroll, height=36, font=FONTS["body"])
        self.footer_entry.pack(fill="x", pady=(0, 15))
        self.footer_entry.insert(0, settings.get("ticket_footer", "Merci pour votre visite !"))

        # Printer Type Selection
        ctk.CTkLabel(scroll, text="Type d'imprimante ticket :", font=FONTS["caption_bold"]).pack(anchor="w", pady=(0, 2))
        self.printer_menu = ctk.CTkOptionMenu(
            scroll,
            values=["Simulation (Fichier / Écran)", "ESC/POS USB Thermique", "Pilote Windows Standard"],
            height=36,
            font=FONTS["body"]
        )
        self.printer_menu.pack(fill="x", pady=(0, 20))
        p_val = settings.get("printer_type", "simulation")
        if p_val == "escpos_usb":
            self.printer_menu.set("ESC/POS USB Thermique")
        else:
            self.printer_menu.set("Simulation (Fichier / Écran)")

        # Save Button
        ctk.CTkButton(
            scroll,
            text="💾 ENREGISTRER LES PARAMÈTRES",
            height=42,
            font=FONTS["body_bold"],
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            command=self._save_store_settings
        ).pack(fill="x", pady=(10, 0))

    def _save_store_settings(self):
        db = get_db()
        p_type = "escpos_usb" if "ESC/POS" in self.printer_menu.get() else "simulation"
        updates = [
            ("store_name", self.name_entry.get().strip()),
            ("store_phone", self.phone_entry.get().strip()),
            ("store_nif", self.nif_entry.get().strip()),
            ("store_address", self.addr_entry.get().strip()),
            ("ticket_footer", self.footer_entry.get().strip()),
            ("printer_type", p_type)
        ]
        for k, v in updates:
            db.execute_query("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (k, v), commit=True)
        ToastNotification.show(self, "Paramètres enregistrés avec succès !", "success")

    # ---------------- 2. REDONDANCE & SAUVEGARDE C/D ----------------
    def _setup_backup_tab(self):
        self.tab_backup.grid_columnconfigure(0, weight=1)
        
        box = ctk.CTkFrame(self.tab_backup, corner_radius=12, fg_color=("#F8FAFC", "#0F172A"), border_width=1, border_color=("#E2E8F0", "#334155"))
        box.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(box, text="Surveillance de la Double Partition SQLite (C: & D:)", font=FONTS["title_small"], text_color=COLORS["primary"]).pack(anchor="w", padx=20, pady=(15, 10))

        self.backup_info_lbl = ctk.CTkLabel(box, text="Chargement de l'état...", font=FONTS["body"], justify="left")
        self.backup_info_lbl.pack(fill="x", padx=20, pady=(0, 15))

        btn_row = ctk.CTkFrame(box, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkButton(
            btn_row,
            text="🔄 Forcer la Synchronisation C: ➔ D:",
            height=38,
            font=FONTS["body_bold"],
            fg_color=COLORS["info"],
            hover_color=COLORS["info_hover"],
            command=self._trigger_sync
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_row,
            text="💾 Exporter Sauvegarde Archive (.db)",
            height=38,
            font=FONTS["body_bold"],
            fg_color=COLORS["emerald"],
            hover_color=COLORS["emerald_hover"],
            command=self._export_archive
        ).pack(side="left")

        self.refresh_backup_status()

    def refresh_backup_status(self):
        status = BackupService.get_backup_status()
        p = status["primary"]
        s = status["secondary"]

        text = (
            f"1. BASE PRINCIPALE (Partition C:) :\n"
            f"   • Emplacement : {p['path']}\n"
            f"   • Taille : {p['size_kb']} Ko | Dernière modification : {p['last_modified']}\n"
            f"   • Statut : {p['status']}\n\n"
            f"2. BASE SECONDAIRE REDONDANTE (Partition D:) :\n"
            f"   • Lecteur D: détecté : {'OUI' if s['drive_present'] else 'NON (Repli sur partition C: sans crash)'}\n"
            f"   • Emplacement : {s['path']}\n"
            f"   • Taille : {s['size_kb']} Ko | Dernière modification : {s['last_modified']}\n"
            f"   • Statut de réplication : {s['status']}"
        )
        self.backup_info_lbl.configure(text=text)

    def _trigger_sync(self):
        success, msg = BackupService.trigger_sync()
        if success:
            ToastNotification.show(self, msg, "success")
        else:
            ToastNotification.show(self, msg, "warning")
        self.refresh_backup_status()

    def _export_archive(self):
        success, msg = BackupService.export_manual_backup()
        if success:
            ToastNotification.show(self, msg, "success", duration_ms=4000)
        else:
            ToastNotification.show(self, msg, "danger")

    # ---------------- 3. GESTION DES UTILISATEURS ----------------
    def _setup_users_tab(self):
        self.tab_users.grid_columnconfigure(0, weight=1)
        self.tab_users.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(self.tab_users, fg_color="transparent", height=45)
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        ctk.CTkLabel(top, text="Comptes Utilisateurs & Droits d'Accès", font=FONTS["title_small"]).pack(side="left")

        ctk.CTkButton(
            top,
            text="+ Nouvel Utilisateur",
            height=34,
            font=FONTS["body_bold"],
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            command=self._open_add_user_modal
        ).pack(side="right")

        cols = [
            ("ID", 1, "center"),
            ("Identifiant", 3, "w"),
            ("Nom Complet", 4, "w"),
            ("Rôle", 2, "center"),
            ("Statut", 2, "center"),
            ("Date Création", 3, "w"),
            ("Actions", 3, "center")
        ]
        self.users_table = ModernTable(self.tab_users, cols)
        self.users_table.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        self.load_users()

    def load_users(self):
        AuthService.resequence_user_ids()
        users = AuthService.get_all_users()
        rows = []
        for u in users:
            u_dict = dict(u)
            role_str = "👑 Administrateur" if u_dict["role"] == "admin" else "💼 Caissier"
            status_str = "🟢 Actif" if u_dict["is_active"] else "🔴 Désactivé"
            
            def make_actions_cell(target_user=u_dict):
                def builder(parent_frame):
                    f = ctk.CTkFrame(parent_frame, fg_color="transparent")
                    
                    btn_edit = ctk.CTkButton(
                        f,
                        text="✏️ Modifier",
                        width=72,
                        height=26,
                        font=FONTS["caption_bold"],
                        fg_color=COLORS["info"],
                        hover_color=COLORS["info_hover"],
                        command=lambda usr=target_user: self._open_edit_user_modal(usr)
                    )
                    btn_edit.pack(side="left", padx=2)

                    btn_del = ctk.CTkButton(
                        f,
                        text="🗑️ Supprimer",
                        width=76,
                        height=26,
                        font=FONTS["caption_bold"],
                        fg_color=COLORS["danger"],
                        hover_color=COLORS["danger_hover"],
                        command=lambda usr=target_user: self._delete_user_confirm(usr)
                    )
                    btn_del.pack(side="left", padx=2)
                    return f
                return builder

            rows.append([
                f"#{u_dict['id']}",
                u_dict["username"],
                u_dict["full_name"],
                role_str,
                status_str,
                u_dict["created_at"][:16] if u_dict["created_at"] else "-",
                make_actions_cell()
            ])
        self.users_table.set_data(rows)

    def _open_add_user_modal(self):
        modal = BaseModal(self.winfo_toplevel(), "Créer un Nouvel Utilisateur", width=480, height=480)

        ctk.CTkLabel(modal.body, text="Identifiant de connexion *", font=FONTS["caption_bold"]).pack(anchor="w", pady=(0, 2))
        u_entry = ctk.CTkEntry(modal.body, height=36, font=FONTS["body"])
        u_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(modal.body, text="Nom Complet *", font=FONTS["caption_bold"]).pack(anchor="w", pady=(0, 2))
        n_entry = ctk.CTkEntry(modal.body, height=36, font=FONTS["body"])
        n_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(modal.body, text="Mot de passe *", font=FONTS["caption_bold"]).pack(anchor="w", pady=(0, 2))
        p_entry = ctk.CTkEntry(modal.body, height=36, show="•", font=FONTS["body"])
        p_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(modal.body, text="Rôle d'accès *", font=FONTS["caption_bold"]).pack(anchor="w", pady=(0, 2))
        r_menu = ctk.CTkOptionMenu(modal.body, values=["caissier", "admin"], height=36, font=FONTS["body"])
        r_menu.pack(fill="x", pady=(0, 15))

        def create():
            u = u_entry.get().strip()
            n = n_entry.get().strip()
            p = p_entry.get().strip()
            if not u or not n or not p:
                ToastNotification.show(modal, "Veuillez remplir tous les champs", "warning")
                return

            success, msg = AuthService.create_user(u, p, n, r_menu.get())
            if success:
                modal.destroy()
                ToastNotification.show(self, msg, "success")
                self.load_users()
            else:
                ToastNotification.show(modal, msg, "danger")

        ctk.CTkButton(modal.body, text="CRÉER LE COMPTE", height=42, font=FONTS["body_bold"], fg_color=COLORS["primary"], command=create).pack(fill="x", side="bottom")

    def _open_edit_user_modal(self, user: dict):
        modal = BaseModal(self.winfo_toplevel(), f"Modifier l'Utilisateur : {user['username']}", width=480, height=540)

        ctk.CTkLabel(modal.body, text="Identifiant de connexion *", font=FONTS["caption_bold"]).pack(anchor="w", pady=(0, 2))
        u_entry = ctk.CTkEntry(modal.body, height=36, font=FONTS["body"])
        u_entry.pack(fill="x", pady=(0, 10))
        u_entry.insert(0, user.get("username", ""))

        ctk.CTkLabel(modal.body, text="Nom Complet *", font=FONTS["caption_bold"]).pack(anchor="w", pady=(0, 2))
        n_entry = ctk.CTkEntry(modal.body, height=36, font=FONTS["body"])
        n_entry.pack(fill="x", pady=(0, 10))
        n_entry.insert(0, user.get("full_name", ""))

        ctk.CTkLabel(modal.body, text="Rôle d'accès *", font=FONTS["caption_bold"]).pack(anchor="w", pady=(0, 2))
        r_menu = ctk.CTkOptionMenu(modal.body, values=["caissier", "admin"], height=36, font=FONTS["body"])
        r_menu.pack(fill="x", pady=(0, 10))
        r_menu.set(user.get("role", "caissier"))

        ctk.CTkLabel(modal.body, text="Statut du Compte *", font=FONTS["caption_bold"]).pack(anchor="w", pady=(0, 2))
        st_menu = ctk.CTkOptionMenu(modal.body, values=["Actif", "Désactivé"], height=36, font=FONTS["body"])
        st_menu.pack(fill="x", pady=(0, 10))
        st_menu.set("Actif" if user.get("is_active") else "Désactivé")

        ctk.CTkLabel(
            modal.body,
            text="Nouveau mot de passe (optionnel) :",
            font=FONTS["caption_bold"]
        ).pack(anchor="w", pady=(0, 2))
        p_entry = ctk.CTkEntry(
            modal.body,
            height=36,
            show="•",
            font=FONTS["body"],
            placeholder_text="Laisser vide pour ne pas modifier"
        )
        p_entry.pack(fill="x", pady=(0, 15))

        def save_changes():
            u = u_entry.get().strip()
            n = n_entry.get().strip()
            p = p_entry.get().strip()
            role = r_menu.get()
            is_active = (st_menu.get() == "Actif")

            if not u or not n:
                ToastNotification.show(modal, "L'identifiant et le nom complet sont obligatoires", "warning")
                return

            success, msg = AuthService.update_user(
                user_id=user["id"],
                username=u,
                full_name=n,
                role=role,
                password=p if p else None,
                is_active=is_active
            )

            if success:
                modal.destroy()
                ToastNotification.show(self, msg, "success")
                self.load_users()
            else:
                ToastNotification.show(modal, msg, "danger")

        ctk.CTkButton(
            modal.body,
            text="💾 ENREGISTRER LES MODIFICATIONS",
            height=42,
            font=FONTS["body_bold"],
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            command=save_changes
        ).pack(fill="x", side="bottom")

    def _delete_user_confirm(self, user: dict):
        # Vérification préventive pour éviter suppression de son propre compte
        curr_u = AuthService.get_current_user()
        if curr_u and curr_u.id == user["id"]:
            ToastNotification.show(self, "❌ Impossible de supprimer votre propre compte actif !", "danger")
            return

        modal = BaseModal(self.winfo_toplevel(), "Confirmation de Suppression", width=440, height=240)

        msg_box = ctk.CTkFrame(modal.body, fg_color="transparent")
        msg_box.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            msg_box,
            text=f"⚠️ Êtes-vous sûr de vouloir supprimer définitivement le compte :\n\n👤 {user['username']} ({user['full_name']}) ?",
            font=FONTS["body_bold"],
            text_color=("#0F172A", "#F8FAFC"),
            justify="center",
            wraplength=380
        ).pack(pady=(10, 15))

        btn_row = ctk.CTkFrame(modal.body, fg_color="transparent")
        btn_row.pack(fill="x", side="bottom", pady=(0, 5))
        btn_row.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_row,
            text="Annuler",
            height=38,
            font=FONTS["body"],
            fg_color=("gray80", "#334155"),
            text_color=("#0F172A", "#F8FAFC"),
            hover_color=("gray70", "#475569"),
            command=modal.destroy
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        def do_delete():
            success, msg = AuthService.delete_user(user["id"])
            modal.destroy()
            if success:
                ToastNotification.show(self, msg, "success")
                self.load_users()
            else:
                ToastNotification.show(self, msg, "danger")

        ctk.CTkButton(
            btn_row,
            text="🗑️ Supprimer Définitivement",
            height=38,
            font=FONTS["body_bold"],
            fg_color=COLORS["danger"],
            hover_color=COLORS["danger_hover"],
            command=do_delete
        ).grid(row=0, column=1, padx=(6, 0), sticky="ew")


    # ---------------- 4. APPARENCE & THÈME ----------------
    def _setup_theme_tab(self):
        box = ctk.CTkFrame(self.tab_theme, corner_radius=12, fg_color=("#F8FAFC", "#0F172A"), border_width=1, border_color=("#E2E8F0", "#334155"))
        box.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(box, text="Personnalisation de l'Interface Utilisateur", font=FONTS["title_small"], text_color=COLORS["primary"]).pack(anchor="w", padx=20, pady=(15, 10))

        ctk.CTkLabel(box, text="Mode d'affichage (Thème) :", font=FONTS["caption_bold"]).pack(anchor="w", padx=20, pady=(0, 4))
        
        current_mode = ctk.get_appearance_mode()
        self.theme_menu = ctk.CTkOptionMenu(
            box,
            values=["Dark", "Light"],
            height=36,
            font=FONTS["body"],
            command=self._change_theme
        )
        self.theme_menu.pack(fill="x", padx=20, pady=(0, 20))
        self.theme_menu.set(current_mode)

    def _change_theme(self, new_mode):
        ctk.set_appearance_mode(new_mode)
        if self.on_theme_change:
            self.on_theme_change(new_mode)
        ToastNotification.show(self, f"Thème {new_mode} activé", "info")
