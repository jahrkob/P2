import customtkinter as ctk
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta
from pathlib import Path


class GraphPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)

        # Graph container
        self.graph_frame = ctk.CTkFrame(self)
        self.graph_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.graph_canvas = None
        self.figure = None
        self.current_amr_ip = None

    def get_database_path(self):
        project_root = Path(__file__).resolve().parent.parent
        return project_root / "implementation" / "database_files" / "instance" / "database.db"

    def get_default_amr_ip(self, cursor):
        cursor.execute(
            """
            SELECT amr_ip
            FROM data
            WHERE amr_ip IS NOT NULL
            GROUP BY amr_ip
            ORDER BY COUNT(*) DESC, amr_ip ASC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        return row[0] if row else None

    def get_graph_data(self, amr_ip=None):
        try:
            database_path = self.get_database_path()
            conn = sqlite3.connect(database_path)
            cursor = conn.cursor()

            selected_amr_ip = amr_ip
            if selected_amr_ip is None:
                selected_amr_ip = self.get_default_amr_ip(cursor)

            if selected_amr_ip is None:
                conn.close()
                return [], [], None

            cursor.execute("""
                SELECT timestamp, packet_loss
                FROM data
                WHERE amr_ip = ?
                ORDER BY timestamp ASC
            """, (selected_amr_ip,))

            rows = cursor.fetchall()
            conn.close()

            if not rows:
                return [], [], selected_amr_ip

            second_data = {}
            for row in rows:
                timestamp_text = row[0]
                packet_loss = row[1]

                if packet_loss is None:
                    continue

                try:
                    dt = datetime.fromisoformat(timestamp_text)
                except ValueError:
                    dt = datetime.fromisoformat(timestamp_text.split(".")[0])

                second_key = dt.replace(microsecond=0)
                second_data.setdefault(second_key, []).append(packet_loss)

            if not second_data:
                return [], [], selected_amr_ip

            time_points = sorted(second_data.keys())
            values = [sum(second_data[t]) / len(second_data[t]) for t in time_points]

            return time_points, values, selected_amr_ip

        except Exception as e:
            print(f"DEBUG: Error in GraphPage.get_graph_data: {e}")
            import traceback
            traceback.print_exc()
            return [], [], None

    def draw_graph(self, amr_ip=None):
        if amr_ip is not None:
            self.current_amr_ip = amr_ip

        times, values, selected_amr_ip = self.get_graph_data(self.current_amr_ip)
        if selected_amr_ip is not None:
            self.current_amr_ip = selected_amr_ip

        if self.figure is not None:
            plt.close(self.figure)
            self.figure = None

        if self.graph_canvas is not None:
            self.graph_canvas.get_tk_widget().destroy()
            self.graph_canvas = None

        fig, ax = plt.subplots(figsize=(10, 4))
        self.figure = fig
        graph_title = "AMR Packet Loss Over Time"
        if selected_amr_ip is not None:
            graph_title = f"AMR Packet Loss Over Time ({selected_amr_ip})"

        if not times or not values:
            ax.set_title(graph_title)
            ax.set_xlabel("Time")
            ax.set_ylabel("Packet Loss (%)")
            if selected_amr_ip is None:
                ax.text(0.5, 0.5, "No AMR data available", ha="center", va="center", transform=ax.transAxes)
            else:
                ax.text(0.5, 0.5, f"No data available for {selected_amr_ip}", ha="center", va="center", transform=ax.transAxes)
            self.graph_canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
            self.graph_canvas.draw()
            self.graph_canvas.get_tk_widget().pack(fill="both", expand=True)
            return

        ax.plot(times, values, linewidth=2, color='#1f77b4')
        ax.set_title(graph_title)
        ax.set_xlabel("Time")
        ax.set_ylabel("Packet Loss (%)")

        if len(times) > 1:
            min_time = min(times)
            max_time = max(times)
            span = (max_time - min_time).total_seconds()
            if span <= 0:
                padding = timedelta(seconds=60)
            else:
                padding = timedelta(seconds=max(span * 0.1, 60))
        else:
            padding = timedelta(minutes=5)

        ax.set_xlim(times[0] - padding, times[-1] + padding)

        import matplotlib.dates as mdates
        ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        fig.autofmt_xdate()
        fig.tight_layout()

        self.graph_canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        self.graph_canvas.draw()
        self.graph_canvas.get_tk_widget().pack(fill="both", expand=True)

    def cleanup(self):
        if self.graph_canvas is not None:
            self.graph_canvas.get_tk_widget().destroy()
            self.graph_canvas = None
        if self.figure is not None:
            plt.close(self.figure)
            self.figure = None

    def update_amrs(self, amrs):
        # Placeholder if later we want to update graph from live AMR data
        pass
