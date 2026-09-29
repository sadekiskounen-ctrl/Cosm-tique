import os
import subprocess
import datetime
from pathlib import Path
from database.db_manager import get_db
from config import REPORTS_DIR

class PrinterService:
    @staticmethod
    def get_store_info():
        db = get_db()
        rows = db.execute_query("SELECT key, value FROM settings")
        settings = {r["key"]: r["value"] for r in rows}
        return {
            "name": settings.get("store_name", "Élégance & Beauté Cosmétique"),
            "phone": settings.get("store_phone", "0550 12 34 56"),
            "address": settings.get("store_address", "Alger, Algérie"),
            "nif": settings.get("store_nif", "001234567890123"),
            "footer": settings.get("ticket_footer", "Merci pour votre fidélité !"),
            "printer_type": settings.get("printer_type", "simulation")
        }

    @staticmethod
    def generate_ticket_text(sale_data):
        """Génère le texte formaté 48/80 colonnes pour ticket thermique."""
        store = PrinterService.get_store_info()
        lines = []
        width = 40

        lines.append("=" * width)
        lines.append(store["name"].center(width))
        lines.append(store["address"].center(width))
        lines.append(f"Tél : {store['phone']}".center(width))
        if store["nif"]:
            lines.append(f"NIF : {store['nif']}".center(width))
        lines.append("=" * width)
        
        lines.append(f"Ticket : {sale_data.get('sale_code', 'N/A')}")
        lines.append(f"Date   : {sale_data.get('date', datetime.datetime.now().strftime('%d/%m/%Y %H:%M'))}")
        lines.append(f"Client : {sale_data.get('customer_name', 'Client Passant')}")
        lines.append("-" * width)
        
        # Header articles
        lines.append(f"{'Désignation':<20}{'Qté':>4}{'P.U':>8}{'Total':>8}")
        lines.append("-" * width)

        for item in sale_data.get("cart", []):
            name = item["product"]["name"][:19]
            qty = item["qty"]
            pu = f"{item['unit_price']:.0f}"
            tot = f"{item['total']:.0f}"
            lines.append(f"{name:<20}{qty:>4}{pu:>8}{tot:>8}")
            if item.get("discount_pct", 0) > 0:
                lines.append(f"  (Remise {item['discount_pct']}%)")

        lines.append("-" * width)
        totals = sale_data.get("totals", {})
        lines.append(f"{'Total Brut :':<28}{totals.get('subtotal', 0):>10.2f} DA")
        if totals.get("discount_amount", 0) > 0:
            lines.append(f"{'Remise Totale :':<28}-{totals.get('discount_amount', 0):>9.2f} DA")
        lines.append("=" * width)
        lines.append(f"{'NET À PAYER :':<25}{totals.get('final_total', 0):>13.2f} DA")
        lines.append("=" * width)

        lines.append(f"Paiement : {sale_data.get('payment_method', 'Espèces').capitalize()}")
        if sale_data.get("payment_method") == "especes":
            lines.append(f"Reçu     : {sale_data.get('amount_received', 0):.2f} DA")
            lines.append(f"Rendu    : {sale_data.get('change_given', 0):.2f} DA")

        lines.append("-" * width)
        lines.append(store["footer"].center(width))
        lines.append("=" * width)
        lines.append("\n\n\n")

        return "\n".join(lines)

    @staticmethod
    def print_ticket(sale_data):
        """Imprime le ticket soit via ESC/POS physique, soit via spooler Windows, soit enregistre un fichier texte."""
        store = PrinterService.get_store_info()
        printer_type = store.get("printer_type", "simulation")
        ticket_text = PrinterService.generate_ticket_text(sale_data)

        # 1. Sauvegarder toujours une copie locale dans reports/tickets/
        tickets_dir = REPORTS_DIR / "tickets"
        tickets_dir.mkdir(parents=True, exist_ok=True)
        ticket_file = tickets_dir / f"{sale_data.get('sale_code', 'ticket')}.txt"
        with open(ticket_file, "w", encoding="utf-8") as f:
            f.write(ticket_text)

        # 2. Impression ESC/POS physique si configurée
        if printer_type == "escpos_usb":
            try:
                from escpos.printer import Usb
                # Vendor/Product ID par défaut ou configurable
                p = Usb(0x0416, 0x5011, profile="POS-5890")
                p.text(ticket_text)
                p.cut()
                return True, "Ticket imprimé sur imprimante thermique ESC/POS"
            except Exception as e:
                return True, f"Ticket généré (Imprimante USB hors ligne : {e})"
        
        return True, f"Ticket enregistré avec succès : {ticket_file.name}"
