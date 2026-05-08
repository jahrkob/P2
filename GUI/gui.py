import customtkinter as ctk  # CustomTkinter library (modern-looking tkinter)

# 🔥 NEW IMPORTS
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta
from functools import partial
from pathlib import Path

# Import page classes from other files
from overview import OverviewPage
from error_log import ErrorLogPage
from map import MapPage

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

        # 🔥 GRAPH FRAME
        self.graph_frame = ctk.CTkFrame(self.container)
        self.graph_frame.grid(row=1, column=0, sticky="nsew")
        self.container.grid_rowconfigure(1, weight=1)

        # ===== PAGES =====
        self.frames = {}

        self.frames["overview"] = OverviewPage(self.container)
        self.frames["errors"] = ErrorLogPage(self.container)
        self.frames["map"] = MapPage(self.container)

        for frame in self.frames.values():
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("overview")

    def get_database_path(self):
        project_root = Path(__file__).resolve().parent.parent
        return project_root / "database_files" / "instance" / "database.db"

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

    # =========================
    # Page switching
    # =========================
    def show_frame(self, name):
        self.frames[name].tkraise()

    # =========================
    # 🔥 DATABASE → GRAPH DATA
    # =========================
    def get_graph_data(self):
        try:
            database_path = self.get_database_path()
            conn = sqlite3.connect(database_path)
            cursor = conn.cursor()

            # Get data from the last 2 hours
            time_limit = (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S.%f")

            cursor.execute("""
                SELECT timestamp, packet_loss
                FROM data
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
            """, (time_limit,))

            rows = cursor.fetchall()
            conn.close()

            print(f"DEBUG: Querying database at {database_path}")
            print(f"DEBUG: Found {len(rows)} rows from database")

            if not rows:
                return [], []

            # Group data by MINUTE and calculate average packet loss per minute
            minute_data = {}
            for row in rows:
                ts = row[0]
                packet_loss = row[1] * 100  # Convert to %
                
                try:
                    dt = datetime.fromisoformat(ts)
                except ValueError:
                    dt = datetime.fromisoformat(ts.split(".")[0])
                
                # Round to the nearest minute
                minute_key = dt.replace(second=0, microsecond=0)
                
                if minute_key not in minute_data:
                    minute_data[minute_key] = []
                minute_data[minute_key].append(packet_loss)

            # Calculate average for each minute
            times = sorted(minute_data.keys())
            values = [sum(minute_data[t]) / len(minute_data[t]) for t in times]

            print(f"DEBUG: Aggregated to {len(times)} data points")
            if times:
                print(f"DEBUG: Time range: {times[0]} to {times[-1]}")
                print(f"DEBUG: Values range: {min(values):.2f} to {max(values):.2f}")
            return times, values
            
        except Exception as e:
            print(f"DEBUG: Error in get_graph_data: {e}")
            import traceback
            traceback.print_exc()
            return [], []

    # =========================
    # 🔥 DRAW GRAPH
    # =========================
    def draw_graph(self):
        times, values = self.get_graph_data()

        if hasattr(self, "graph_canvas"):
            self.graph_canvas.get_tk_widget().destroy()

        fig, ax = plt.subplots(figsize=(10, 4))

        print(f"DEBUG draw_graph: times={len(times)} values={len(values)}")

        if not times or not values:
            print("DEBUG: No data to display")
            ax.set_title("AMR Packet Loss Over Time")
            ax.set_xlabel("Time")
            ax.set_ylabel("Packet Loss (%)")
            ax.text(0.5, 0.5, "No data available", ha="center", va="center", transform=ax.transAxes)
            self.graph_canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
            self.graph_canvas.draw()
            self.graph_canvas.get_tk_widget().pack(fill="both", expand=True)
            return

        # Plot the data
        ax.plot(times, values, linewidth=2, marker='o', markersize=4, color='#1f77b4')
        ax.set_title("AMR Packet Loss Over Time")
        ax.set_xlabel("Time")
        ax.set_ylabel("Packet Loss (%)")

        # Set axis limits with padding
        if len(times) > 1:
            min_time = min(times)
            max_time = max(times)
            span = (max_time - min_time).total_seconds()
            if span <= 0:
                padding = timedelta(seconds=60)
            else:
                padding = timedelta(seconds=max(span * 0.1, 60))
        else:
            # Single point - add padding around it
            padding = timedelta(minutes=5)
            
        ax.set_xlim(times[0] - padding, times[-1] + padding)

        # Format x-axis date display
        import matplotlib.dates as mdates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        fig.autofmt_xdate()
        fig.tight_layout()

        self.graph_canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        self.graph_canvas.draw()
        self.graph_canvas.get_tk_widget().pack(fill="both", expand=True)

    # =========================
    # CORE METHODS
    # =========================
    def get_data(self):
        return {
            "amrs": [
                {"id": 3, "status": "CRITICAL", "ping": 23, "loss": 10, "jitter": 9},
                {"id": 1, "status": "OFFLINE", "ping": 0, "loss": 0, "jitter": 0}
            ],
            "errors": [
                {"level": "CRITICAL", "amr": 1, "time": "19:02"},
                {"level": "WARNING", "amr": 3, "time": "19:07"}
            ]
        }

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
        data = self.get_data()

        self.show_graph(data)

        self.frames["errors"].load_errors()

        # 🔥 GRAPH UPDATE
        self.draw_graph()

        self.notification("Data updated")

        self.update_loop_id = self.after(3000, self.update_loop)

    # =========================
    # CLEANUP
    # =========================
    def on_closing(self):
        """Handle window close event"""
        if self.update_loop_id is not None:
            self.after_cancel(self.update_loop_id)
        self.destroy()



# ==================================================
#                   Lasse Stuff
# ==================================================

class amr_card(ctk.CTkFrame):
    def __init__(self, master, width = 200, height = 200, corner_radius = None, border_width = None, bg_color = "transparent", fg_color = None, border_color = None, background_corner_colors = None, overwrite_preferred_drawing_method = None, **kwargs):
        super().__init__(master, width, height, corner_radius, border_width, bg_color, fg_color, border_color, background_corner_colors, overwrite_preferred_drawing_method, **kwargs)