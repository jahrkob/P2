import customtkinter as ctk


class OverviewPage(ctk.CTkFrame):
    def __init__(self, parent, on_graph_request=None):
        super().__init__(parent)

        self.on_graph_request = on_graph_request

        self.container = ctk.CTkFrame(self, fg_color="#101317")
        self.container.pack(fill="both", expand=True, padx=10, pady=10)

        header = ctk.CTkFrame(self.container, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 4))

        ctk.CTkLabel(header, text="AMR Overview", font=("Arial", 26, "bold")).pack(anchor="w")

        self.scroll_area = ctk.CTkScrollableFrame(self.container, fg_color="transparent")
        self.scroll_area.pack(fill="both", expand=True, padx=6, pady=(0, 10))

        self.empty_label = ctk.CTkLabel(
            self.scroll_area,
            text="No AMRs available",
            font=("Arial", 16),
            text_color="#b0b6bd"
        )
        self.empty_label.pack(pady=40)

        self.card_widgets = []

    def _status_style(self, status):
        status_text = str(status or "").upper()
        if status_text == "ONLINE":
            return "#1f8f4c", "#184f2f", "#c9f7db", "#2ecc71"
        if status_text == "CRITICAL":
            return "#c94f4f", "#6f2323", "#ffe1e1", "#ff5e5e"
        return "#70757d", "#494c52", "#e4e7ea", "#9aa0a6"

    def _connection_state(self, status):
        status_text = str(status or "").upper()
        return "offline" if status_text == "OFFLINE" else "online"

    def _metric_style(self, value, status, lower_is_better=True, threshold=None):
        status_text = str(status or "").upper()
        if status_text == "OFFLINE":
            return "#5d6066", "#d1d4d8", "#8a8f96"

        value_num = None
        try:
            value_num = float(value)
        except (TypeError, ValueError):
            return "#5d6066", "#d1d4d8", "#8a8f96"

        if threshold is None:
            threshold = 0

        good = value_num <= threshold if lower_is_better else value_num >= threshold
        if good:
            return "#1f8f4c", "#dff6e7", "#2ecc71"
        return "#c94f4f", "#ffe1e1", "#ff5e5e"

    def _clear_cards(self):
        for widget in self.card_widgets:
            widget.destroy()
        self.card_widgets = []

    def _open_graph(self, amr_ip):
        if self.on_graph_request is not None:
            self.on_graph_request(amr_ip)

    def _create_metric_box(self, parent, label, value, status, threshold, unit="", lower_is_better=True):
        bg_color, text_color, accent = self._metric_style(value, status, lower_is_better=lower_is_better, threshold=threshold)
        box = ctk.CTkFrame(parent, fg_color=bg_color, corner_radius=12)
        box.grid_propagate(False)
        box.configure(width=105, height=64)

        ctk.CTkLabel(box, text=label, font=("Arial", 12, "bold"), text_color=text_color).pack(pady=(8, 0))
        display_value = "-" if value in (None, "", "-") else f"{value}{unit}"
        ctk.CTkLabel(box, text=display_value, font=("Arial", 16, "bold"), text_color=text_color).pack(pady=(1, 0))
        ctk.CTkProgressBar(box, height=8, progress_color=accent, fg_color="#3a3f45").pack(fill="x", padx=12, pady=(4, 8))
        try:
            value_num = float(value)
            progress = max(0.0, min(1.0, 1.0 - (value_num / (threshold * 2 if threshold else 100.0)))) if lower_is_better else max(0.0, min(1.0, value_num / (threshold * 2 if threshold else 100.0)))
            box.winfo_children()[-1].set(progress)
        except (TypeError, ValueError):
            box.winfo_children()[-1].set(0)
        return box

    def _create_card(self, amr):
        status = amr.get("status", "OFFLINE")
        badge_fg, badge_border, badge_text, dot = self._status_style(status)
        amr_ip = str(amr.get("ip") or amr.get("amr_ip") or "")
        amr_name = amr.get("name") or amr_ip or "?"
        if isinstance(amr_name, str) and amr_name.upper().startswith("AMR #"):
            amr_title = amr_name
        else:
            amr_title = f"AMR #{amr_name}"

        card = ctk.CTkFrame(self.scroll_area, fg_color="#171b20", corner_radius=18, border_width=1, border_color=badge_border)
        card.pack(fill="x", padx=8, pady=8)

        top_row = ctk.CTkFrame(card, fg_color="transparent")
        top_row.pack(fill="x", padx=16, pady=(14, 6))

        ctk.CTkLabel(
            top_row,
            text=str(status).upper(),
            font=("Arial", 16, "bold"),
            text_color=badge_text,
            fg_color=badge_fg,
            corner_radius=10,
            padx=18,
            pady=8,
        ).pack(side="left")

        ctk.CTkLabel(
            top_row,
            text=amr_title,
            font=("Arial", 18),
            text_color="#e7eaee"
        ).pack(side="left", padx=16)

        connection_state = self._connection_state(status)
        connection_dot = "#2ecc71" if connection_state == "online" else "#9aa0a6"
        status_row = ctk.CTkFrame(top_row, fg_color="transparent")
        status_row.pack(side="right")
        ctk.CTkLabel(status_row, text="●", font=("Arial", 20, "bold"), text_color=connection_dot).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(status_row, text=connection_state, font=("Arial", 15, "bold"), text_color="#d7dbe0").pack(side="left")

        if amr_ip:
            ctk.CTkLabel(card, text=f"IP: {amr_ip}", font=("Arial", 12), text_color="#99a2ad").pack(anchor="w", padx=18, pady=(0, 6))

        metric_row = ctk.CTkFrame(card, fg_color="transparent")
        metric_row.pack(fill="x", padx=16, pady=(6, 10))
        metric_row.grid_columnconfigure((0, 1, 2), weight=1)

        ping_box = self._create_metric_box(metric_row, "ping", amr.get("ping", "-"), status, 50, unit="", lower_is_better=True)
        loss_box = self._create_metric_box(metric_row, "loss", amr.get("loss", "-"), status, 5, unit="", lower_is_better=True)
        jitter_box = self._create_metric_box(metric_row, "jitter", amr.get("jitter", "-"), status, 10, unit="", lower_is_better=True)

        ping_box.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        loss_box.grid(row=0, column=1, padx=8, sticky="ew")
        jitter_box.grid(row=0, column=2, padx=(8, 0), sticky="ew")

        bottom_row = ctk.CTkFrame(card, fg_color="transparent")
        bottom_row.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkButton(
            bottom_row,
            text="Open graph",
            width=140,
            height=38,
            fg_color="#2d6cdf",
            hover_color="#2458b7",
            command=lambda ip=amr_ip: self._open_graph(ip) if ip else None,
        ).pack(side="right")

        return card

    def update_amrs(self, amrs):
        self._clear_cards()

        if not amrs:
            self.empty_label.pack(pady=40)
            return

        self.empty_label.pack_forget()

        for amr in amrs:
            card = self._create_card(amr)
            self.card_widgets.append(card)