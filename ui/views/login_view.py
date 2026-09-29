import customtkinter as ctk
from ui.theme import FONTS, COLORS
from services.auth_service import AuthService
from ui.components.notification import ToastNotification


class LoginView(ctk.CTkFrame):
    """
    Écran de connexion moderne, épuré et sécurisé pour CosmétiquePro.
    Champs vides par défaut, bascule visibilité mot de passe, navigation fluide.
    """
    def __init__(self, parent, on_login_success):
        super().__init__(parent, fg_color=("#F1F5F9", "#0B1120"))
        self.on_login_success = on_login_success
        self.pwd_visible = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── CARTE CENTRALE DE CONNEXION ──────────────────────────────────────
        self.card = ctk.CTkFrame(
            self,
            width=420,
            height=520,
            corner_radius=20,
            fg_color=("#FFFFFF", "#1E293B"),
            border_width=1,
            border_color=("#E2E8F0", "#334155")
        )
        self.card.grid(row=0, column=0, padx=20, pady=20)
        self.card.grid_propagate(False)

        # ── BADGE & LOGO DE MARQUE ───────────────────────────────────────────
        self.brand_box = ctk.CTkFrame(self.card, fg_color="transparent")
        self.brand_box.pack(pady=(35, 20))

        self.icon_badge = ctk.CTkFrame(
            self.brand_box,
            width=64,
            height=64,
            corner_radius=18,
            fg_color=COLORS["primary"]
        )
        self.icon_badge.pack(pady=(0, 12))
        self.icon_badge.pack_propagate(False)

        self.icon_lbl = ctk.CTkLabel(
            self.icon_badge,
            text="✨",
            font=(FONTS["title_large"][0], 28)
        )
        self.icon_lbl.place(relx=0.5, rely=0.5, anchor="center")

        self.title_lbl = ctk.CTkLabel(
            self.brand_box,
            text="COSMÉTIQUE PRO",
            font=FONTS["title_large"],
            text_color=("#0F172A", "#F8FAFC")
        )
        self.title_lbl.pack(pady=(0, 2))

        self.subtitle_lbl = ctk.CTkLabel(
            self.brand_box,
            text="Gestion Commerciale & Point de Vente",
            font=FONTS["caption"],
            text_color=("#64748B", "#94A3B8")
        )
        self.subtitle_lbl.pack()

        # ── FORMULAIRE DE SAISIE ─────────────────────────────────────────────
        form_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        form_frame.pack(fill="x", padx=36)

        # 1. Identifiant
        ctk.CTkLabel(
            form_frame,
            text="👤 Identifiant :",
            font=FONTS["caption_bold"],
            text_color=("#475569", "#94A3B8")
        ).pack(anchor="w", pady=(0, 4))

        self.username_entry = ctk.CTkEntry(
            form_frame,
            height=44,
            placeholder_text="Entrez votre identifiant...",
            font=FONTS["body"],
            corner_radius=10,
            border_width=1.5,
            border_color=("#CBD5E1", "#334155"),
            fg_color=("#F8FAFC", "#0F172A")
        )
        self.username_entry.pack(fill="x", pady=(0, 16))
        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus_set())

        # 2. Mot de passe
        ctk.CTkLabel(
            form_frame,
            text="🔒 Mot de passe :",
            font=FONTS["caption_bold"],
            text_color=("#475569", "#94A3B8")
        ).pack(anchor="w", pady=(0, 4))

        pwd_container = ctk.CTkFrame(form_frame, fg_color="transparent")
        pwd_container.pack(fill="x", pady=(0, 22))

        self.password_entry = ctk.CTkEntry(
            pwd_container,
            height=44,
            show="•",
            placeholder_text="Entrez votre mot de passe...",
            font=FONTS["body"],
            corner_radius=10,
            border_width=1.5,
            border_color=("#CBD5E1", "#334155"),
            fg_color=("#F8FAFC", "#0F172A")
        )
        self.password_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.password_entry.bind("<Return>", lambda e: self._attempt_login())

        # Bouton Afficher / Masquer le mot de passe
        self.toggle_pwd_btn = ctk.CTkButton(
            pwd_container,
            text="👁️",
            width=44,
            height=44,
            font=("Segoe UI Emoji", 14),
            fg_color=("#E2E8F0", "#334155"),
            hover_color=("#CBD5E1", "#475569"),
            text_color=("#0F172A", "#F8FAFC"),
            corner_radius=10,
            command=self._toggle_password_visibility
        )
        self.toggle_pwd_btn.pack(side="right")

        # 3. Bouton Connexion
        self.login_btn = ctk.CTkButton(
            form_frame,
            text="SE CONNECTER ➔",
            height=46,
            font=FONTS["body_bold"],
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            corner_radius=10,
            command=self._attempt_login
        )
        self.login_btn.pack(fill="x")

        # Focus initial automatique sur l'identifiant
        self.username_entry.focus_set()

    def _toggle_password_visibility(self):
        self.pwd_visible = not self.pwd_visible
        if self.pwd_visible:
            self.password_entry.configure(show="")
            self.toggle_pwd_btn.configure(text="🙈")
        else:
            self.password_entry.configure(show="•")
            self.toggle_pwd_btn.configure(text="👁️")

    def _attempt_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            ToastNotification.show(self, "Veuillez saisir votre identifiant et mot de passe", "warning")
            if not username:
                self.username_entry.focus_set()
            else:
                self.password_entry.focus_set()
            return

        success, msg = AuthService.login(username, password)
        if success:
            user = AuthService.get_current_user()
            ToastNotification.show(self.master, f"Bienvenue, {user.full_name} !", "success")
            self.on_login_success(user)
        else:
            ToastNotification.show(self, msg, "danger")
            self.password_entry.delete(0, "end")
            self.password_entry.focus_set()
