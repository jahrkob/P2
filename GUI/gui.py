import customtkinter as ctk  # CustomTkinter library (modern-looking tkinter)

# Import page classes from other files
from overview import OverviewPage
from error_log import ErrorLogPage
from map import MapPage

# Set app theme to dark mode
ctk.set_appearance_mode("dark")


class GUI(ctk.CTk):
    def __init__(self):
        super().__init__()  # Start the main CTk window

        # Window title and size
        self.title("AMR Dashboard")
        self.geometry("1100x650")

        # ===== GRID SETUP =====
        # The window has 2 columns:
        # column 0 = sidebar, column 1 = main content
        self.grid_columnconfigure(1, weight=1)  # Main content expands
        self.grid_rowconfigure(0, weight=1)     # Row expands with window

        # ===== SIDEBAR =====
        # Left menu frame
        self.sidebar = ctk.CTkFrame(self, width=200)
        self.sidebar.grid(row=0, column=0, sticky="ns")  # Stretch up/down

        # Build buttons/labels inside sidebar
        self.build_sidebar()

        # ===== MAIN CONTAINER =====
        # Right side area where pages are shown
        self.container = ctk.CTkFrame(self)
        self.container.grid(row=0, column=1, sticky="nsew")  # Fill all space

        # Let page frame inside container expand
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # ===== PAGES =====
        # Dictionary to store all page objects
        self.frames = {}

        # Create each page once
        self.frames["overview"] = OverviewPage(self.container)
        self.frames["errors"] = ErrorLogPage(self.container)
        self.frames["map"] = MapPage(self.container)

        # Put all pages in same grid cell
        # Only the top one (raised) is visible
        for frame in self.frames.values():
            frame.grid(row=0, column=0, sticky="nsew")

        # Show overview page first
        self.show_frame("overview")

    # =========================
    # Sidebar UI
    # =========================
    def build_sidebar(self):
        # Sidebar title
        ctk.CTkLabel(self.sidebar, text="Dashboard",
                     font=("Arial", 18)).pack(pady=15)

        # Button: go to overview page
        ctk.CTkButton(
            self.sidebar,
            text="AMR Overview",
            command=lambda: self.show_frame("overview")
        ).pack(pady=5, padx=10, fill="x")

        # Button: go to error log page
        ctk.CTkButton(
            self.sidebar,
            text="Error Log",
            command=lambda: self.show_frame("errors")
        ).pack(pady=5, padx=10, fill="x")

        # Button: go to map page
        ctk.CTkButton(
            self.sidebar,
            text="Map",
            command=lambda: self.show_frame("map")
        ).pack(pady=5, padx=10, fill="x")

    # =========================
    # Page switching
    # =========================
    def show_frame(self, name):
        # Bring selected page to front (make it visible)
        self.frames[name].tkraise()

    # =========================
    # CORE METHODS (your 4)
    # =========================

    def get_data(self):
        """
        Get AMR data.
        For now this returns fake data (dummy data).
        Later replace with real API/socket data.
        """
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
        """
        Send AMR data to pages so they can update their UI.
        """
        # Update overview page cards/table
        self.frames["overview"].update_amrs(data["amrs"])

        # Update map page markers/positions
        self.frames["map"].update_map(data["amrs"])

    def show_error(self, error):
        """
        Add one AMR error to the Error Log page.
        """
        self.frames["errors"].add_error(error)

    def notification(self, msg):
        """
        Simple notification.
        Right now: print to terminal only.
        """
        print(f"[NOTIFICATION]: {msg}")

    # =========================
    # Example update loop
    # =========================
    def update_loop(self):
        # 1) Get latest data
        data = self.get_data()

        # 2) Update overview + map
        self.show_graph(data)

        # 3) Add all new errors to error log
        for err in data["errors"]:
            self.show_error(err)

        # 4) Print update message
        self.notification("Data updated")

        # 5) Run this function again after 3000 ms (3 sec)
        self.after(3000, self.update_loop)