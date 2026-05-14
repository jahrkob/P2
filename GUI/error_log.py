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

        self.textbox = ctk.CTkTextbox(self, width=800, height=500, font=("Consolas", 12))
        self.textbox.pack(padx=10, pady=10, fill="both", expand=True)

        # Track last loaded row count
        self.last_count = 0

        try:
            self.load_errors()
        except Exception:
            self.textbox.insert("end", "No error entries available.\n")

    # =========================
    # DATABASE ACCESS
    def _on_filter_change(self, choice):
        """Handle filter selection change"""
        self.selected_filter = choice
        self._render_filtered_errors()

    def _render_filtered_errors(self):
        """Re-render errors based on current filter"""
        if self.selected_filter == "All":
            filtered_errors = self.all_errors
        else:
            filtered_errors = [err for err in self.all_errors if str(err["amr_ip"]) == self.selected_filter]

        scroll_pos = self.textbox.yview()
        at_bottom = scroll_pos[1] == 1.0

        self.textbox.delete("1.0", "end")

        if not filtered_errors:
            self.textbox.insert("end", "No error entries available.\n")
            if at_bottom:
                self.textbox.yview_moveto(1.0)
            else:
                self.textbox.yview_moveto(scroll_pos[0])
            return

        for row in filtered_errors:
            ts = self.format_timestamp(row["timestamp"])
            ip = str(row["amr_ip"])
            ip_field = self.ip_field_with_padding(ip)
            line = f"[{ts}] {ip_field} | {row['error']} -> {row['error_desc']}\n"
            self.textbox.insert("end", line)

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
        ip = str(error["amr"])
        ts = self.format_timestamp(error["time"]) if hasattr(self, "format_timestamp") else str(error["time"])

        # Same alignment as DB view (pad IP to max IPv4 length)
        ip_field = self.ip_field_with_padding(ip)
        line = f"[{ts}] {ip_field} | {error['level']}\n"
        self.textbox.insert("end", line)

        scroll_pos = self.textbox.yview()
        if scroll_pos[1] == 1.0:
            self.textbox.yview_moveto(1.0)
