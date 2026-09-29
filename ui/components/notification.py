import customtkinter as ctk
from ui.theme import FONTS, COLORS

class ToastNotification:
    @staticmethod
    def show(parent, message: str, type_: str = "success", duration_ms: int = 3500):
        """
        Affiche un toast élégant dans le coin inférieur droit de la fenêtre.
        type_: 'success', 'warning', 'danger', 'info'
        """
        color_map = {
            "success": (COLORS["success"], "✓"),
            "warning": (COLORS["warning"], "⚠"),
            "danger": (COLORS["danger"], "✕"),
            "info": (COLORS["info"], "ℹ")
        }
        accent, icon_str = color_map.get(type_, (COLORS["info"], "ℹ"))

        toast = ctk.CTkFrame(
            parent,
            corner_radius=10,
            fg_color=("#1E293B", "#1E293B"),
            border_width=1,
            border_color=accent
        )
        toast.place(relx=0.98, rely=0.95, anchor="se")

        # Icon
        icon_lbl = ctk.CTkLabel(
            toast,
            text=icon_str,
            font=FONTS["title_small"],
            text_color=accent
        )
        icon_lbl.pack(side="left", padx=(14, 8), pady=10)

        # Message
        msg_lbl = ctk.CTkLabel(
            toast,
            text=message,
            font=FONTS["body_bold"],
            text_color="#F8FAFC"
        )
        msg_lbl.pack(side="left", padx=(0, 16), pady=10)

        # Disparaît automatiquement
        parent.after(duration_ms, lambda: toast.destroy() if toast.winfo_exists() else None)
