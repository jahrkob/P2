import customtkinter as ctk

app = ctk.CTk()
app.geometry("1080x720")

class card(ctk.CTkFrame):
    def __init__(self, master, width = 200, height = 200, corner_radius = 10, border_width = None, bg_color = 'transparent', fg_color = '#323232', border_color = None, background_corner_colors = None, overwrite_preferred_drawing_method = None, **kwargs):
        super().__init__(master, width, height, corner_radius, border_width, bg_color, fg_color, border_color, background_corner_colors, overwrite_preferred_drawing_method, **kwargs)

frame1 = card(app)
frame2 = card(app)
frame3 = card(app)
frame4 = card(app)

padding = {
    "padx": 10,
    "pady": 10
}

options = {
    "sticky": "nsew",
    **padding
}

frame1.grid(column=1,row=1,**options)
frame2.grid(column=2,row=1,**options)
frame3.grid(column=1,row=2,**options)
frame4.grid(column=2,row=2,**options)

app.mainloop()