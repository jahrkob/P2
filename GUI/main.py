from gui import GUI

app = GUI()
app.after(1000, app.update_loop)  # start updates
app.mainloop()