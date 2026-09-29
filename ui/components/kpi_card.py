import customtkinter as ctk
from ui.theme import FONTS, COLORS

# Commerce Storefront KPI Card – Warm Stone palette, mono prices
_CARD_BG_DARK  = "#27272A"   # Zinc-800
_CARD_BDR_DARK = "#3F3F46"   # Zinc-700
_ICON_BG_DARK  = "#18181B"   # Zinc-950
_CARD_BG_LIGHT = "#FFFFFF"
_CARD_BDR_LT   = "#E6DFD7"   # Warm Stone border
_ICON_BG_LT    = "#F5EFEB"   # Warm Cream


class KPICard(ctk.CTkFrame):
    def __init__(self, parent, title: str, value: str, subtitle: str = "",
                 icon_text: str = "📊", accent_color: str = "#D9480F", **kwargs):
        super().__init__(
            parent,
            corner_radius=14,
            fg_color=(_CARD_BG_LIGHT, _CARD_BG_DARK),
            border_width=1,
            border_color=(_CARD_BDR_LT, _CARD_BDR_DARK),
            **kwargs
        )
        self.accent_color = accent_color

        # ── Orange top accent bar ─────────────────────────────────────────────
        top_bar = ctk.CTkFrame(self, height=3, corner_radius=0, fg_color=accent_color)
        top_bar.pack(fill="x", side="top")

        # ── Content container (packed into self, uses grid internally) ────────
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=12, pady=10)

        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=1)

        # Icon box
        self.icon_frame = ctk.CTkFrame(
            content,
            width=48,
            height=48,
            corner_radius=12,
            fg_color=(_ICON_BG_LT, _ICON_BG_DARK)
        )
        self.icon_frame.grid(row=0, column=0, rowspan=3, padx=(0, 12), pady=(0, 0), sticky="w")
        self.icon_frame.grid_propagate(False)

        self.icon_label = ctk.CTkLabel(
            self.icon_frame,
            text=icon_text,
            font=("Segoe UI", 20),
            text_color=accent_color
        )
        self.icon_label.place(relx=0.5, rely=0.5, anchor="center")

        # Title
        self.title_label = ctk.CTkLabel(
            content,
            text=title.upper(),
            font=("Segoe UI", 10, "bold"),
            text_color=("#78716C", "#71717A"),
            anchor="w"
        )
        self.title_label.grid(row=0, column=1, sticky="w", padx=(0, 0), pady=(0, 1))

        # Value (monospace price style)
        self.value_label = ctk.CTkLabel(
            content,
            text=value,
            font=("Consolas", 20, "bold"),
            text_color=("#1C1917", "#FAFAFA"),
            anchor="w"
        )
        self.value_label.grid(row=1, column=1, sticky="w", padx=(0, 0), pady=(0, 1))

        # Subtitle / trend
        self.sub_label = ctk.CTkLabel(
            content,
            text=subtitle,
            font=("Segoe UI", 10),
            text_color=("#78716C", "#71717A"),
            anchor="w"
        )
        self.sub_label.grid(row=2, column=1, sticky="w", padx=(0, 0), pady=(0, 0))

    def update_value(self, value: str, subtitle: str = ""):
        self.value_label.configure(text=value)
        if subtitle:
            self.sub_label.configure(text=subtitle)

    def update_accent(self, accent_color: str):
        self.accent_color = accent_color
        self.icon_label.configure(text_color=accent_color)

