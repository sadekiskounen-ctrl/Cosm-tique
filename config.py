import os
import sys
from pathlib import Path

# Application Metadata
APP_NAME = "CosmétiquePro - Gestion & Caisse"
APP_VERSION = "2.0.0"
APP_AUTHOR = "Cosmetique Solutions Algérie"
CURRENCY = "DA"  # Dinar Algérien

# Base paths
IS_FROZEN = getattr(sys, 'frozen', False)
if IS_FROZEN:
    APP_DIR = Path(sys.executable).parent
else:
    APP_DIR = Path(__file__).parent.resolve()

ASSETS_DIR = APP_DIR / "assets"
REPORTS_DIR = APP_DIR / "reports"
EXPORTS_DIR = APP_DIR / "exports"

# Create required local folders
for folder in [ASSETS_DIR, REPORTS_DIR, EXPORTS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# Database Redundancy Configuration (C: and D: partitions)
# Primary location: C:\CosmetiqueApp\data.db or fallback in AppData if no root write access
PRIMARY_DB_DIR = Path("C:/CosmetiqueApp")
try:
    PRIMARY_DB_DIR.mkdir(parents=True, exist_ok=True)
    PRIMARY_DB_PATH = PRIMARY_DB_DIR / "cosmetique.db"
except Exception:
    app_data = Path(os.environ.get("APPDATA", str(APP_DIR))) / "CosmetiqueApp"
    app_data.mkdir(parents=True, exist_ok=True)
    PRIMARY_DB_PATH = app_data / "cosmetique.db"

# Secondary redundant location: D:\CosmetiqueApp\data.db
SECONDARY_DRIVE = Path("D:/")
SECONDARY_DB_DIR = Path("D:/CosmetiqueApp")
SECONDARY_DB_PATH = SECONDARY_DB_DIR / "cosmetique_backup.db"

# Barcode Types
BARCODE_FORMATS = ["EAN13", "CODE128"]

# Product Categories
CATEGORIES = [
    "Produits Alimentaires",
    "Boissons & Snacking",
    "Compléments Alimentaires & Diététique",
    "Confiserie & Chocolats",
    "Soins Visage",
    "Maquillage",
    "Parfumerie & Eaux de Toilette",
    "Soins Capillaires & Shampoings",
    "Soins Corps & Bain",
    "Hygiène & Déodorants",
    "Vernis & Onglerie",
    "Accessoires & Pinceaux",
    "Bébé & Maternité",
    "Solaire & Autobronzants"
]

# Theme Colors (Modern Glass/Dark & Light Luxury Palette)
THEME = {
    "dark": {
        "bg_primary": "#0F172A",       # Slate 900
        "bg_secondary": "#1E293B",     # Slate 800
        "bg_card": "#1E293B",          # Card background
        "bg_hover": "#334155",         # Slate 700
        "sidebar_bg": "#0B1120",       # Darkest slate
        "text_primary": "#F8FAFC",     # Bright white
        "text_secondary": "#94A3B8",   # Slate 400
        "text_muted": "#64748B",       # Slate 500
        "accent": "#EC4899",           # Rose 500 (Cosmetic luxury touch)
        "accent_hover": "#DB2777",     # Rose 600
        "accent_gradient": ("#EC4899", "#8B5CF6"), # Rose to Violet
        "emerald": "#10B981",          # Success / Sales
        "emerald_hover": "#059669",
        "amber": "#F59E0B",            # Warning / Low stock
        "rose": "#EF4444",             # Danger / Rupture / Expired
        "cyan": "#06B6D4",             # Info
        "border": "#334155",
        "table_row_alt": "#1A2333"
    },
    "light": {
        "bg_primary": "#F8FAFC",       # Slate 50
        "bg_secondary": "#FFFFFF",     # Pure White
        "bg_card": "#FFFFFF",
        "bg_hover": "#F1F5F9",         # Slate 100
        "sidebar_bg": "#0F172A",       # Dark Slate sidebar
        "text_primary": "#0F172A",     # Slate 900
        "text_secondary": "#475569",   # Slate 600
        "text_muted": "#94A3B8",       # Slate 400
        "accent": "#EC4899",           # Luxury Rose
        "accent_hover": "#DB2777",
        "accent_gradient": ("#EC4899", "#8B5CF6"),
        "emerald": "#10B981",
        "emerald_hover": "#059669",
        "amber": "#F59E0B",
        "rose": "#EF4444",
        "cyan": "#0891B2",
        "border": "#E2E8F0",
        "table_row_alt": "#F8FAFC"
    }
}
