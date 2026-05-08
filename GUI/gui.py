import customtkinter as ctk  # CustomTkinter library (modern-looking tkinter)

#  NEW IMPORTS
import sqlite3
from functools import partial
from pathlib import Path

import sys
cur_parent_dirs = sys.path[0].split('\\')
parent_dir_index = cur_parent_dirs.index("P2")+1
sys.path.append("\\".join(cur_parent_dirs[0:parent_dir_index])) # allows imports from P2 folder

from implementation.amr import AMR

#sys.path.append(os.path.abspath("/home/el/foo4/stuff"))
#from implementation.amr import AMR

# Import page classes from other files
from overview import OverviewPage
from error_log import ErrorLogPage
from map import MapPage
from graph import GraphPage

# Set app theme to dark mode
ctk.set_appearance_mode("dark")
# Disable DPI awareness to avoid issues
ctk.deactivate_automatic_dpi_awareness()


class GUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AMR Dashboard")
        self.geometry("1100x650")
        
        # Handle window close properly
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.update_loop_id = None
        self.last_data_signature = None

        # ===== GRID SETUP =====
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ===== SIDEBAR =====
        self.sidebar = ctk.CTkFrame(self, width=200)
        self.sidebar.grid(row=0, column=0, sticky="ns")

        self.build_sidebar()

        # ===== MAIN CONTAINER =====
        self.container = ctk.CTkFrame(self)
        self.container.grid(row=0, column=1, sticky="nsew")

        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # ===== PAGES =====
        self.frames = {}

        self.frames["overview"] = OverviewPage(self.container, on_graph_request=self.open_graph_for_amr)
        self.frames["errors"] = ErrorLogPage(self.container)
        self.frames["map"] = MapPage(self.container)
        self.frames["graph"] = GraphPage(self.container)

        for frame in self.frames.values():
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("overview")

    # =========================
    # Sidebar UI
    # =========================
    def build_sidebar(self):
        ctk.CTkLabel(self.sidebar, text="Dashboard",
                     font=("Arial", 18)).pack(pady=15)

        ctk.CTkButton(
            self.sidebar,
            text="AMR Overview",
            command=partial(self.show_frame, "overview")
        ).pack(pady=5, padx=10, fill="x")

        ctk.CTkButton(
            self.sidebar,
            text="Error Log",
            command=partial(self.show_frame, "errors")
        ).pack(pady=5, padx=10, fill="x")

        ctk.CTkButton(
            self.sidebar,
            text="Map",
            command=partial(self.show_frame, "map")
        ).pack(pady=5, padx=10, fill="x")

        ctk.CTkButton(
            self.sidebar,
            text="Graph",
            command=partial(self.show_frame, "graph")
        ).pack(pady=5, padx=10, fill="x")

    # =========================
    # Page switching
    # =========================
    def show_frame(self, name, amr_ip=None):
        self.frames[name].tkraise()
        # Draw graph when graph page is shown
        if name == "graph":
            self.frames["graph"].draw_graph(amr_ip)

    def open_graph_for_amr(self, amr_ip):
        self.show_frame("graph", amr_ip)

    def get_database_path(self):
        project_root = Path(__file__).resolve().parent.parent
        return project_root / "implementation" / "database_files" / "instance" / "database.db"

    # =========================
    # CORE METHODS
    # =========================
    def get_data(self):
        database_path = self.get_database_path()

        # Read the current database state once and build a compact snapshot for the UI.
        # This keeps the overview focused on the latest row per AMR instead of redrawing
        # every historical record on the screen.
        with sqlite3.connect(database_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            amr_rows = cursor.execute("SELECT ip, name, raspi_ip FROM amr ORDER BY ip ASC LIMIT 10").fetchall()
            latest_data_rows = cursor.execute("SELECT * FROM data ORDER BY timestamp DESC, id DESC").fetchall()
            latest_error_rows = cursor.execute("SELECT * FROM error ORDER BY timestamp DESC, id DESC").fetchall()

        latest_data_by_ip = {}
        for row in latest_data_rows:
            # Keep only the most recent data row for each AMR IP.
            amr_ip = row["amr_ip"]
            if amr_ip not in latest_data_by_ip:
                latest_data_by_ip[amr_ip] = row

        latest_error_by_ip = {}
        for row in latest_error_rows:
            # Same idea for errors: one latest entry per AMR is enough for the overview.
            amr_ip = row["amr_ip"]
            if amr_ip not in latest_error_by_ip:
                latest_error_by_ip[amr_ip] = row

        amrs = []
        errors = []

        for amr in amr_rows:
            amr_ip = amr["ip"]
            latest_data = latest_data_by_ip.get(amr_ip)
            latest_error = latest_error_by_ip.get(amr_ip)

            if latest_error is not None:
                status = "CRITICAL"
            elif latest_data is not None:
                status = "ONLINE"
            else:
                status = "OFFLINE"

            packet_loss = None
            if latest_data is not None and latest_data["packet_loss"] is not None:
                packet_loss = round(float(latest_data["packet_loss"]) * 100, 1)

            jitter = None
            if latest_data is not None and latest_data["jitter"] is not None:
                jitter = round(float(latest_data["jitter"]), 1)

            ping = None
            if latest_data is not None and latest_data["rtt"] is not None:
                ping = round(float(latest_data["rtt"]), 1)

            amrs.append(
                {
                    "name": amr["name"],
                    "ip": amr_ip,
                    "status": status,
                    "ping": ping,
                    "loss": packet_loss,
                    "jitter": jitter,
                    "battery": None if latest_data is None else latest_data["battery"],
                    "signal_strength": None if latest_data is None else latest_data["signal_strength"],
                    "rssi": None if latest_data is None else latest_data["rssi"],
                }
            )

            if latest_error is not None:
                errors.append(
                    {
                        "level": latest_error["error"],
                        "amr": amr_ip,
                        "time": latest_error["timestamp"],
                        "description": latest_error["error_desc"],
                    }
                )

        return {
            "amrs": amrs,
            "errors": errors,
        }

    def get_data_signature(self):
        database_path = self.get_database_path()

        # A small fingerprint of the tables is cheaper than rebuilding the whole screen.
        # If this signature stays the same, nothing visible needs to change.
        with sqlite3.connect(database_path) as conn:
            cursor = conn.cursor()
            amr_count = cursor.execute("SELECT COUNT(*) FROM amr").fetchone()[0]
            latest_data = cursor.execute("SELECT COALESCE(MAX(id), 0), COALESCE(MAX(timestamp), '') FROM data").fetchone()
            latest_error = cursor.execute("SELECT COALESCE(MAX(id), 0), COALESCE(MAX(timestamp), '') FROM error").fetchone()

        return (amr_count, latest_data[0], latest_data[1], latest_error[0], latest_error[1])

    def show_graph(self, data):
        self.frames["overview"].update_amrs(data["amrs"])
        self.frames["map"].update_map(data["amrs"])

    def show_error(self, error):
        self.frames["errors"].add_error(error)

    def notification(self, msg):
        print(f"[NOTIFICATION]: {msg}")

    # =========================
    # UPDATE LOOP
    # =========================
    def update_loop(self):
        data_signature = self.get_data_signature()

        # Only rebuild the cards and error log if the database actually changed.
        # This avoids recreating all widgets every few seconds when the data is unchanged.
        if data_signature != self.last_data_signature:
            data = self.get_data()

            self.show_graph(data)

            self.frames["errors"].load_errors()

            self.notification("Data updated")
            self.last_data_signature = data_signature

        self.update_loop_id = self.after(3000, self.update_loop)

    # =========================
    # CLEANUP
    # =========================
    def on_closing(self):
        """Handle window close event"""
        if self.update_loop_id is not None:
            try:
                self.after_cancel(self.update_loop_id)
            except Exception:
                pass
            self.update_loop_id = None

        graph_frame = self.frames.get("graph")
        if graph_frame is not None and hasattr(graph_frame, "cleanup"):
            try:
                graph_frame.cleanup()
            except Exception:
                pass

        self.quit()
        self.destroy()



# ==================================================
#                   Lasse Stuff
# ==================================================
AMR_list = []

class status_box(ctk.CTkTextbox):
    def __init__(self, master, width = 80, height = 46, corner_radius = None, border_width = None, border_spacing = 3, bg_color = "transparent", fg_color = None, border_color = None, text_color = None, scrollbar_button_color = None, scrollbar_button_hover_color = None, font = None, activate_scrollbars = True, **kwargs):
        super().__init__(master, width, height, corner_radius, border_width, border_spacing, bg_color, fg_color, border_color, text_color, scrollbar_button_color, scrollbar_button_hover_color, font, activate_scrollbars, **kwargs)
        self.insert(0,"offline")


class amr_card(ctk.CTkFrame):
    def __init__(self, master, amr:AMR, width = 300, height = 50, corner_radius = 10, border_width = None, bg_color = "transparent", fg_color = None, border_color = None, background_corner_colors = None, overwrite_preferred_drawing_method = None, **kwargs):
        super().__init__(master, width, height, corner_radius, border_width, bg_color, fg_color, border_color, background_corner_colors, overwrite_preferred_drawing_method, **kwargs)
        status_indicator = status_box(self)
        status_indicator.grid()


if __name__ == '__main__':
    app = ctk.CTk()
    
    card = amr_card(app)

    card.pack()

    app.mainloop()