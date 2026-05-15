import customtkinter as ctk
import sqlite3
import re
from pathlib import Path


class ErrorLogPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)

        ctk.CTkLabel(self, text="Error Log", font=("Arial", 20)).pack(pady=10)
        self.all_errors = []
        self.selected_filter = "All"

        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(filter_frame, text="Filter by IP:", font=("Arial", 12)).pack(side="left", padx=(0, 8))

        self.filter_combo = ctk.CTkComboBox(
            filter_frame,
            values=["All"],
            state="readonly",
            width=180,
            command=self._on_filter_change
        )
        self.filter_combo.set("All")
        self.filter_combo.pack(side="left")

        self.scroll_area = ctk.CTkScrollableFrame(self, width=800, height=500)
        self.scroll_area.pack(padx=10, pady=10, fill="both", expand=True)

        self.error_modal = None

        # Track last loaded row count
        self.last_count = 0

        try:
            self.load_errors()
        except Exception:
            self._show_empty_state()

    # =========================
    # DATABASE ACCESS
    def _on_filter_change(self, choice):
        """Handle filter selection change"""
        self.selected_filter = choice
        self._render_filtered_errors()

    def _render_filtered_errors(self):
        """Re-render errors based on current filter"""
        self._close_error_popup()

        if self.selected_filter == "All":
            filtered_errors = self.all_errors
        else:
            filtered_errors = [err for err in self.all_errors if str(err["amr_ip"]) == self.selected_filter]

        self._clear_rows()

        if not filtered_errors:
            self._show_empty_state()
            return

        for row in filtered_errors:
            self._add_error_row(row)

    def _clear_rows(self):
        for widget in self.scroll_area.winfo_children():
            widget.destroy()

    def _show_empty_state(self):
        self._close_error_popup()
        self._clear_rows()
        ctk.CTkLabel(
            self.scroll_area,
            text="No error entries available.",
            font=("Arial", 13),
        ).pack(pady=20)

    def _format_view_context(self):
        if self.selected_filter == "All":
            return "All IPs"
        return f"IP {self.selected_filter}"

    def _show_error_popup(self, row):
        self._close_error_popup()

        overlay = ctk.CTkFrame(self, fg_color="#0b0e12")
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.error_modal = overlay

        popup = ctk.CTkFrame(
            overlay,
            fg_color="#171b20",
            corner_radius=18,
            border_width=1,
            border_color="#2f3640",
            width=520,
            height=340,
        )
        popup.place(relx=0.5, rely=0.5, anchor="center")

        content = ctk.CTkFrame(popup, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        fields = [
            ("IP", str(row["amr_ip"])),
            ("Error name", str(row["error"])),
            ("Error description", str(row["error_desc"] or "No description available.")),
        ]

        for label, value in fields:
            field_row = ctk.CTkFrame(content, fg_color="transparent")
            field_row.pack(fill="x", pady=6)
            ctk.CTkLabel(field_row, text=f"{label}:", font=("Arial", 12, "bold"), width=140, anchor="w").pack(side="left")
            ctk.CTkLabel(field_row, text=value, font=("Arial", 12), anchor="w", justify="left", wraplength=280).pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            popup,
            text="Close",
            width=100,
            command=self._close_error_popup,
        ).pack(pady=(0, 18))

    def _close_error_popup(self):
        if self.error_modal is not None:
            self.error_modal.destroy()
            self.error_modal = None

    def _add_error_row(self, row):
        self._close_error_popup()
        row_frame = ctk.CTkFrame(self.scroll_area, fg_color="#171b20", corner_radius=12)
        row_frame.pack(fill="x", padx=8, pady=6)

        header = ctk.CTkFrame(row_frame, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(10, 4))

        ts = self.format_timestamp(row["timestamp"])
        ip = str(row["amr_ip"])
        ctk.CTkLabel(header, text=f"[{ts}]", font=("Consolas", 12, "bold")).pack(side="left")
        ctk.CTkLabel(header, text=f"AMR {ip}", font=("Arial", 12, "bold")).pack(side="left", padx=(10, 0))
        ctk.CTkLabel(header, text=str(row["error"]), font=("Arial", 12)).pack(side="left", padx=(12, 0))

        ctk.CTkButton(
            header,
            text="Describe error",
            width=130,
            command=lambda r=row: self._show_error_popup(r),
        ).pack(side="right")

    # =========================
    def get_errors_from_db(self):
        # Use the same implementation database as the graph and overview pages.
        project_root = Path(__file__).resolve().parent.parent
        database_path = project_root / "implementation" / "database_files" / "instance" / "database.db"

        conn = sqlite3.connect(database_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM error ORDER BY timestamp DESC")
            return cursor.fetchall()
        except sqlite3.OperationalError:
            return []
        finally:
            conn.close()

    # =========================
    # FORMAT HELPERS
    # =========================
    def format_timestamp(self, ts):
        return str(ts).split(".")[0]  # remove microseconds

    def is_valid_ipv4(self, ip_str: str) -> bool:
        return bool(re.match(r"^\d{1,3}(?:\.\d{1,3}){3}$", ip_str))

    def ip_field_with_padding(self, ip: str) -> str:
        """Return 'AMR {ip}' padded using format width 15 (IPv4 max length)."""
        ip_s = str(ip)
        print(f"AMR {ip_s:30}")  # debug print to verify padding
        return f"AMR {ip_s:30}"

    # =========================
    # LOAD ERRORS (SMART UPDATE)
    # =========================
    def load_errors(self):
        try:
            errors = self.get_errors_from_db()
        except Exception:
            errors = []

        self.all_errors = errors

        # Build filter options: "All" + all unique IPs
        ips = ["All"] + sorted(list(set(str(err["amr_ip"]) for err in self.all_errors)))
        self.filter_combo.configure(values=ips)

        # Reset filter to "All" if current selection no longer exists
        if self.selected_filter not in ips:
            self.selected_filter = "All"
            self.filter_combo.set("All")

        # Use maximum possible IPv4 length so '|' stays in same column
        self.ip_column_width = len("AMR ") + len("255.255.255.255")

        self.last_count = len(errors)
        self._render_filtered_errors()

    # =========================
    # ADD NEW ERROR (LIVE)
    # =========================
    def add_error(self, error):
        row = {
            "amr_ip": error["amr"],
            "timestamp": error["time"],
            "error": error["level"],
            "error_desc": error.get("description", "No description available."),
        }

        if self.selected_filter != "All" and str(row["amr_ip"]) != self.selected_filter:
            return

        self._add_error_row(row)
