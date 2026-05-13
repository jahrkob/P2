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
        self.current_metrics = ["packet_loss"]

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

    def _metric_config(self, metric_name):
        metric_name = metric_name.lower()
        if metric_name == "packet_loss":
            return "packet_loss", "Packet loss (%)", "Packet Loss Over Time", "#c94f4f"
        if metric_name == "jitter":
            return "jitter", "Jitter (ms)", "Jitter Over Time", "#d9822b"
        if metric_name == "ping":
            return "rtt", "Ping (ms)", "Ping Over Time", "#2d6cdf"
        return None, None, None, None

    def get_graph_data(self, amr_ip=None, metric_name="packet_loss"):
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

            column_name, _, _, _ = self._metric_config(metric_name)
            if column_name is None:
                conn.close()
                return [], [], selected_amr_ip

            cursor.execute("""
                SELECT timestamp, {column_name}
                FROM data
                WHERE amr_ip = ?
                ORDER BY timestamp ASC
            """.format(column_name=column_name), (selected_amr_ip,))

            rows = cursor.fetchall()
            conn.close()

            if not rows:
                return [], [], selected_amr_ip

            second_data = {}
            for row in rows:
                timestamp_text = row[0]
                metric_value = row[1]

                if metric_value is None:
                    continue

                try:
                    dt = datetime.fromisoformat(timestamp_text)
                except ValueError:
                    dt = datetime.fromisoformat(timestamp_text.split(".")[0])

                second_key = dt.replace(microsecond=0)
                second_data.setdefault(second_key, []).append(metric_value)

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

    def _clear_canvas(self):
        if self.figure is not None:
            plt.close(self.figure)
            self.figure = None

        if self.graph_canvas is not None:
            self.graph_canvas.get_tk_widget().destroy()
            self.graph_canvas = None

    def draw_graph(self, amr_ip=None, metrics=None):
        if amr_ip is not None:
            self.current_amr_ip = amr_ip

        if metrics is not None and len(metrics) > 0:
            self.current_metrics = metrics
        elif not self.current_metrics:
            self.current_metrics = ["packet_loss"]

        selected_amr_ip = self.current_amr_ip
        metric_series = []
        for metric_name in self.current_metrics:
            times, values, metric_amr_ip = self.get_graph_data(self.current_amr_ip, metric_name)
            if metric_amr_ip is not None:
                selected_amr_ip = metric_amr_ip
            metric_series.append((metric_name, times, values))

        if selected_amr_ip is not None:
            self.current_amr_ip = selected_amr_ip

        self._clear_canvas()

        if len(self.current_metrics) == 1:
            metric_name, times, values = metric_series[0]
            _, ylabel, title_prefix, color = self._metric_config(metric_name)
            fig, ax = plt.subplots(figsize=(10, 4))
            self.figure = fig
            graph_title = title_prefix
            if selected_amr_ip is not None:
                graph_title = f"{title_prefix} ({selected_amr_ip})"

            if not times or not values:
                ax.set_title(graph_title)
                ax.set_xlabel("Time")
                ax.set_ylabel(ylabel)
                message = "No AMR data available" if selected_amr_ip is None else f"No data available for {selected_amr_ip}"
                ax.text(0.5, 0.5, message, ha="center", va="center", transform=ax.transAxes)
            else:
                ax.plot(times, values, linewidth=2, color=color)
                ax.set_title(graph_title)
                ax.set_xlabel("Time")
                ax.set_ylabel(ylabel)
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
                locator = mdates.AutoDateLocator()
                formatter = mdates.ConciseDateFormatter(locator)
                ax.xaxis.set_major_locator(locator)
                ax.xaxis.set_major_formatter(formatter)
                fig.autofmt_xdate()
                fig.tight_layout()
        else:
            fig, axes = plt.subplots(len(self.current_metrics), 1, figsize=(10, 4 * len(self.current_metrics)), sharex=True)
            self.figure = fig
            if len(self.current_metrics) == 1:
                axes = [axes]

            for axis, (metric_name, times, values) in zip(axes, metric_series):
                _, ylabel, title_prefix, color = self._metric_config(metric_name)
                if selected_amr_ip is not None:
                    title_prefix = f"{title_prefix} ({selected_amr_ip})"

                axis.set_title(title_prefix)
                axis.set_ylabel(ylabel)

                if not times or not values:
                    axis.text(0.5, 0.5, "No data available", ha="center", va="center", transform=axis.transAxes)
                    continue

                axis.plot(times, values, linewidth=2, color=color)

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
                axis.set_xlim(times[0] - padding, times[-1] + padding)

            axes[-1].set_xlabel("Time")
            import matplotlib.dates as mdates
            locator = mdates.AutoDateLocator()
            formatter = mdates.ConciseDateFormatter(locator)
            axes[-1].xaxis.set_major_locator(locator)
            axes[-1].xaxis.set_major_formatter(formatter)
            fig.autofmt_xdate()
            fig.tight_layout()

        self.graph_canvas = FigureCanvasTkAgg(self.figure, master=self.graph_frame)
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
