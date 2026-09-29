import customtkinter as ctk
from ui.theme import FONTS, COLORS

# Commerce Storefront palette constants for modal
_MODAL_BG_DARK  = "#18181B"   # Zinc-900
_MODAL_HDR_DARK = "#27272A"   # Zinc-800
_MODAL_BDR      = "#3F3F46"   # Zinc-700 border
_MODAL_ACCENT   = "#D9480F"   # Burnt Orange


class BaseModal(ctk.CTkToplevel):
    def __init__(self, parent, title: str, width: int = 500, height: int = 400):
        super().__init__(parent)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.resizable(True, True)
        self.transient(parent.winfo_toplevel() if hasattr(parent, 'winfo_toplevel') else parent)
        self.grab_set()

        # ── Center on parent ──────────────────────────────────────────────────
        try:
            parent.update_idletasks()
            top = parent.winfo_toplevel()
            px = top.winfo_rootx() + (top.winfo_width() - width) // 2
            py = top.winfo_rooty() + (top.winfo_height() - height) // 2
            self.geometry(f"+{max(0, px)}+{max(0, py)}")
        except Exception:
            pass

        # ── Background ────────────────────────────────────────────────────────
        self.configure(fg_color=("#FAF7F4", _MODAL_BG_DARK))

        # ── Header bar ────────────────────────────────────────────────────────
        self.header_frame = ctk.CTkFrame(
            self,
            fg_color=(_MODAL_HDR_DARK, _MODAL_HDR_DARK),
            height=52, corner_radius=0
        )
        self.header_frame.pack(fill="x", side="top")
        self.header_frame.pack_propagate(False)

        # Orange accent stripe on left
        ctk.CTkFrame(
            self.header_frame, width=3, corner_radius=0,
            fg_color=_MODAL_ACCENT
        ).pack(side="left", fill="y")

        self.title_lbl = ctk.CTkLabel(
            self.header_frame,
            text=title,
            font=("Segoe UI", 13, "bold"),
            text_color=("#FAFAFA", "#FAFAFA")
        )
        self.title_lbl.pack(side="left", padx=16, pady=14)

        self.close_btn = ctk.CTkButton(
            self.header_frame,
            text="✕",
            width=34,
            height=34,
            font=("Segoe UI", 14, "bold"),
            fg_color="transparent",
            text_color=("#71717A", "#71717A"),
            hover_color=("#3F3F46", "#3F3F46"),
            command=self.destroy
        )
        self.close_btn.pack(side="right", padx=10, pady=9)

        # ── Content container ─────────────────────────────────────────────────
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=18, pady=14)
