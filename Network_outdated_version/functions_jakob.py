import sqlite3
import time
import json
import subprocess
from datetime import datetime

import requests


class InternetDevice:
    """Base class for internet-connected devices."""

    def __init__(self, device_name, ip):
        self.device_name = device_name
        self.ip = ip

    def __str__(self):
        return f"{self.device_name} ({self.ip})"


class AMR(InternetDevice):
    """Autonomous Mobile Robot."""

    def __init__(self, id, amr_ip, name, raspi_ip, api_version="v2.0.0"):
        super().__init__(name, amr_ip)
        self.id = id
        self.amr_ip = amr_ip
        self.name = name
        self.raspi_ip = raspi_ip
        self.auth_token = "ZGlzdHJpYnV0b3I6NjjmMmYwZjFlZmYxMGQzMTUyYzk1ZjZmMDU5NjU3NmU0ODJiYjhINDQ4MDY0MzNmNGNmOTI5NzkyODM0YjAxNA=="
        self.api_version = api_version

        self.status_code = None
        self.status = {}

    # Måske overflødigt
    # def __str__(self):
    #     battery = self.get_battery_percentage()
    #     state = self.get_state_text()
    #     mode = self.get_mode_text()
    #     return (
    #         f"{self.name} ({self.amr_ip}) - "
    #         f"RasPi IP: {self.raspi_ip}, "
    #         f"Battery: {battery}, State: {state}, Mode: {mode}"
    #     )

    def update_status(self):
        """Fetch live status from the AMR API."""
        headers = {
            "accept": "application/json",
            "Accept-Language": "en_US"
        }

        if self.auth_token:
            headers["Authorization"] = f"Basic {self.auth_token}"

        url = f"http://{self.amr_ip}/api/{self.api_version}/status"
        response = requests.get(url, headers=headers, timeout=5)

        self.status_code = response.status_code
        response.raise_for_status()
        self.status = response.json()

    def get_battery_percentage(self):
        return self.status.get("battery_percentage")

    def get_position(self):
        return self.status.get("position", {})

    def get_pos_x(self):
        return self.get_position().get("x")

    def get_pos_y(self):
        return self.get_position().get("y")

    def get_state_text(self):
        return self.status.get("state_text")

    def get_mode_text(self):
        return self.status.get("mode_text")

    def get_errors(self):
        return self.status.get("errors", [])


class NetworkMonitorer:
    """Monitor and manage AMRs using SQLite + live API polling."""

    def __init__(self, fleet_manager_ip, database="database.db", auth_token=None):
        self.fleet_manager_ip = fleet_manager_ip
        self.database = database
        self.auth_token = auth_token
        self.amr_list = []

        self.initialize_database()
        self.load_amrs_from_database()

    def __str__(self):
        amr_info = "\n".join(str(amr) for amr in self.amr_list)
        return (
            f"Fleet Manager IP: {self.fleet_manager_ip}\n\n"
            f"AMRs:\n{amr_info if amr_info else 'Ingen AMR fundet'}"
        )

    def initialize_database(self):
        """Create tables if they do not already exist."""
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS amr (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip VARCHAR(39) NOT NULL UNIQUE,
                name VARCHAR(80),
                raspi_ip VARCHAR(80) UNIQUE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amr_id INTEGER NOT NULL,
                timestamp DATETIME NOT NULL,
                rtt FLOAT,
                jitter FLOAT,
                packet_loss FLOAT,
                signal_strength FLOAT,
                noise FLOAT,
                rssi FLOAT,
                battery FLOAT,
                pos_x FLOAT,
                pos_y FLOAT,
                FOREIGN KEY (amr_id) REFERENCES amr(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS "error" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amr_id INTEGER NOT NULL,
                timestamp DATETIME NOT NULL,
                error TEXT NOT NULL,
                error_desc TEXT,
                FOREIGN KEY (amr_id) REFERENCES amr(id)
            )
        """)

        conn.commit()
        conn.close()

    def load_amrs_from_database(self):
        """Load all AMRs from database."""
        self.amr_list = []

        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, ip, name, raspi_ip
            FROM amr
        """)

        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            amr = AMR(
                id=row[0],
                amr_ip=row[1],
                name=row[2],
                raspi_ip=row[3],
                auth_token=self.auth_token
            )
            self.amr_list.append(amr)

    def add_amr_to_database(self, amr_ip, name, raspi_ip):
        """Add a new AMR to database."""
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO amr (ip, name, raspi_ip)
            VALUES (?, ?, ?)
        """, (amr_ip, name, raspi_ip))

        conn.commit()
        conn.close()

        self.load_amrs_from_database()

    def remove_amr_from_database(self, amr_id):
        """Remove an AMR from database."""
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM amr WHERE id = ?", (amr_id,))
        conn.commit()
        conn.close()

        self.load_amrs_from_database()

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
        conn = sqlite3.connect(self.database)
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
        """Save one error row to error table."""
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO "error" (amr_id, timestamp, error, error_desc)
            VALUES (?, ?, ?, ?)
        """, (
            amr_id,
            datetime.now().isoformat(),
            error_name,
            error_desc
        ))

        conn.commit()
        conn.close()

    def save_api_errors(self, amr):
        errors = amr.get_errors()

        if not errors:
            return

        for err in errors:
            if isinstance(err, dict):
                error_name = str(err.get("code", err.get("error", "API_ERROR")))
                error_desc = str(err.get("description", err.get("message", json.dumps(err))))
            else:
                error_name = "API_ERROR"
                error_desc = str(err)

            self.save_error(amr.amr_id, error_name, error_desc)

    def measure_network_metrics(self, amr):
        """
        Measure RTT, jitter and packet loss using ping.
        Works on typical Linux ping output.
        """
        try:
            result = subprocess.run(
                ["ping", "-c", "4", amr.amr_ip],
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
        """
        Henter signal-metrics fra Raspberry Pi.

        Eksempel på JSON:
        {
            "rssi": -71.0,
            "quality": 39.0,
            "noise": None
        }

        RSSI bruges også som signal_strength.
        Noise må gerne være None.
        """

        url = f"http://{amr.raspi_ip}:5000/api/status"

        headers = {
        "Authorization": "Bearer YOUR_RASPBERRY_PI_TOKEN"
        }

        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()

        metrics = response.json()

        rssi = metrics.get("rssi")
        noise = metrics.get("noise")
        signal_strength = rssi

        return signal_strength, noise, rssi

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

    def active_monitoring(self, interval_seconds=5, max_cycles=None, reload_from_database=True):
        """
        Run monitoring in a loop.

        reload_from_database=True means new AMRs added to DB
        are automatically included next cycle.
        """
        cycle = 0

        while True:
            print(f"\n--- Ny monitoreringscyklus {cycle + 1} | {datetime.now().isoformat()} ---")

            if reload_from_database:
                self.load_amrs_from_database()

            for amr in self.amr_list:
                self.monitor_one_amr(amr)

            cycle += 1
            if max_cycles is not None and cycle >= max_cycles:
                print("Monitorering stoppet.")
                break

            time.sleep(interval_seconds)


if __name__ == "__main__":
    monitor = NetworkMonitorer(
        fleet_manager_ip="192.168.1.1",
        database="database.db",
        auth_token="DIN_BASIC_AUTH_TOKEN"
    )

    # Eksempel:
    # monitor.add_amr_to_database(
    #     ip="192.168.1.51",
    #     name="AMR #1",
    #     raspi_ip="192.168.1.101"
    # )

    print(monitor)

    # Én enkelt runde
    for amr in monitor.amr_list:
        monitor.monitor_one_amr(amr)

    # Kontinuerlig monitorering
    # monitor.active_monitoring(interval_seconds=5)