import sqlite3
import shutil
import hashlib
import threading
import logging
from pathlib import Path
from datetime import datetime
from config import PRIMARY_DB_PATH, SECONDARY_DRIVE, SECONDARY_DB_DIR, SECONDARY_DB_PATH

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("DB_MANAGER")

_db_lock = threading.Lock()

class DatabaseManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.primary_path = PRIMARY_DB_PATH
        self.secondary_path = SECONDARY_DB_PATH
        self.secondary_available = False
        self._check_secondary_drive()
        self.init_db()
        self._initialized = True

    def _check_secondary_drive(self):
        """Vérifie si le lecteur D: existe et prépare le répertoire de secours."""
        try:
            if SECONDARY_DRIVE.exists():
                SECONDARY_DB_DIR.mkdir(parents=True, exist_ok=True)
                self.secondary_available = True
                logger.info(f"Lecteur secondaire D: détecté. Chemin backup : {self.secondary_path}")
            else:
                self.secondary_available = False
                logger.warning("Lecteur secondaire D: non disponible. Mode simple partition C: actif.")
        except Exception as e:
            self.secondary_available = False
            logger.warning(f"Erreur lors de la vérification de la partition D: {e}")

    def get_connection(self):
        """Retourne une connexion à la base principale SQLite optimisée basse consommation / Windows 7."""
        conn = sqlite3.connect(self.primary_path, timeout=20.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA cache_size = -8000;")
        conn.execute("PRAGMA temp_store = MEMORY;")
        conn.execute("PRAGMA mmap_size = 30000000;")
        return conn

    def init_db(self):
        """Initialise la base de données avec toutes les tables nécessaires et index optimisés Windows 7."""
        with _db_lock:
            self.primary_path.parent.mkdir(parents=True, exist_ok=True)
            
            is_new = not self.primary_path.exists() or self.primary_path.stat().st_size == 0
            
            if is_new and self.secondary_available and self.secondary_path.exists() and self.secondary_path.stat().st_size > 0:
                logger.info("Restauration de la base de données depuis la partition de secours D:...")
                try:
                    shutil.copy2(self.secondary_path, self.primary_path)
                    is_new = False
                except Exception as e:
                    logger.error(f"Échec de la restauration depuis D: {e}")

            conn = self.get_connection()
            cursor = conn.cursor()

            # 1. Table Utilisateurs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('admin', 'caissier')),
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 2. Table Fournisseurs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS suppliers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    contact_person TEXT,
                    phone TEXT,
                    email TEXT,
                    address TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 3. Table Produits
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    barcode TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    brand TEXT,
                    category TEXT NOT NULL,
                    purchase_price REAL NOT NULL DEFAULT 0.0,
                    sale_price REAL NOT NULL DEFAULT 0.0,
                    vat_rate REAL DEFAULT 0.0,
                    stock_qty INTEGER NOT NULL DEFAULT 0,
                    min_stock_alert INTEGER DEFAULT 5,
                    expiry_date DATE,
                    supplier_id INTEGER,
                    is_active INTEGER DEFAULT 1,
                    created_via_po_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL,
                    FOREIGN KEY (created_via_po_id) REFERENCES purchase_orders(id) ON DELETE SET NULL
                );
            """)

            # 4. Table Mouvements de Stock
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_movements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    movement_type TEXT NOT NULL CHECK(movement_type IN ('reception', 'vente', 'ajustement', 'inventaire', 'perte_casse')),
                    qty INTEGER NOT NULL,
                    old_stock INTEGER NOT NULL,
                    new_stock INTEGER NOT NULL,
                    unit_price REAL,
                    reason TEXT,
                    user_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                );
            """)

            # 5. Table Sessions de Caisse
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cash_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    opening_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closing_date TIMESTAMP,
                    opening_amount REAL NOT NULL DEFAULT 0.0,
                    theoretical_cash REAL DEFAULT 0.0,
                    real_cash REAL DEFAULT 0.0,
                    cash_difference REAL DEFAULT 0.0,
                    total_sales_amount REAL DEFAULT 0.0,
                    total_sales_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'open' CHECK(status IN ('open', 'closed')),
                    notes TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );
            """)

            # 6. Table Ventes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_code TEXT UNIQUE NOT NULL,
                    session_id INTEGER,
                    user_id INTEGER NOT NULL,
                    total_ht REAL NOT NULL DEFAULT 0.0,
                    total_tva REAL NOT NULL DEFAULT 0.0,
                    discount_amount REAL NOT NULL DEFAULT 0.0,
                    total_ttc REAL NOT NULL DEFAULT 0.0,
                    payment_method TEXT DEFAULT 'especes' CHECK(payment_method IN ('especes', 'carte', 'autre')),
                    amount_received REAL NOT NULL DEFAULT 0.0,
                    change_given REAL NOT NULL DEFAULT 0.0,
                    customer_name TEXT DEFAULT 'Client Passant',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES cash_sessions(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );
            """)

            # 7. Table Lignes de Vente
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sale_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    product_name TEXT NOT NULL,
                    barcode TEXT,
                    unit_price REAL NOT NULL,
                    purchase_price REAL NOT NULL,
                    qty INTEGER NOT NULL,
                    discount_pct REAL DEFAULT 0.0,
                    total_line REAL NOT NULL,
                    FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES products(id)
                );
            """)

            # 8. Table Bons de Commande Fournisseur
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS purchase_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_code TEXT UNIQUE NOT NULL,
                    supplier_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'en_attente',
                    total_amount REAL DEFAULT 0.0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    received_at TIMESTAMP,
                    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
                );
            """)

            # 9. Table Lignes de Bons de Commande
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS purchase_order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    product_id INTEGER,
                    product_name TEXT,
                    barcode TEXT,
                    qty_ordered INTEGER NOT NULL,
                    qty_received INTEGER DEFAULT 0,
                    unit_cost REAL NOT NULL,
                    total_cost REAL NOT NULL,
                    is_new_product INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'en_attente',
                    FOREIGN KEY (order_id) REFERENCES purchase_orders(id) ON DELETE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
                );
            """)

            # 10. Table Paramètres Généraux du Magasin
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
            """)

            # ── Migration défensive pour bases existantes ──────────────────────
            # 1. Vérifier si purchase_orders a un ancien CHECK restrictif
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='purchase_orders'")
            po_sql_row = cursor.fetchone()
            if po_sql_row and "CHECK" in po_sql_row[0]:
                try:
                    cursor.execute("PRAGMA foreign_keys=OFF;")
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS purchase_orders_migrated (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            order_code TEXT UNIQUE NOT NULL,
                            supplier_id INTEGER NOT NULL,
                            status TEXT DEFAULT 'en_attente',
                            total_amount REAL DEFAULT 0.0,
                            notes TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            received_at TIMESTAMP,
                            FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
                        );
                    """)
                    cursor.execute("""
                        INSERT OR IGNORE INTO purchase_orders_migrated (id, order_code, supplier_id, status, total_amount, notes, created_at, received_at)
                        SELECT id, order_code, supplier_id, status, total_amount, notes, created_at, received_at FROM purchase_orders;
                    """)
                    cursor.execute("DROP TABLE purchase_orders;")
                    cursor.execute("ALTER TABLE purchase_orders_migrated RENAME TO purchase_orders;")
                    cursor.execute("PRAGMA foreign_keys=ON;")
                    logger.info("Table purchase_orders migrée sans contrainte CHECK restrictive.")
                except Exception as e:
                    logger.warning(f"Erreur migration purchase_orders: {e}")

            # 2. Vérifier si purchase_order_items a product_id NOT NULL
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='purchase_order_items'")
            poi_sql_row = cursor.fetchone()
            if poi_sql_row and "product_id INTEGER NOT NULL" in poi_sql_row[0]:
                try:
                    cursor.execute("PRAGMA foreign_keys=OFF;")
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS purchase_order_items_migrated (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            order_id INTEGER NOT NULL,
                            product_id INTEGER,
                            product_name TEXT,
                            barcode TEXT,
                            qty_ordered INTEGER NOT NULL,
                            qty_received INTEGER DEFAULT 0,
                            unit_cost REAL NOT NULL,
                            total_cost REAL NOT NULL,
                            is_new_product INTEGER DEFAULT 0,
                            status TEXT DEFAULT 'en_attente',
                            FOREIGN KEY (order_id) REFERENCES purchase_orders(id) ON DELETE CASCADE,
                            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
                        );
                    """)
                    cursor.execute("""
                        INSERT OR IGNORE INTO purchase_order_items_migrated (id, order_id, product_id, qty_ordered, qty_received, unit_cost, total_cost)
                        SELECT id, order_id, product_id, qty_ordered, qty_received, unit_cost, total_cost FROM purchase_order_items;
                    """)
                    cursor.execute("DROP TABLE purchase_order_items;")
                    cursor.execute("ALTER TABLE purchase_order_items_migrated RENAME TO purchase_order_items;")
                    cursor.execute("PRAGMA foreign_keys=ON;")
                    logger.info("Table purchase_order_items migrée avec product_id NULLable.")
                except Exception as e:
                    logger.warning(f"Erreur migration purchase_order_items: {e}")

            # Vérifier colonnes products
            cursor.execute("PRAGMA table_info(products)")
            prod_cols = [r[1] for r in cursor.fetchall()]
            if "created_via_po_id" not in prod_cols:
                try:
                    cursor.execute("ALTER TABLE products ADD COLUMN created_via_po_id INTEGER;")
                except Exception as e:
                    logger.debug(f"Migration products.created_via_po_id : {e}")

            # Vérifier colonnes purchase_order_items
            cursor.execute("PRAGMA table_info(purchase_order_items)")
            poi_cols = [r[1] for r in cursor.fetchall()]
            if "product_name" not in poi_cols:
                try:
                    cursor.execute("ALTER TABLE purchase_order_items ADD COLUMN product_name TEXT;")
                except Exception:
                    pass
            if "barcode" not in poi_cols:
                try:
                    cursor.execute("ALTER TABLE purchase_order_items ADD COLUMN barcode TEXT;")
                except Exception:
                    pass
            if "is_new_product" not in poi_cols:
                try:
                    cursor.execute("ALTER TABLE purchase_order_items ADD COLUMN is_new_product INTEGER DEFAULT 0;")
                except Exception:
                    pass
            if "status" not in poi_cols:
                try:
                    cursor.execute("ALTER TABLE purchase_order_items ADD COLUMN status TEXT DEFAULT 'en_attente';")
                except Exception:
                    pass

            # ── Indexation SQLite optimisée Windows 7 (recherche instantanée) ──
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode);",
                "CREATE INDEX IF NOT EXISTS idx_products_supplier ON products(supplier_id);",
                "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);",
                "CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);",
                "CREATE INDEX IF NOT EXISTS idx_products_created_po ON products(created_via_po_id);",
                "CREATE INDEX IF NOT EXISTS idx_stock_movements_product ON stock_movements(product_id);",
                "CREATE INDEX IF NOT EXISTS idx_stock_movements_type ON stock_movements(movement_type);",
                "CREATE INDEX IF NOT EXISTS idx_po_supplier ON purchase_orders(supplier_id);",
                "CREATE INDEX IF NOT EXISTS idx_po_status ON purchase_orders(status);",
                "CREATE INDEX IF NOT EXISTS idx_po_code ON purchase_orders(order_code);",
                "CREATE INDEX IF NOT EXISTS idx_poi_order ON purchase_order_items(order_id);",
                "CREATE INDEX IF NOT EXISTS idx_poi_product ON purchase_order_items(product_id);",
            ]
            for idx_sql in indexes:
                try:
                    cursor.execute(idx_sql)
                except Exception as e:
                    logger.debug(f"Index creation ({idx_sql}): {e}")

            conn.commit()

            if is_new:
                self._insert_seed_data(cursor, conn)
            else:
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM products")
                product_count = cursor.fetchone()[0]
                if user_count == 0 or product_count == 0:
                    logger.warning("Base de données vide détectée. Réinitialisation...")
                    self._insert_seed_data(cursor, conn)

            conn.close()
            self.sync_to_secondary()

    def _insert_seed_data(self, cursor, conn):
        """Insère les données de base : Comptes par défaut et catalogue cosmétique."""
        logger.info("Insertion des données initiales...")
        admin_pwd = hashlib.sha256("admin123".encode("utf-8")).hexdigest()
        cashier_pwd = hashlib.sha256("1234".encode("utf-8")).hexdigest()

        cursor.execute("INSERT OR IGNORE INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
                       ("admin", admin_pwd, "Administrateur", "admin"))
        cursor.execute("INSERT OR IGNORE INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
                       ("caissier", cashier_pwd, "Sarah Caisse", "caissier"))

        default_settings = [
            ("store_name", "Élégance & Beauté Cosmétique"),
            ("store_phone", "0550 12 34 56"),
            ("store_address", "12 Boulevard Didouche Mourad, Alger"),
            ("store_nif", "001234567890123"),
            ("ticket_footer", "Merci de votre visite ! Produits ni repris ni échangés après 48h."),
            ("printer_type", "simulation"),
            ("currency", "DA")
        ]
        for k, v in default_settings:
            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

        suppliers = [
            ("L'Oréal Algérie Distribution", "Karim Benali", "0555 10 20 30", "contact@loreal-dz.com", "Zone Industrielle Oued Smar, Alger"),
            ("Venus Cosmétiques DZ", "Amina Mansouri", "0560 40 50 60", "commercial@venus.dz", "Rouiba, Alger"),
            ("Nivea & Beiersdorf Import", "Sofiane Brahimi", "0770 90 80 70", "ventes@beiersdorf.dz", "Bab Ezzouar, Alger"),
            ("Parfums & Luxe International", "Yacine Cherif", "0661 22 33 44", "luxeparfums@gmail.com", "Hydra, Alger")
        ]
        for s in suppliers:
            cursor.execute("INSERT INTO suppliers (name, contact_person, phone, email, address) VALUES (?, ?, ?, ?, ?)", s)

        products = [
            ("6131112220011", "Sérum Anti-Âge Acide Hyaluronique 30ml", "L'Oréal Paris", "Soins Visage", 1800.0, 2600.0, 18, 5, "2027-12-31", 1),
            ("6131112220028", "Crème Hydratante Éclat du Jour 50ml", "Venus", "Soins Visage", 450.0, 750.0, 25, 6, "2027-08-15", 2),
            ("6131112220035", "Rouge à Lèvres Mat Infaillible #105", "L'Oréal Paris", "Maquillage", 1200.0, 1850.0, 12, 4, "2028-01-10", 1),
            ("6131112220042", "Mascara Volume Extra Noir Lash Sensational", "Maybelline", "Maquillage", 1100.0, 1700.0, 15, 5, "2027-06-30", 1),
            ("6131112220059", "Fond de Teint Fluide Accord Parfait Beige Doré", "L'Oréal Paris", "Maquillage", 1600.0, 2400.0, 8, 4, "2027-11-20", 1),
            ("6131112220066", "Eau de Parfum La Nuit Trésor 50ml", "Lancôme", "Parfumerie & Eaux de Toilette", 9500.0, 14500.0, 4, 2, "2029-05-18", 4),
            ("6131112220073", "Eau de Toilette Sauvage Homme 100ml", "Dior", "Parfumerie & Eaux de Toilette", 12500.0, 18900.0, 3, 2, "2029-04-12", 4),
            ("6131112220080", "Shampoing Réparateur Argan & Kératine 400ml", "Venus", "Soins Capillaires & Shampoings", 380.0, 600.0, 30, 8, "2028-03-01", 2),
            ("6131112220097", "Masque Cheveux Nourrissant Huile Extraordinaire", "Elsève", "Soins Capillaires & Shampoings", 750.0, 1150.0, 14, 5, "2027-09-14", 1),
            ("6131112220103", "Lait Corporel Nourrissant Peaux Sèches 400ml", "Nivea", "Soins Corps & Bain", 680.0, 1050.0, 20, 6, "2027-10-05", 3),
            ("6131112220110", "Déodorant Bille Invisible Black & White 50ml", "Nivea", "Hygiène & Déodorants", 320.0, 520.0, 28, 8, "2028-02-28", 3),
            ("6131112220127", "Vernis à Ongles Gel Tenue 7 Jours Rouge Carmin", "Essie", "Vernis & Onglerie", 650.0, 990.0, 16, 5, "2028-05-30", 1),
            ("6131112220134", "Pinceau Poudre Professionnel Poils Doux", "Real Techniques", "Accessoires & Pinceaux", 950.0, 1500.0, 10, 3, None, 4),
            ("6131112220141", "Crème Solaire Haute Protection SPF 50+ 50ml", "La Roche-Posay", "Solaire & Autobronzants", 2200.0, 3200.0, 6, 4, "2026-11-30", 4),
            ("6131112220158", "Eau Micellaire Démaquillante Peaux Sensibles 400ml", "Garnier", "Soins Visage", 650.0, 980.0, 22, 6, "2027-07-20", 1),
            ("6131112220165", "Chocolat Noir 72% Cacao 100g", "Lindt", "Produits Alimentaires", 380.0, 550.0, 20, 5, "2027-04-15", 3),
            ("6131112220172", "Boisson Énergétique Bio Citron Gingembre 250ml", "VitaminWell", "Boissons & Snacking", 250.0, 390.0, 24, 6, "2026-12-31", 3),
            ("6131112220189", "Gélules Collagène & Vitamine C (60 gélules)", "NutriBeauté", "Compléments Alimentaires & Diététique", 1600.0, 2450.0, 15, 4, "2028-02-15", 1)
        ]

        for p in products:
            cursor.execute("""
                INSERT INTO products (barcode, name, brand, category, purchase_price, sale_price, stock_qty, min_stock_alert, expiry_date, supplier_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, p)
            product_id = cursor.lastrowid
            cursor.execute("""
                INSERT INTO stock_movements (product_id, movement_type, qty, old_stock, new_stock, unit_price, reason, user_id)
                VALUES (?, 'reception', ?, 0, ?, ?, 'Stock Initial', 1)
            """, (product_id, p[6], p[6], p[4]))

        conn.commit()

    def sync_to_secondary(self):
        """Synchronise la base principale C: vers la partition de secours D:."""
        if not self.secondary_available:
            self._check_secondary_drive()
            if not self.secondary_available:
                return False

        try:
            with _db_lock:
                if self.primary_path.exists():
                    shutil.copy2(self.primary_path, self.secondary_path)
                    logger.info(f"Synchronisation réussie vers {self.secondary_path}")
                    return True
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation vers D: {e}")
            return False

    def execute_query(self, query, params=(), commit=False):
        """Exécute une requête SQL de manière thread-safe."""
        with _db_lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(query, params)
                if commit:
                    conn.commit()
                    result = cursor.lastrowid
                else:
                    result = cursor.fetchall()
                return result
            except Exception as e:
                if commit:
                    conn.rollback()
                logger.error(f"Erreur SQL sur la requête '{query}': {e}")
                raise e
            finally:
                conn.close()
                if commit:
                    threading.Thread(target=self.sync_to_secondary, daemon=True).start()

    def execute_script(self, script_text):
        """Exécute un script SQL complet."""
        with _db_lock:
            conn = self.get_connection()
            try:
                conn.executescript(script_text)
                conn.commit()
            finally:
                conn.close()
                threading.Thread(target=self.sync_to_secondary, daemon=True).start()

def get_db():
    return DatabaseManager()
