import sqlite3
import time
import json
import subprocess
from datetime import datetime

import requests

class NetworkMonitorer:
    """Class to monitor the network and manage the fleet of AMRs."""

    def __init__(self, fleet_manager_ip, database = "database.db", auth_token = None):
        self.fleet_manager_ip = fleet_manager_ip
        self.databbase = database
        self.auth_token = auth_token
        self.amr_list = []

        self.initialize_database()
        self.load_devices_from_database()

    def __str__(self):
        amr_info = "\n".join(str(amr) for amr in self.amr_list)
        return (
            f"Fleet Manager IP: {self.fleet_manager_ip}\n\n"
            f"AMRs:\n{amr_info if amr_info else 'Ingen AMR fundet'}"
        )

    def load_amrs_from_database(self):
        conn = sqlite3.connect("test_database.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM amr")

        self.amr_list = cursor.fetchall()

    def add_amr_to_database(self, amr):
        pass

    def remove_amr_from_database(self, amr):
        pass

    def save_data_row(
        self,
        amr_id,
        timestamp,
        rtt,
        jitter,
        packet_loss,
        signal_strength,
        noise,
        rssi,
        battery,
        pos_x,
        pos_y
    ):
        """Save one monitoring row to data table."""
        conn = sqlite3.connect(self.databbase)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO data (
                amr_id, timestamp, rtt, jitter, packet_loss,
                signal_strength, noise, rssi, battery, pos_x, pos_y
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            amr_id, timestamp, rtt, jitter, packet_loss,
            signal_strength, noise, rssi, battery, pos_x, pos_y
        ))

        conn.commit()
        conn.close()

    def save_error(self, amr_id, error_name, error_desc):
        pass

    def clear_errors_for_amr(self, amr_id):
        pass

    def save_api_errors(self, amr):
        pass

    def measure_network_metrics(self, amr):
        try:
            result = subprocess.run(
                ["ping", "-c", "4", amr.ip],
                capture_output=True,
                text=True,
                timeout=10
            )

            output = result.stdout + "\n" + result.stderr

            rtt = None
            jitter = None
            packet_loss = None

            for line in output.splitlines():
                if "packet loss" in line:
                    parts = line.split(",")
                    for part in parts:
                        if "packet loss" in part:
                            value = part.strip().replace("% packet loss", "")
                            packet_loss = float(value)

                if "min/avg/max" in line or "round-trip min/avg/max" in line:
                    try:
                        stats_part = line.split("=")[1].strip()
                        values_part = stats_part.split(" ")[0]
                        values = values_part.split("/")
                        rtt = float(values[1])      # avg
                        jitter = float(values[3])   # mdev
                    except (IndexError, ValueError):
                        pass

            if rtt is None:
                rtt = 0.0
            if jitter is None:
                jitter = 0.0
            if packet_loss is None:
                packet_loss = 100.0 if result.returncode != 0 else 0.0

            return rtt, jitter, packet_loss

        except Exception as e:
            self.save_error(amr.amr_id, "NETWORK_MEASUREMENT_ERROR", str(e))
            return 0.0, 0.0, 100.0

    def get_raspi_metrics(self, amr):
        pass

    def monitor_one_amr(self, amr):
        """Poll one AMR, measure network/Wi-Fi, and save to database."""
        timestamp = datetime.now().isoformat()

        rtt = None
        jitter = None
        packet_loss = None
        signal_strength = None
        noise = None
        rssi = None
        battery = None
        pos_x = None
        pos_y = None

        try:
            amr.update_status()
            battery = amr.get_battery_percentage()
            pos_x = amr.get_pos_x()
            pos_y = amr.get_pos_y()
            self.save_api_errors(amr)

        except Exception as e:
            self.save_error(amr.amr_id, "POLLING_ERROR", str(e))

        try:
            rtt, jitter, packet_loss = self.measure_network_metrics(amr)
        except Exception as e:
            self.save_error(amr.amr_id, "PING_ERROR", str(e))

        try:
            signal_strength, noise, rssi = self.get_raspi_metrics(amr)
        except Exception as e:
            self.save_error(amr.amr_id, "RASPI_METRICS_ERROR", str(e))

        self.save_data_row(
            amr_id=amr.amr_id,
            timestamp=timestamp,
            rtt=rtt,
            jitter=jitter,
            packet_loss=packet_loss,
            signal_strength=signal_strength,
            noise=noise,
            rssi=rssi,
            battery=battery,
            pos_x=pos_x,
            pos_y=pos_y
        )

        print(
            f"{amr.name} | "
            f"Battery: {battery} | "
            f"Pos: ({pos_x}, {pos_y}) | "
            f"RTT: {rtt} ms | "
            f"Jitter: {jitter} ms | "
            f"Packet loss: {packet_loss}% | "
            f"RSSI: {rssi}"
        )

    def active_monitoring(self):
        pass