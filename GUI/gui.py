import customtkinter as ctk  # CustomTkinter library (modern-looking tkinter)

# 🔥 NEW IMPORTS
import sqlite3
from functools import partial

import sys
cur_parent_dirs = sys.path[0].split('\\')
parent_dir_index = cur_parent_dirs.index("P2")
sys.path.append("\\".join(cur_parent_dirs[0:parent_dir_index+1])) # allows imports from P2 folder

from implementation.amr import AMR
import re

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

        self.frames["overview"] = OverviewPage(self.container)
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
    def show_frame(self, name):
        self.frames[name].tkraise()
        # Draw graph when graph page is shown
        if name == "graph":
            self.frames["graph"].draw_graph()

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
AMR_list = []

ipv4_pattern = re.compile(
    r"^(?:(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])$"
)

def is_valid_ipv4(ip):
    return bool(ipv4_pattern.match(ip))

class MyTextBox(ctk.CTkTextbox):
    def __init__(self, master, width = 200, height = 200, corner_radius = None, border_width = None, border_spacing = 3, bg_color = "transparent", fg_color = None, border_color = None, text_color = None, scrollbar_button_color = None, scrollbar_button_hover_color = None, font = None, activate_scrollbars = True, **kwargs):
        super().__init__(master, width, height, corner_radius, border_width, border_spacing, bg_color, fg_color, border_color, text_color, scrollbar_button_color, scrollbar_button_hover_color, font, activate_scrollbars, **kwargs)
        self.tag_config("center", justify="center")

    def write(self, text):
        self.delete('0.0',"end")
        self.configure(state="normal")
        self.insert("0.0",text)
        self.configure(state="disabled")
        self.tag_add("center", "0.0", "end")
    
    def delete_text(self):
        self.delete('0.0',"end")

class status_box(ctk.CTkFrame):
    def __init__(self, master, width = 80, height = 40, corner_radius = 8, border_width = None, bg_color = "gray", fg_color = None, border_color = None, background_corner_colors = None, overwrite_preferred_drawing_method = None, **kwargs):
        super().__init__(master, width, height, corner_radius, border_width, bg_color, fg_color, border_color, background_corner_colors, overwrite_preferred_drawing_method, **kwargs)
        self.textbox = MyTextBox(self,width=width,height=height,bg_color="transparent")
        self.textbox.write("offline")
        self.textbox.place(relx=0.5,rely=0.5,anchor=ctk.CENTER)


class amr_card(ctk.CTkFrame):
    def __init__(self, master, amr:AMR, width = 300, height = 50, corner_radius = 10, border_width = None, bg_color = "transparent", fg_color = None, border_color = None, background_corner_colors = None, overwrite_preferred_drawing_method = None, **kwargs):
        super().__init__(master, width, height, corner_radius, border_width, bg_color, fg_color, border_color, background_corner_colors, overwrite_preferred_drawing_method, **kwargs)

        self.grid_propagate(False) # disables children deciding size of parent
        self.amr = amr

        if not is_valid_ipv4(self.amr.ip):
            print(f"WARNING: INVALID IP, given IP-address is not valid: {self.amr.ip}\nThis may cause unintended effects in buttons")
        self.bindtags(self.amr.ip)
        

        self.status_indicator = status_box(self)
        self.status_indicator.grid(row=1,column=1)
        self.status_indicator.bindtags(self.amr.ip)

        self.name = MyTextBox(self,height=height)
        self.name.write(self.amr.name)
        self.name.grid(row=1,column=2)
        self.name.bindtags(self.amr.ip)
        
        self.bind_class(self.amr.ip,"<Button-1>", func=lambda e: print(f'clicked! {e}'))
        


if __name__ == '__main__':
    app = ctk.CTk()
    
    card = amr_card(app,
                    AMR("192.168.0.128","AMR #1","","")
    )

    card.pack()

    app.mainloop()