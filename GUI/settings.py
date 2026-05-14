##### external dependencies #####
import customtkinter as ctk
import re
import sqlalchemy


##### importing same project files #####
import sys
cur_parent_dirs = sys.path[0].split('\\')
parent_dir_index = cur_parent_dirs.index("P2")
sys.path.append("\\".join(cur_parent_dirs[0:parent_dir_index+1])) # allows imports from P2 folder

from implementation.network_monitorer import NetworkMonitorer, TableNames

# =======================================================================
#                               Popup
#========================================================================

class Popup(ctk.CTkFrame):
    # this popup is created using CLAUDE
    """
    A modal popup rendered as an overlay directly on the parent window.
    Uses place() to cover the entire parent and centers a card in the middle.
 
    To use it is preferred to make classes that inherit from popup and places elements in self.content.

    Usage:
        popup = Popup(parent, title="My Popup", width=400, height=300)
 
        ctk.CTkLabel(popup.content, text="Name").pack(anchor="w")
        ctk.CTkEntry(popup.content, placeholder_text="Enter name…").pack(fill="x", pady=(2, 10))
        ctk.CTkButton(popup.content, text="OK", command=popup.close).pack()
    """
 
    def __init__(
        self,
        parent: ctk.CTk,
        title: str = "",
        width: int = 400,
        height: int = 300,
        corner_radius: int = 16,
        background = "#1e1e1e"
    ):
        # The outer frame acts as the darkening overlay — covers the whole parent
        super().__init__(
            parent,
            corner_radius=corner_radius,
            fg_color=background,
            bg_color="transparent",
        )
        self._parent = parent
        self._card_width = width
        self._card_height = height
 
        # Stretch overlay over the entire parent surface
        self.place(x=0, y=0, relwidth=1, relheight=1)
        self.lift()
 
        # Semi-transparent feel via a stipple canvas behind the card
        self._dim = ctk.CTkCanvas(
            self,
            highlightthickness=0,
            bg=background,
        )
        self._dim.place(x=0, y=0, relwidth=1, relheight=1)
        # self._dim.bind("<Configure>", self._draw_dim)
 
        # Card frame centered in the overlay
        self._card = ctk.CTkFrame(
            self,
            width=width,
            height=height,
            corner_radius=corner_radius,
        )
        self._card.place(relx=0.5, rely=0.5, anchor="center")
        self._card.pack_propagate(False)
 
        # Optional title bar
        if title:
            title_bar = ctk.CTkFrame(
                self._card,
                corner_radius=0,
                fg_color=self._card.cget("fg_color"),
                height=44,
            )
            title_bar.pack(fill="x")
            title_bar.pack_propagate(False)
 
            ctk.CTkLabel(
                title_bar,
                text=title,
                font=ctk.CTkFont(size=15, weight="bold"),
                anchor="w",
            ).place(x=16, rely=0.5, anchor="w")
 
            ctk.CTkButton(
                title_bar,
                text="✕",
                width=28,
                height=28,
                corner_radius=6,
                fg_color="transparent",
                hover_color=("gray80", "gray30"),
                command=self.close,
            ).place(relx=1.0, x=-8, rely=0.5, anchor="e")
 
            ctk.CTkFrame(
                self._card,
                corner_radius=corner_radius,
                height=1,
                fg_color=("gray80", "gray25"),
            ).pack(fill="x")
 
        # Public content frame — place your widgets here
        self.content = ctk.CTkFrame(self._card, fg_color="transparent")
        self.content.pack(expand=True, fill="both", padx=16, pady=16)
 
        # Escape to close; clicking the dim area closes too
        parent.bind("<Escape>", lambda e: self.close(), add="+")
        self._dim.bind("<Button-1>", lambda e: self.close())
 
    # ------------------------------------------------------------------
 
    # def _draw_dim(self, event=None):
    #     """Redraws the stipple rectangle that simulates a dark overlay."""
    #     self._dim.delete("all")
    #     w = self._dim.winfo_width()
    #     h = self._dim.winfo_height()
    #     self._dim.create_rectangle(
    #         0, 0, w, h,
    #         fill="#000000",
    #         stipple="gray50",   # 50% stipple ≈ semi-transparent black
    #         outline="",
    #         tags="dim",
    #     )
 
    # ------------------------------------------------------------------
 
    def close(self):
        """Removes the overlay from the parent."""
        self._parent.unbind("<Escape>")
        self.place_forget()
        self.destroy()

# =======================================================================
#                           Error Popup
#========================================================================

class ErrorPopup(Popup):
    def __init__(self, parent, title, description="", width = 400, height = 300, corner_radius = 16):
        super().__init__(parent, title, width, height, corner_radius)
        self.description = description
        if self.description:
            self.description_box = ctk.CTkTextbox(self.content)
            self.description_box.insert('0.0',self.description)
            self.description_box.configure(state='disabled')
            self.description_box.pack(pady=20,padx=20,fill='both',expand=True)

# =======================================================================
#                           ADD AMR Popup
#========================================================================

class AddAMRPopup(Popup):
    def __init__(self, parent, network_monitorer:NetworkMonitorer, title = "Add AMR", width = 400, height = 350, corner_radius = 16):
        super().__init__(parent, title, width, height, corner_radius)
        self.network_monitorer = network_monitorer

        ctk.CTkLabel(self.content, text='Name of AMR').pack()
        self.name_entry = ctk.CTkEntry(self.content, placeholder_text='ex. AMR #4', width=280)
        self.name_entry.pack()

        ctk.CTkLabel(self.content, text='AMR IP-address').pack(pady=(10,0))
        self.ip_entry = ctk.CTkEntry(self.content, placeholder_text='ex. 192.168.100.52', width=280)
        self.ip_entry.pack()

        ctk.CTkLabel(self.content, text='Nuc Device EUI').pack(pady=(10,0))
        self.DevEUI_entry = ctk.CTkEntry(self.content, placeholder_text='ex. A8-40-41-5B-40-5D-15-F9', width=280)
        self.DevEUI_entry.pack()

        self.submit_button = ctk.CTkButton(self.content,text='Submit', command=self.submit)
        self.submit_button.pack(pady=(30,0))
    
    def check_valid_Dev_EUI(self, Dev_EUI:str):
        DEVICE_EUI_PATTERN = re.compile(r'^([0-9A-Fa-f]{2}-){7}[0-9A-Fa-f]{2}$')
        return bool(DEVICE_EUI_PATTERN.match(Dev_EUI))
    
    def check_valid_IP_address(self, ip_adr:str):
        IP_ADDRESS_PATTERN = re.compile(r'(\b25[0-5]|\b2[0-4][0-9]|\b[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}')
        return bool(IP_ADDRESS_PATTERN.match(ip_adr))

    def submit(self):
        name = self.name_entry.get()
        ip_adr = self.ip_entry.get()
        dev_eui = self.DevEUI_entry.get()

        if not name:
            name = f'AMR: {ip_adr}'
        
        if not self.check_valid_IP_address(ip_adr):
            Popup(self._parent,'Invalid IP address given', height=100)
            return

        if not self.check_valid_Dev_EUI(dev_eui):
            Popup(self._parent,'Invalid Device EUI given', height=100)
            return
        
        if self.network_monitorer.check_value_exists(TableNames.amr,'ip',ip_adr):
            ErrorPopup(self._parent,'Operation Failed', 'AMR with given IP-address already exists')
            return
        
        if self.network_monitorer.check_value_exists(TableNames.amr,'raspi_ip',dev_eui):
            ErrorPopup(self._parent,'Operation Failed', 'Given Device EUI is already listed under another AMR')
            return

        if not self.network_monitorer.add_amr_to_database(ip_adr,name,dev_eui):
            ErrorPopup(self._parent,'Operation Failed', 'Unknown error, check terminal.')
        else:
            self.close()

# =======================================================================
#                         Remove AMR Popup
#========================================================================

class RemoveAMRPopup(Popup):
    def __init__(self, parent, network_monitorer:NetworkMonitorer, title = "Remove AMR", width = 400, height = 250, corner_radius = 16):
        super().__init__(parent, title, width, height, corner_radius)
        self.network_monitorer = network_monitorer

        ctk.CTkLabel(self.content, text='AMR IP-address').pack(pady=(10,0))
        self.ip_entry = ctk.CTkEntry(self.content, placeholder_text='ex. 192.168.100.52', width=280)
        self.ip_entry.pack()

        self.submit_button = ctk.CTkButton(self.content,text='Delete', command=self.submit)
        self.submit_button.pack(pady=(30,0))
    
    def check_valid_IP_address(self, ip_adr:str):
        IP_ADDRESS_PATTERN = re.compile(r'(\b25[0-5]|\b2[0-4][0-9]|\b[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}')
        return bool(IP_ADDRESS_PATTERN.match(ip_adr))

    def submit(self):
        ip_adr = self.ip_entry.get()
        
        if not self.check_valid_IP_address(ip_adr):
            Popup(self._parent,'Invalid IP address given', height=100)
            return
    
        if self.network_monitorer.check_value_exists(TableNames.amr,'ip',ip_adr):
            ErrorPopup(self._parent,'Operation Failed', 'AMR with given IP-address already exists')
            return

        self.network_monitorer.remove_amr_from_database(ip_adr)
        self.close()


# =======================================================================
#                           Settings page
#========================================================================

class SettingsPage(ctk.CTkFrame):
    def __init__(self, master, network_monitorer:NetworkMonitorer, width = 200, height = 200, corner_radius = None, border_width = None, bg_color = "transparent", fg_color = None, border_color = None, background_corner_colors = None, overwrite_preferred_drawing_method = None, **kwargs):
        super().__init__(master, width, height, corner_radius, border_width, bg_color, fg_color, border_color, background_corner_colors, overwrite_preferred_drawing_method, **kwargs)
        self.network_monitorer = network_monitorer
        
        self.title_font = ctk.CTkFont('Arial', size=40, weight='bold')
        self.setting_font = ctk.CTkFont('Arial', size=18, weight='bold')
        setting_pady = (10,10)

        ctk.CTkLabel(self,text='Settings',font=self.title_font).pack(pady=(10,20))

        ctk.CTkLabel(self,text='Start monitoring new AMR', font=self.setting_font).pack(pady=(setting_pady[0],0))
        self.add_amr_button = ctk.CTkButton(self,width=200, text='Add AMR', command=self.popup_add_amr)
        self.add_amr_button.pack(pady=(0,setting_pady[1]))

        ctk.CTkLabel(self,text='Stop monitoring new AMR', font=self.setting_font).pack(pady=(setting_pady[0],0))
        self.add_amr_button = ctk.CTkButton(self,width=200, text='Remove AMR', command=self.popup_remove_amr)
        self.add_amr_button.pack(pady=(0,setting_pady[1]))

    def popup_add_amr(self):
        AddAMRPopup(self,self.network_monitorer)
    
    def popup_remove_amr(self):
        RemoveAMRPopup(self,self.network_monitorer)


