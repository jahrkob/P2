import customtkinter as ctk
import sqlite3

class ErrorLogPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)

        # Title
        ctk.CTkLabel(self, text="Error Log", font=("Arial", 20)).pack(pady=10)

        # Textbox to display errors
        self.textbox = ctk.CTkTextbox(self, width=800, height=500)
        self.textbox.pack(padx=10, pady=10, fill="both", expand=True)

        # Load existing errors on startup
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
    # LOAD ALL ERRORS
    # =========================
    def load_errors(self):
        self.textbox.delete("1.0", "end")

        errors = self.get_errors_from_db()

        for row in errors:
            line = f"[{row['timestamp']}] AMR {row['amr_ip']} | {row['error']} -> {row['error_desc']}\n"
            self.textbox.insert("end", line)

    # =========================
    # ADD NEW ERROR (from GUI)
    # =========================
    def add_error(self, error):
        line = f"[{error['time']}] AMR {error['amr']} | {error['level']}\n"
        self.textbox.insert("end", line)