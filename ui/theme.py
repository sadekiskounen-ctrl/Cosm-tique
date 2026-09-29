# Modern Sleek Color Theme Tokens — Commerce Storefront Design System
import customtkinter as ctk

FONT_FAMILY = "Segoe UI"
FONT_MONO = "Consolas"

FONTS = {
    "title_large": (FONT_FAMILY, 24, "bold"),
    "title_medium": (FONT_FAMILY, 18, "bold"),
    "title_small": (FONT_FAMILY, 15, "bold"),
    "body_bold": (FONT_FAMILY, 13, "bold"),
    "body": (FONT_FAMILY, 13),
    "caption": (FONT_FAMILY, 11),
    "caption_bold": (FONT_FAMILY, 11, "bold"),
    "kpi_value": (FONT_MONO, 22, "bold"),
    "mono": (FONT_MONO, 12),
    "price": (FONT_MONO, 14, "bold"),
    "price_large": (FONT_MONO, 20, "bold")
}

# ── COMMERCE STOREFRONT PALETTE ──────────────────────────────────────────────
# Primary: Burnt Orange (#D9480F) | Secondary: Berry (#E11D48) | Amber (#B45309)
# Base: Warm Cream (#FAF7F4) | Surface: Pure White (#FFFFFF)
COLORS = {
    # Dark Mode (Warm Stone / Charcoal)
    "bg_dark": "#18181B",          # Zinc 900
    "bg_card_dark": "#27272A",     # Zinc 800
    "bg_sidebar_dark": "#09090B",  # Deepest Stone/Zinc
    "bg_row_alt_dark": "#202023",  # Alternating row

    # Light Mode (Warm Cream / Crisp White)
    "bg_light": "#FAF7F4",         # Warm Cream Base
    "bg_card_light": "#FFFFFF",    # Pure Crisp White
    "bg_sidebar_light": "#1C1917", # Warm Stone Navy/Black
    "bg_row_alt_light": "#F5EFEB", # Light Cream Accent
    
    # Surfaces & Outlines
    "surface": "#FFFFFF",
    "surface_high": "#F0EBE6",
    "surface_highest": "#E6DFD7",
    "outline_hi": "#C9BEB2",

    # Typography Colors
    "text_white": "#FAFAF9",
    "text_dark": "#1C1917",
    "text_gray": "#A8A29E",
    "text_muted": "#78716C",
    "text_secondary": "#78716C",

    # Brand Colors (Storefront Burnt Orange)
    "primary": "#D9480F",          # Burnt Orange
    "primary_hover": "#EA580C",
    "primary_subtle": "#FFF7ED",
    "brand_orange": "#EA580C",

    # Secondary & Accent (Berry)
    "secondary": "#E11D48",        # Berry Accent
    "secondary_hover": "#BE123C",
    "secondary_subtle": "#FFF1F2",

    # Status / Functional Colors
    "success": "#15803D",          # Forest / Emerald Positive
    "success_hover": "#166534",
    "success_subtle": "#F0FDF4",
    "emerald": "#15803D",
    "emerald_hover": "#166534",
    "positive": "#15803D",

    "warning": "#B45309",          # Warm Amber
    "warning_hover": "#92400E",
    "warning_subtle": "#FFFBEB",
    "amber": "#B45309",
    "amber_hover": "#92400E",
    "tertiary": "#B45309",

    "danger": "#E11D48",           # Berry Red
    "danger_hover": "#BE123C",
    "danger_subtle": "#FFF1F2",
    "rose": "#E11D48",
    "rose_hover": "#BE123C",

    "info": "#0D9488",             # Teal Accent
    "info_hover": "#0F766E",
    "info_subtle": "#F0FDFA",
    "cyan": "#0D9488",
    "cyan_hover": "#0F766E",
    "quaternary": "#0D9488",

    # Borders & Cards
    "border_dark": "#3F3F46",
    "border_light": "#E6DFD7",
    "card_hover": "#3F3F46"
}
