import customtkinter as ctk
from ui.theme import FONTS, COLORS

class ModernTable(ctk.CTkFrame):
    def __init__(self, parent, columns: list[tuple[str, int, str]], on_row_click=None, row_height: int = 38, **kwargs):
        """
        columns: list of tuples (Column Title, weight/width, align 'w'/'e'/'center')
        """
        super().__init__(
            parent,
            corner_radius=10,
            fg_color=("#FFFFFF", "#1E293B"),
            border_width=1,
            border_color=("#E2E8F0", "#334155"),
            **kwargs
        )
        self.columns_info = columns
        self.on_row_click = on_row_click
        self.row_height = row_height
        self.rows_data = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 1. Header Frame
        self.header_frame = ctk.CTkFrame(
            self,
            corner_radius=8,
            fg_color=("#F1F5F9", "#0F172A"),
            height=38
        )
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=(8, 24), pady=(8, 4))
        self.header_frame.grid_propagate(False)

        for col_idx, (col_title, col_weight, align) in enumerate(self.columns_info):
            self.header_frame.grid_columnconfigure(col_idx, weight=col_weight, uniform="table_col")
            lbl = ctk.CTkLabel(
                self.header_frame,
                text=col_title.upper(),
                font=FONTS["caption_bold"],
                text_color=("#475569", "#94A3B8"),
                anchor=align
            )
            lbl.grid(row=0, column=col_idx, sticky="ew", padx=8, pady=8)

        # 2. Scrollable Body
        self.body_frame = ctk.CTkScrollableFrame(
            self,
            corner_radius=0,
            fg_color="transparent"
        )
        self.body_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self.body_frame.grid_columnconfigure(0, weight=1)

        # Dynamic header-body width synchronization on resize / scrollbar appearance
        self.body_frame.bind("<Configure>", self._sync_header_width)

        # Empty state label
        self.empty_label = None

    def _sync_header_width(self, event=None):
        try:
            if hasattr(self.body_frame, "_parent_canvas"):
                canvas_w = self.body_frame._parent_canvas.winfo_width()
                body_w = self.body_frame.winfo_width()
                if body_w > 0 and canvas_w > 0:
                    diff = max(16, body_w - canvas_w)
                    self.header_frame.grid_configure(padx=(8, 8 + diff))
        except Exception:
            pass

    def set_data(self, data_rows: list[list]):
        """
        data_rows: list of rows, where each row is a list of cell values (or CTk widgets / callables)
        """
        for widget in self.body_frame.winfo_children():
            widget.destroy()

        self.rows_data = data_rows

        if not data_rows:
            self.empty_label = ctk.CTkLabel(
                self.body_frame,
                text="Aucune donnée trouvée",
                font=FONTS["body"],
                text_color=("#94A3B8", "#64748B")
            )
            self.empty_label.grid(row=0, column=0, pady=40)
            return

        for row_idx, row in enumerate(data_rows):
            row_bg = ("#F8FAFC", "#1A2333") if row_idx % 2 == 1 else ("#FFFFFF", "#1E293B")
            
            row_frame = ctk.CTkFrame(
                self.body_frame,
                corner_radius=6,
                fg_color=row_bg,
                height=self.row_height
            )
            row_frame.grid(row=row_idx, column=0, sticky="ew", pady=1)
            row_frame.grid_propagate(False)

            for col_idx, (_, col_weight, align) in enumerate(self.columns_info):
                row_frame.grid_columnconfigure(col_idx, weight=col_weight, uniform="table_col")
                cell_value = row[col_idx] if col_idx < len(row) else ""

                if callable(cell_value):
                    widget = cell_value(row_frame)
                    if align == "center":
                        widget.grid(row=0, column=col_idx, padx=4, pady=2)
                    elif align == "w":
                        widget.grid(row=0, column=col_idx, padx=6, pady=2, sticky="w")
                    elif align == "e":
                        widget.grid(row=0, column=col_idx, padx=6, pady=2, sticky="e")
                    else:
                        widget.grid(row=0, column=col_idx, padx=4, pady=2, sticky="nsew")
                elif isinstance(cell_value, ctk.CTkBaseClass):
                    if align == "center":
                        cell_value.grid(row=0, column=col_idx, padx=4, pady=2)
                    elif align == "w":
                        cell_value.grid(row=0, column=col_idx, padx=6, pady=2, sticky="w")
                    elif align == "e":
                        cell_value.grid(row=0, column=col_idx, padx=6, pady=2, sticky="e")
                    else:
                        cell_value.grid(row=0, column=col_idx, padx=4, pady=2, sticky="nsew")
                else:
                    lbl = ctk.CTkLabel(
                        row_frame,
                        text=str(cell_value),
                        font=FONTS["body"],
                        text_color=("#0F172A", "#F8FAFC"),
                        anchor=align
                    )
                    lbl.grid(row=0, column=col_idx, sticky="ew", padx=8, pady=4)
                    
                    if self.on_row_click:
                        lbl.bind("<Button-1>", lambda e, r=row_idx: self.on_row_click(r))
            
            if self.on_row_click:
                row_frame.bind("<Button-1>", lambda e, r=row_idx: self.on_row_click(r))

