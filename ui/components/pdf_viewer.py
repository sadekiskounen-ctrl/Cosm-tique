# In-App PDF Viewer Modal Component
import os
import io
import shutil
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from PIL import Image, ImageTk

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None

from ui.theme import COLORS, FONTS
from ui.components.modal import BaseModal
from ui.components.notification import ToastNotification


class PdfViewerModal(BaseModal):
    """
    Visionneuse PDF intégrée haute résolution dans l'application.
    Permet de visualiser, zoomer, naviguer dans les pages, défiler horizontalement
    et verticalement (barres de défilement 2D, molette + Shift, glisser-déposer), imprimer et exporter.
    """
    def __init__(self, parent, pdf_path: str, title: str = "Aperçu Document PDF"):
        super().__init__(parent, f"📄 {title}", width=980, height=800)
        self.pdf_path = pdf_path
        self.doc = None
        self.current_page = 0
        self.total_pages = 0
        self.zoom_level = 1.0  # 100%
        self.photo_image = None
        self._drag_start_x = 0
        self._drag_start_y = 0

        self.transient(parent.winfo_toplevel() if hasattr(parent, 'winfo_toplevel') else parent)

        # ── TOOLBAR SUPÉRIEURE ───────────────────────────────────────────────
        self.toolbar = ctk.CTkFrame(
            self.body,
            fg_color=("white", COLORS["bg_card_dark"]),
            corner_radius=10,
            border_width=1,
            border_color=(COLORS["border_light"], COLORS["border_dark"])
        )
        self.toolbar.pack(fill="x", pady=(0, 10))

        tb_inner = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        tb_inner.pack(fill="x", padx=12, pady=8)

        # ── Navigation Pages (Gauche) ──
        nav_frame = ctk.CTkFrame(tb_inner, fg_color="transparent")
        nav_frame.pack(side="left")

        self.btn_prev = ctk.CTkButton(
            nav_frame, text="◀ Précédent", width=90, height=32,
            font=FONTS["caption_bold"], fg_color=("gray90", COLORS["border_dark"]),
            text_color=COLORS["text_dark"], hover_color=("gray80", "#4B5563"),
            command=self.prev_page
        )
        self.btn_prev.pack(side="left", padx=(0, 6))

        self.page_lbl = ctk.CTkLabel(
            nav_frame, text="Page 1 / 1", font=FONTS["body_bold"],
            text_color=COLORS["primary"], width=100
        )
        self.page_lbl.pack(side="left", padx=4)

        self.btn_next = ctk.CTkButton(
            nav_frame, text="Suivant ▶", width=90, height=32,
            font=FONTS["caption_bold"], fg_color=("gray90", COLORS["border_dark"]),
            text_color=COLORS["text_dark"], hover_color=("gray80", "#4B5563"),
            command=self.next_page
        )
        self.btn_next.pack(side="left", padx=(6, 12))

        # ── Zoom Controls (Centre) ──
        zoom_frame = ctk.CTkFrame(tb_inner, fg_color="transparent")
        zoom_frame.pack(side="left", padx=10)

        ctk.CTkButton(
            zoom_frame, text="🔍 −", width=36, height=32,
            font=FONTS["caption_bold"], fg_color=("gray90", COLORS["border_dark"]),
            text_color=COLORS["text_dark"], hover_color=("gray80", "#4B5563"),
            command=self.zoom_out
        ).pack(side="left", padx=2)

        self.zoom_lbl = ctk.CTkLabel(zoom_frame, text="100%", font=FONTS["caption_bold"], width=50)
        self.zoom_lbl.pack(side="left", padx=2)

        ctk.CTkButton(
            zoom_frame, text="🔍 +", width=36, height=32,
            font=FONTS["caption_bold"], fg_color=("gray90", COLORS["border_dark"]),
            text_color=COLORS["text_dark"], hover_color=("gray80", "#4B5563"),
            command=self.zoom_in
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            zoom_frame, text="Ajuster Largeur", width=105, height=32,
            font=FONTS["caption_bold"], fg_color=("gray90", COLORS["border_dark"]),
            text_color=COLORS["text_dark"], hover_color=("gray80", "#4B5563"),
            command=self.zoom_fit
        ).pack(side="left", padx=(6, 0))

        # ── Actions Droite (Imprimer, Télécharger) ──
        act_frame = ctk.CTkFrame(tb_inner, fg_color="transparent")
        act_frame.pack(side="right")

        ctk.CTkButton(
            act_frame, text="🖨️ Imprimer", height=34,
            font=FONTS["caption_bold"], fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            command=self.print_pdf
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            act_frame, text="💾 Enregistrer sous...", height=34,
            font=FONTS["caption_bold"], fg_color=COLORS["secondary"],
            hover_color=COLORS["secondary_hover"],
            command=self.save_as_pdf
        ).pack(side="left", padx=(0, 8))

        # ── ZONE D'AFFICHAGE DU DOCUMENT AVEC SCROLLBARS 2D (HAUT/BAS & GAUCHE/DROITE) ──
        self.viewer_container = ctk.CTkFrame(
            self.body,
            fg_color=("#E2E8F0", "#0B0F19"),
            corner_radius=10,
            border_width=1,
            border_color=(COLORS["border_light"], COLORS["border_dark"])
        )
        self.viewer_container.pack(fill="both", expand=True)
        self.viewer_container.grid_rowconfigure(0, weight=1)
        self.viewer_container.grid_columnconfigure(0, weight=1)

        is_dark = ctk.get_appearance_mode() == "Dark"
        canvas_bg = "#0B0F19" if is_dark else "#E2E8F0"

        self.canvas = tk.Canvas(
            self.viewer_container,
            bg=canvas_bg,
            highlightthickness=0,
            bd=0
        )
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=(3, 0), pady=(3, 0))

        self.v_scrollbar = ctk.CTkScrollbar(
            self.viewer_container,
            orientation="vertical",
            command=self.canvas.yview
        )
        self.v_scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 3), pady=(3, 0))

        self.h_scrollbar = ctk.CTkScrollbar(
            self.viewer_container,
            orientation="horizontal",
            command=self.canvas.xview
        )
        self.h_scrollbar.grid(row=1, column=0, sticky="ew", padx=(3, 0), pady=(0, 3))

        self.canvas.configure(
            xscrollcommand=self.h_scrollbar.set,
            yscrollcommand=self.v_scrollbar.set
        )

        # Bindings navigation et glisser-déposer
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Shift-MouseWheel>", self._on_shift_mousewheel)
        self.canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.canvas.bind("<B1-Motion>", self._on_drag_motion)
        self.canvas.bind("<ButtonPress-2>", self._on_drag_start)
        self.canvas.bind("<B2-Motion>", self._on_drag_motion)
        self.canvas.bind("<Configure>", lambda e: self._on_canvas_resize())

        # Charger le document
        self.load_pdf()

    def _on_mousewheel(self, event):
        if event.state & 0x0001:  # Shift enfoncé -> scroll horizontal
            self.canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_shift_mousewheel(self, event):
        self.canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_drag_start(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def _on_drag_motion(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def _on_canvas_resize(self):
        # Réajuste l'affichage lors du redimensionnement si nécessaire
        if self.photo_image:
            self._update_canvas_view()

    def load_pdf(self):
        if not os.path.exists(self.pdf_path):
            self.canvas.delete("all")
            self.canvas.create_text(
                300, 200,
                text=f"❌ Fichier PDF introuvable :\n{self.pdf_path}",
                fill="#EF4444", font=("Arial", 12, "bold"), justify="center"
            )
            return

        if fitz is None:
            self.canvas.delete("all")
            self.canvas.create_text(
                300, 200,
                text="⚠️ PyMuPDF n'est pas disponible pour le rendu interne.\nUtilisez 'Enregistrer sous' ou ouvrez avec votre lecteur PDF externe.",
                fill="#F59E0B", font=("Arial", 11, "bold"), justify="center"
            )
            return

        try:
            self.doc = fitz.open(self.pdf_path)
            self.total_pages = len(self.doc)
            self.current_page = 0
            self.render_page()
        except Exception as ex:
            self.canvas.delete("all")
            self.canvas.create_text(
                300, 200,
                text=f"❌ Erreur lors du chargement du PDF :\n{ex}",
                fill="#EF4444", font=("Arial", 11, "bold"), justify="center"
            )

    def render_page(self):
        if not self.doc or self.total_pages == 0:
            return

        dpi = int(140 * self.zoom_level)
        try:
            page = self.doc[self.current_page]
            pix = page.get_pixmap(dpi=dpi)
            img_data = pix.tobytes("png")
            pil_image = Image.open(io.BytesIO(img_data))

            self.photo_image = ImageTk.PhotoImage(pil_image)
            self._img_width = pil_image.width
            self._img_height = pil_image.height

            self._update_canvas_view()

            self.page_lbl.configure(text=f"Page {self.current_page + 1} / {self.total_pages}")
            self.zoom_lbl.configure(text=f"{int(self.zoom_level * 100)}%")

            self.btn_prev.configure(state="normal" if self.current_page > 0 else "disabled")
            self.btn_next.configure(state="normal" if self.current_page < self.total_pages - 1 else "disabled")
        except Exception as ex:
            self.canvas.delete("all")
            self.canvas.create_text(
                300, 200,
                text=f"❌ Erreur rendu page :\n{ex}",
                fill="#EF4444", font=("Arial", 10), justify="center"
            )

    def _update_canvas_view(self):
        if not self.photo_image:
            return
        self.canvas.delete("all")

        canvas_w = max(self.canvas.winfo_width(), 100)
        canvas_h = max(self.canvas.winfo_height(), 100)

        # Calcul de la marge pour centrer si l'image est plus petite que la fenêtre
        pad_x = max(16, (canvas_w - self._img_width) // 2)
        pad_y = max(16, (canvas_h - self._img_height) // 2 if self._img_height < canvas_h else 16)

        self.canvas.create_image(pad_x, pad_y, anchor="nw", image=self.photo_image)

        total_w = max(canvas_w, self._img_width + pad_x * 2)
        total_h = max(canvas_h, self._img_height + pad_y * 2)
        self.canvas.config(scrollregion=(0, 0, total_w, total_h))

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.render_page()

    def next_page(self):
        if self.doc and self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.render_page()

    def zoom_in(self):
        if self.zoom_level < 3.0:
            self.zoom_level += 0.2
            self.render_page()

    def zoom_out(self):
        if self.zoom_level > 0.4:
            self.zoom_level -= 0.2
            self.render_page()

    def zoom_fit(self):
        if self.doc and self.total_pages > 0:
            try:
                page = self.doc[self.current_page]
                # Page width in points (72 dpi)
                p_width = page.rect.width
                canvas_w = self.canvas.winfo_width()
                if canvas_w > 150 and p_width > 0:
                    # Target dpi to fit canvas width with 40px margin
                    target_width = canvas_w - 50
                    # Standard 140 dpi baseline = 1.0 zoom (72 points -> 140 px = ~1.944 scale)
                    needed_zoom = target_width / (p_width * (140.0 / 72.0))
                    self.zoom_level = max(0.5, min(2.5, round(needed_zoom, 2)))
                else:
                    self.zoom_level = 1.0
            except Exception:
                self.zoom_level = 1.0
        else:
            self.zoom_level = 1.0
        self.render_page()

    def print_pdf(self):
        try:
            if os.name == 'nt':
                os.startfile(self.pdf_path, "print")
                ToastNotification.show(self, "🖨️ Document envoyé à l'imprimante...", "info")
            else:
                os.system(f"lpr '{self.pdf_path}'")
                ToastNotification.show(self, "🖨️ Impression lancée...", "info")
        except Exception as ex:
            ToastNotification.show(self, f"Erreur d'impression : {ex}", "danger")

    def save_as_pdf(self):
        dest = filedialog.asksaveasfilename(
            parent=self,
            title="Enregistrer une copie du PDF",
            defaultextension=".pdf",
            initialfile=os.path.basename(self.pdf_path),
            filetypes=[("Documents PDF", "*.pdf"), ("Tous les fichiers", "*.*")]
        )
        if dest:
            try:
                shutil.copy2(self.pdf_path, dest)
                ToastNotification.show(self, f"✅ PDF enregistré sous :\n{dest}", "success")
            except Exception as ex:
                ToastNotification.show(self, f"Erreur de sauvegarde : {ex}", "danger")

    def destroy(self):
        if self.doc:
            try:
                self.doc.close()
            except Exception:
                pass
        super().destroy()
