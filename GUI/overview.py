import customtkinter as ctk


class OverviewPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)

        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(self.container, text="AMR Overview", font=("Arial", 18)).pack(pady=10)

    def update_amrs(self, amrs):
        # Placeholder to update AMR summary widgets
        pass