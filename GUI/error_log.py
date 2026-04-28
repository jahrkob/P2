import customtkinter as ctk
import sqlite3
import re

class ErrorLogPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)

        ctk.CTkLabel(self, text="Error Log", font=("Arial", 20)).pack(pady=10)

        self.textbox = ctk.CTkTextbox(self, width=800, height=500)
        self.textbox.pack(padx=10, pady=10, fill="both", expand=True)

        # Track last loaded row count
        self.last_count = 0

        self.load_errors()

    # =========================
    # DATABASE ACCESS
    # =========================
    def get_errors_from_db(self):
        conn = sqlite3.connect("database_files/instance/database.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM error ORDER BY timestamp DESC")
        rows = cursor.fetchall()

        conn.close()
        return rows

    # =========================
    # FORMAT HELPERS
    # =========================
    def format_timestamp(self, ts):
        return str(ts).split(".")[0]  # remove microseconds

    def is_valid_ipv4(self, ip_str: str) -> bool:
        return bool(re.match(r"^\d{1,3}(?:\.\d{1,3}){3}$", ip_str))

    def ip_field_with_padding(self, ip: str) -> str:
        """Return 'AMR {ip}' padded using format width 15 (IPv4 max length).

        Uses the f-string format specifier `:15s` to pad shorter IPs so the
        `|` column aligns vertically.
        """
        ip_s = str(ip)
        return f"AMR {ip_s:15s}"

    # =========================
    # LOAD ERRORS (SMART UPDATE)
    # =========================
    def load_errors(self):
        errors = self.get_errors_from_db()

        # Use maximum possible IPv4 length so '|' stays in same column
        self.ip_column_width = len("AMR ") + len("255.255.255.255")

        scroll_pos = self.textbox.yview()
        at_bottom = scroll_pos[1] == 1.0

        if len(errors) != self.last_count:
            self.textbox.delete("1.0", "end")

            for row in errors:
                ts = self.format_timestamp(row['timestamp'])
                ip = str(row['amr_ip'])

                # align IP column using fixed maximum IPv4 width
                ip_field = self.ip_field_with_padding(ip)
                line = f"[{ts}] {ip_field} | {row['error']} -> {row['error_desc']}\n"
                self.textbox.insert("end", line)

            self.last_count = len(errors)

        # Restore scroll position
        if at_bottom:
            self.textbox.yview_moveto(1.0)
        else:
            self.textbox.yview_moveto(scroll_pos[0])

    # =========================
    # ADD NEW ERROR (LIVE)
    # =========================
    def add_error(self, error):
        scroll_pos = self.textbox.yview()
        at_bottom = scroll_pos[1] == 1.0

        ip = str(error['amr'])
        ts = self.format_timestamp(error['time']) if hasattr(self, 'format_timestamp') else str(error['time'])

        # Same alignment as DB view (pad IP to max IPv4 length)
        ip_field = self.ip_field_with_padding(ip)
        line = f"[{ts}] {ip_field} | {error['level']}\n"
        self.textbox.insert("end", line)

        if at_bottom:
            self.textbox.yview_moveto(1.0)