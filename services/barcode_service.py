import io
import os
import random
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import barcode
from barcode.writer import ImageWriter
from config import REPORTS_DIR


class BarcodeService:
    @staticmethod
    def generate_random_ean13():
        """Génère un code EAN-13 valide avec le préfixe 613 (Algérie)."""
        core = "613" + "".join([str(random.randint(0, 9)) for _ in range(9)])
        s = 0
        for i, char in enumerate(core):
            digit = int(char)
            s += digit * 3 if i % 2 == 1 else digit
        checksum = (10 - (s % 10)) % 10
        return core + str(checksum)

    @staticmethod
    def generate_barcode_image(code: str, format_type="ean13"):
        """Génère une image PIL du code-barres."""
        code = str(code).strip()
        writer = ImageWriter()
        writer.set_options({
            'module_width': 0.28,
            'module_height': 14.0,
            'font_size': 10,
            'text_distance': 5.0,
            'quiet_zone': 5.0
        })
        try:
            if len(code) == 13 and code.isdigit():
                ean = barcode.get("ean13", code, writer=writer)
            else:
                ean = barcode.get("code128", code, writer=writer)
            buffer = io.BytesIO()
            ean.write(buffer)
            buffer.seek(0)
            img = Image.open(buffer)
            return img
        except Exception:
            try:
                ean = barcode.get("code128", code, writer=writer)
                buffer = io.BytesIO()
                ean.write(buffer)
                buffer.seek(0)
                return Image.open(buffer)
            except Exception:
                img = Image.new('RGB', (250, 80), color='white')
                d = ImageDraw.Draw(img)
                d.text((10, 30), f"Code: {code}", fill='black')
                return img

    @staticmethod
    def create_product_sticker(product_name: str, price: float, barcode_str: str, currency="DA"):
        """Crée une étiquette premium avec code-barres visible + numéro."""
        barcode_img = BarcodeService.generate_barcode_image(barcode_str)

        # Dimensions étiquette 60mm x 40mm @ 200dpi => 472x315 px
        W, H = 480, 300
        label_img = Image.new("RGB", (W, H), color="white")
        draw = ImageDraw.Draw(label_img)

        # Fond dégradé léger (lignes horizontales)
        for y in range(H):
            gray = int(255 - (y / H) * 12)
            draw.line([(0, y), (W, y)], fill=(gray, gray, gray))

        # Bordure extérieure élégante
        draw.rectangle([(2, 2), (W - 3, H - 3)], outline="#1E293B", width=2)
        draw.rectangle([(5, 5), (W - 6, H - 6)], outline="#EC4899", width=1)

        # Bande colorée en haut
        draw.rectangle([(2, 2), (W - 3, 44)], fill="#1E293B")

        # Charger des polices (fallback si pas dispo)
        try:
            font_bold_lg = ImageFont.truetype("arialbd.ttf", 16)
            font_bold_md = ImageFont.truetype("arialbd.ttf", 24)
            font_bold_sm = ImageFont.truetype("arialbd.ttf", 13)
            font_reg_sm  = ImageFont.truetype("arial.ttf", 11)
        except Exception:
            font_bold_lg = ImageFont.load_default()
            font_bold_md = font_bold_lg
            font_bold_sm = font_bold_lg
            font_reg_sm  = font_bold_lg

        # Nom du produit sur fond foncé
        name_short = product_name[:32] + ("..." if len(product_name) > 32 else "")
        draw.text((W // 2, 23), name_short, fill="white", anchor="mm", font=font_bold_lg)

        # Prix en gros + rouge cosmétique
        price_text = f"{price:,.0f} {currency}".replace(",", " ")
        draw.text((W // 2, 72), price_text, fill="#EC4899", anchor="mm", font=font_bold_md)

        # Code-barres image
        bw, bh = barcode_img.size
        target_bw = min(400, W - 40)
        target_bh = int(bh * (target_bw / bw))
        if target_bh > 140:
            target_bh = 140
            target_bw = int(bw * (target_bh / bh))

        barcode_resized = barcode_img.resize((target_bw, target_bh), Image.Resampling.LANCZOS)
        bx = (W - target_bw) // 2
        by = 100
        label_img.paste(barcode_resized, (bx, by))

        # Numéro de code-barres en dessous (en gras)
        draw.text((W // 2, by + target_bh + 12), barcode_str, fill="#0F172A", anchor="mm", font=font_bold_sm)

        # Petit logo cosmétique en bas à droite
        draw.text((W - 12, H - 14), "CosmetiquePro", fill="#94A3B8", anchor="rm", font=font_reg_sm)

        return label_img

    @staticmethod
    def save_sticker_to_pdf(product_name: str, price: float, barcode_str: str):
        """Sauvegarde l'étiquette en PDF et retourne le chemin."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import mm
            from reportlab.platypus import SimpleDocTemplate, Image as RLImage, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.colors import HexColor
            from reportlab.lib.enums import TA_CENTER

            labels_dir = REPORTS_DIR / "etiquettes"
            labels_dir.mkdir(parents=True, exist_ok=True)

            pdf_path = labels_dir / f"etiquette_{barcode_str}.pdf"
            img_path = labels_dir / f"_tmp_{barcode_str}.png"

            # Générer l'image PNG d'abord
            img = BarcodeService.create_product_sticker(product_name, price, barcode_str)
            img.save(str(img_path))

            doc = SimpleDocTemplate(
                str(pdf_path),
                pagesize=A4,
                rightMargin=20*mm, leftMargin=20*mm,
                topMargin=25*mm, bottomMargin=25*mm
            )

            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'title', parent=styles['Normal'],
                fontSize=18, fontName='Helvetica-Bold',
                textColor=HexColor('#1E293B'), alignment=TA_CENTER, spaceAfter=8
            )
            sub_style = ParagraphStyle(
                'sub', parent=styles['Normal'],
                fontSize=13, fontName='Helvetica',
                textColor=HexColor('#64748B'), alignment=TA_CENTER, spaceAfter=20
            )
            price_style = ParagraphStyle(
                'price', parent=styles['Normal'],
                fontSize=22, fontName='Helvetica-Bold',
                textColor=HexColor('#EC4899'), alignment=TA_CENTER, spaceAfter=20
            )
            code_style = ParagraphStyle(
                'code', parent=styles['Normal'],
                fontSize=14, fontName='Helvetica-Bold',
                textColor=HexColor('#0F172A'), alignment=TA_CENTER, spaceAfter=10
            )
            footer_style = ParagraphStyle(
                'footer', parent=styles['Normal'],
                fontSize=9, fontName='Helvetica',
                textColor=HexColor('#94A3B8'), alignment=TA_CENTER
            )

            price_text = f"{price:,.0f} {chr(68)}{chr(65)}".replace(",", " ")

            story = [
                Spacer(1, 10*mm),
                Paragraph("\U0001f3f7\ufe0f \u00c9tiquette Produit", title_style),
                Paragraph(product_name, sub_style),
                Paragraph(price_text, price_style),
                RLImage(str(img_path), width=130*mm, height=50*mm),
                Spacer(1, 4*mm),
                Paragraph(barcode_str, code_style),
                Spacer(1, 15*mm),
                Paragraph("CosmetiquePro \u2014 Gestion Cosm\u00e9tique", footer_style),
            ]

            doc.build(story)
            # Supprimer l'image temporaire
            try:
                img_path.unlink()
            except Exception:
                pass

            return str(pdf_path)
        except ImportError:
            # Fallback: sauvegarder en PNG si reportlab absent
            return BarcodeService.save_sticker_to_file(product_name, price, barcode_str)

    @staticmethod
    def save_sticker_to_file(product_name: str, price: float, barcode_str: str):
        img = BarcodeService.create_product_sticker(product_name, price, barcode_str)
        labels_dir = REPORTS_DIR / "etiquettes"
        labels_dir.mkdir(parents=True, exist_ok=True)
        filename = labels_dir / f"etiquette_{barcode_str}.png"
        img.save(filename)
        return str(filename)

    @staticmethod
    def open_pdf_viewer(pdf_path: str):
        """Ouvre le PDF avec le lecteur PDF par défaut du système."""
        try:
            os.startfile(pdf_path)
            return True
        except Exception:
            try:
                subprocess.Popen(["start", "", pdf_path], shell=True)
                return True
            except Exception as e:
                return False
