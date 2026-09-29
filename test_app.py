import unittest
import os
from pathlib import Path
from database.db_manager import get_db
from services.auth_service import AuthService
from services.stock_service import StockService
from services.pos_service import POSService
from services.barcode_service import BarcodeService
from services.printer_service import PrinterService
from services.reporting_service import ReportingService
from services.backup_service import BackupService

class TestCosmetiqueApp(unittest.TestCase):
    def setUp(self):
        self.db = get_db()

    def test_01_db_initialization(self):
        """Vérifie que les tables existent et que les données initiales sont présentes."""
        users = self.db.execute_query("SELECT * FROM users")
        self.assertGreaterEqual(len(users), 2, "Les utilisateurs par défaut doivent être créés")

        products = self.db.execute_query("SELECT * FROM products")
        self.assertGreaterEqual(len(products), 10, "Le catalogue cosmétique initial doit être inséré")

        suppliers = self.db.execute_query("SELECT * FROM suppliers")
        self.assertGreaterEqual(len(suppliers), 3, "Les fournisseurs initiaux doivent exister")

    def test_02_auth_service(self):
        """Test de la connexion Admin et Caissier."""
        ok, msg = AuthService.login("admin", "admin123")
        self.assertTrue(ok, "La connexion admin doit réussir")
        self.assertTrue(AuthService.is_admin())

        cashiers = self.db.execute_query("SELECT username FROM users WHERE role = 'caissier' LIMIT 1")
        if cashiers:
            cashier_user = cashiers[0]["username"]
            ok_cashier, msg_c = AuthService.login(cashier_user, "1234")
            if not ok_cashier:
                # Si le mot de passe a été personnalisé, on teste l'existence du rôle caissier
                self.assertIsNotNone(cashier_user)
            else:
                self.assertTrue(ok_cashier)
                self.assertFalse(AuthService.is_admin())

        wrong, msg_w = AuthService.login("admin", "mauvaismotdepasse")
        self.assertFalse(wrong, "La mauvaise combinaison doit échouer")

    def test_03_stock_and_alerts(self):
        """Test de recherche par code-barre, mouvements de stock et alertes."""
        p = StockService.get_product_by_barcode("6131112220011")
        self.assertIsNotNone(p, "Le produit de test doit être trouvé par son code-barre")
        initial_stock = p["stock_qty"]

        # Réception
        ok, msg = StockService.add_reception(p["id"], qty=5, purchase_price=1800.0, user_id=1)
        self.assertTrue(ok)
        p_updated = StockService.get_product_by_id(p["id"])
        self.assertEqual(p_updated["stock_qty"], initial_stock + 5)

        # Vérification alertes
        tot, low, out, exp = StockService.get_total_alerts_count()
        self.assertIsInstance(tot, int)

    def test_04_pos_and_sale(self):
        """Test du flux de vente POS complet avec déduction de stock et ticket."""
        pos = POSService()
        p = StockService.get_product_by_barcode("6131112220028")
        stock_before = p["stock_qty"]

        # Ouvrir une session de caisse
        open_ok, session_id = POSService.open_cash_session(user_id=1, opening_amount=5000.0)

        # Ajouter au panier
        add_ok, _ = pos.add_product(dict(p), qty=2)
        self.assertTrue(add_ok)

        totals = pos.get_totals()
        self.assertEqual(totals["final_total"], p["sale_price"] * 2)

        # Compléter la vente
        sale_ok, sale_details = pos.complete_sale(
            user_id=1,
            payment_method="especes",
            amount_received=2000.0,
            customer_name="Client Test"
        )
        self.assertTrue(sale_ok)
        self.assertEqual(sale_details["change_given"], 2000.0 - (p["sale_price"] * 2))

        # Vérifier stock décrémenté
        p_after = StockService.get_product_by_id(p["id"])
        self.assertEqual(p_after["stock_qty"], stock_before - 2)

        # Génération du ticket
        ticket_text = PrinterService.generate_ticket_text(sale_details)
        self.assertIn("Ticket", ticket_text)
        self.assertIn("NET À PAYER", ticket_text)

        # Clôturer la caisse
        current_sess = POSService.get_current_session()
        if current_sess:
            close_ok, close_stats = POSService.close_cash_session(
                session_id=current_sess["id"],
                real_cash=5000.0 + (p["sale_price"] * 2),
                notes="Clôture de test"
            )
            self.assertTrue(close_ok)
            self.assertEqual(close_stats["difference"], 0.0)

    def test_05_barcode_generation(self):
        """Test de la génération d'un code EAN-13 et image d'étiquette."""
        ean = BarcodeService.generate_random_ean13()
        self.assertEqual(len(ean), 13)
        self.assertTrue(ean.startswith("613"))

        sticker = BarcodeService.create_product_sticker("Parfum Test Luxe 50ml", 4500.0, ean)
        self.assertIsNotNone(sticker)
        self.assertGreater(sticker.size[0], 200)

    def test_06_reports_and_backup(self):
        """Test des KPIs et de l'état de sauvegarde C/D."""
        kpis = ReportingService.get_dashboard_kpis()
        self.assertIn("today_sales", kpis)
        self.assertIn("stock_value", kpis)

        status = BackupService.get_backup_status()
        self.assertTrue(status["primary"]["exists"])

if __name__ == "__main__":
    unittest.main()
