import json
import os
import platform
import re
import sqlite3
import subprocess
import time
from datetime import datetime

from amr import AMR
from raspberry_pi_files.RaspberryPi import RaspberryPi


class NetworkMonitorer:
    """Class to monitor the network and manage the fleet of AMRs."""

    def __init__(self, fleet_manager_ip, database, auth_token=None, raspi_port=80, monitor_wifi=True):
        self.fleet_manager_ip = fleet_manager_ip
        self.database = os.path.abspath(database)
        self.auth_token = auth_token
        self.raspi_port = raspi_port
        self.monitor_wifi = monitor_wifi
        self.amr_list = []
        self.initialize_database()
        self.load_amr_database()

    def __str__(self):
        amr_info = "\n".join(str(amr) for amr in self.amr_list)
        return (
            f"Fleet Manager IP: {self.fleet_manager_ip}\n\n"
            f"AMRs:\n{amr_info if amr_info else 'Ingen AMR fundet'}"
        )

    def initialize_database(self, drop_existing=False):
        os.makedirs(os.path.dirname(self.database), exist_ok=True)
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()

        if drop_existing:
            cursor.execute("DROP TABLE IF EXISTS error")
            cursor.execute("DROP TABLE IF EXISTS data")
            cursor.execute("DROP TABLE IF EXISTS amr")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS amr (
                ip TEXT PRIMARY KEY,
                name TEXT,
                raspi_ip TEXT NOT NULL UNIQUE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amr_ip TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                robot_name TEXT,
                state_text TEXT,
                mode_text TEXT,
                map_id TEXT,
                rtt REAL,
                jitter REAL,
                packet_loss REAL,
                signal_strength REAL,
                noise REAL,
                rssi REAL,
                battery REAL,
                pos_x REAL,
                pos_y REAL,
                FOREIGN KEY (amr_ip) REFERENCES amr(ip)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS error (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amr_ip TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                error TEXT NOT NULL,
                error_desc TEXT,
                FOREIGN KEY (amr_ip) REFERENCES amr(ip)
            )
        """)

        self.ensure_data_column(cursor, "robot_name", "TEXT")
        self.ensure_data_column(cursor, "state_text", "TEXT")
        self.ensure_data_column(cursor, "mode_text", "TEXT")
        self.ensure_data_column(cursor, "map_id", "TEXT")

        conn.commit()
        conn.close()

    def ensure_data_column(self, cursor, column_name, column_type):
        existing_columns = [row[1] for row in cursor.execute("PRAGMA table_info(data)").fetchall()]
        if column_name not in existing_columns:
            cursor.execute(f"ALTER TABLE data ADD COLUMN {column_name} {column_type}")

    def load_amr_database(self):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute("SELECT ip, name, raspi_ip FROM amr ORDER BY name")

        self.amr_list = [
            AMR(ip=row[0], name=row[1], raspi_ip=row[2], auth_token=self.auth_token)
            for row in cursor.fetchall()
        ]

        conn.close()

    def add_amr_to_database(self, ip, name, raspi_ip):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO amr (ip, name, raspi_ip) VALUES (?, ?, ?)
                ON CONFLICT(ip) DO UPDATE SET
                    name = excluded.name,
                    raspi_ip = excluded.raspi_ip
                """,
                (ip, name, raspi_ip),
            )
        except sqlite3.IntegrityError as e:
            print(str(e))

        conn.commit()
        conn.close()
        self.load_amr_database()

    def remove_amr_from_database(self, ip):
        """Removes an AMR from all tables in the database."""
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()

        try:
            cursor.execute("BEGIN")
            cursor.execute("DELETE FROM data WHERE amr_ip = ?", (ip,))
            cursor.execute("DELETE FROM error WHERE amr_ip = ?", (ip,))
            cursor.execute("DELETE FROM amr WHERE ip = ?", (ip,))
            conn.commit()
            self.amr_list = [amr for amr in self.amr_list if amr.ip != ip]
        except Exception as e:
            conn.rollback()
            print("Error: ", e)
        finally:
            conn.close()

    def save_amr_data(
        self,
        amr_ip,
        robot_name,
        state_text,
        mode_text,
        map_id,
        rtt,
        jitter,
        packet_loss,
        signal_strength,
        noise,
        rssi,
        battery,
        pos_x,
        pos_y,
    ):
        """Saves network and AMR data to the database."""
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO data (
                amr_ip, timestamp, robot_name, state_text, mode_text, map_id,
                rtt, jitter, packet_loss, signal_strength,
                noise, rssi, battery, pos_x, pos_y
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                amr_ip,
                timestamp,
                robot_name,
                state_text,
                mode_text,
                map_id,
                rtt,
                jitter,
                packet_loss,
                signal_strength,
                noise,
                rssi,
                battery,
                pos_x,
                pos_y,
            ),
        )

        conn.commit()
        conn.close()

    def save_amr_error(self, amr_ip, error, error_desc):
        """Saves an AMR, network or Raspberry Pi error to the database."""
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()

        cursor.execute(
            "INSERT INTO error (amr_ip, timestamp, error, error_desc) VALUES (?, ?, ?, ?)",
            (amr_ip, timestamp, error, error_desc),
        )

        conn.commit()
        conn.close()

    def save_api_errors(self, amr: AMR):
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

            self.save_amr_error(amr.ip, error_name, error_desc)

    def measure_network_metrics(self, amr: AMR):
        """Measure RTT, jitter and packet loss using ping."""
        try:
            ping_count_arg = "-n" if platform.system().lower() == "windows" else "-c"
            result = subprocess.run(
                ["ping", ping_count_arg, "4", amr.ip],
                capture_output=True,
                text=True,
                timeout=10,
            )

            output = result.stdout + "\n" + result.stderr
            rtt = None
            jitter = 0.0
            packet_loss = None

            for line in output.splitlines():
                lower_line = line.lower()

                if "packet loss" in lower_line:
                    for part in line.split(","):
                        if "packet loss" in part.lower():
                            match = re.search(r"(\d+(?:\.\d+)?)\s*%\s*packet loss", part, re.IGNORECASE)
                            if match:
                                packet_loss = float(match.group(1))
                elif "loss" in lower_line:
                    match = re.search(r"\((\d+(?:\.\d+)?)%\s*loss\)", line, re.IGNORECASE)
                    if match:
                        packet_loss = float(match.group(1))

                if "min/avg/max" in lower_line or "round-trip min/avg/max" in lower_line:
                    try:
                        stats_part = line.split("=")[1].strip()
                        values_part = stats_part.split(" ")[0]
                        values = values_part.split("/")
                        rtt = float(values[1])
                        jitter = float(values[3])
                    except (IndexError, ValueError):
                        pass
                elif "average" in lower_line:
                    match = re.search(r"Average\s*=\s*(\d+(?:\.\d+)?)ms", line, re.IGNORECASE)
                    if match:
                        rtt = float(match.group(1))

            if rtt is None:
                rtt = 0.0
            if packet_loss is None:
                packet_loss = 100.0 if result.returncode != 0 else 0.0

            return rtt, jitter, packet_loss

        except Exception as e:
            self.save_amr_error(amr.ip, "NETWORK_MEASUREMENT_ERROR", str(e))
            return 0.0, 0.0, 100.0

    def monitor_one_amr(self, amr: AMR):
        """Poll one AMR, measure network/Wi-Fi, save to database and print result."""
        rtt = None
        jitter = None
        packet_loss = None
        signal_strength = None
        noise = None
        rssi = None
        battery = None
        pos_x = None
        pos_y = None
        polling_error = None
        raspi_error = None
        wifi_status = "Skipped - Raspberry Pi not configured"

        try:
            amr.update_status()
            battery = amr.get_battery_percentage()
            pos_x = amr.get_pos_x()
            pos_y = amr.get_pos_y()
            self.save_api_errors(amr)
        except Exception as e:
            polling_error = str(e)
            self.save_amr_error(amr.ip, "POLLING_ERROR", polling_error)

        try:
            rtt, jitter, packet_loss = self.measure_network_metrics(amr)
        except Exception as e:
            self.save_amr_error(amr.ip, "PING_ERROR", str(e))

        if self.monitor_wifi and amr.raspi_ip:
            wifi_status = "Enabled"
            try:
                raspberry_pi = RaspberryPi(f"{amr.name} Raspberry Pi", amr.raspi_ip, self.raspi_port)
                signal_strength, noise, rssi = raspberry_pi.get_signal_metrics()
            except Exception as e:
                raspi_error = str(e)
                self.save_amr_error(amr.ip, "RASPI_METRICS_ERROR", raspi_error)

        self.save_amr_data(
            amr_ip=amr.ip,
            robot_name=amr.get_robot_name(),
            state_text=amr.get_state_text(),
            mode_text=amr.get_mode_text(),
            map_id=amr.get_map_id(),
            rtt=rtt,
            jitter=jitter,
            packet_loss=packet_loss,
            signal_strength=signal_strength,
            noise=noise,
            rssi=rssi,
            battery=battery,
            pos_x=pos_x,
            pos_y=pos_y,
        )

        self.print_monitoring_result(
            amr=amr,
            battery=battery,
            pos_x=pos_x,
            pos_y=pos_y,
            rtt=rtt,
            jitter=jitter,
            packet_loss=packet_loss,
            signal_strength=signal_strength,
            noise=noise,
            rssi=rssi,
            polling_error=polling_error,
            raspi_error=raspi_error,
            wifi_status=wifi_status,
        )

    def print_monitoring_result(
        self,
        amr,
        battery,
        pos_x,
        pos_y,
        rtt,
        jitter,
        packet_loss,
        signal_strength,
        noise,
        rssi,
        polling_error=None,
        raspi_error=None,
        wifi_status=None,
    ):
        errors = amr.get_errors()
        print(f"\n--- Monitorering: {amr.name} ({amr.ip}) ---")
        print("AMR status:")
        print(f"  Robot name: {amr.get_robot_name()}")
        print(f"  State: {amr.get_state_text()}")
        print(f"  Mode: {amr.get_mode_text()}")
        print(f"  Battery: {battery}%")
        print(f"  Position: x={pos_x}, y={pos_y}")
        print(f"  Map ID: {amr.get_map_id()}")
        print(f"  API errors: {errors if errors else 'None'}")
        if polling_error:
            print(f"  Status API error: {polling_error}")

        print("Network metrics:")
        print(f"  RTT: {rtt} ms")
        print(f"  Jitter: {jitter} ms")
        print(f"  Packet loss: {packet_loss}%")

        print("WiFi metrics:")
        print(f"  Status: {wifi_status}")
        print(f"  Raspberry Pi: {amr.raspi_ip or 'None'}")
        print(f"  RSSI: {rssi} dBm")
        print(f"  Quality/signal: {signal_strength}")
        print(f"  Noise: {noise}")
        if raspi_error:
            print(f"  WiFi API error: {raspi_error}")

    def print_latest_database_rows(self, limit=5):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()

        print("\nSeneste data i databasen:")
        for row in cursor.execute(
            """
            SELECT amr_ip, timestamp, robot_name, state_text, mode_text, battery,
                   pos_x, pos_y, rtt, jitter, packet_loss, signal_strength,
                   noise, rssi
            FROM data
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ):
            print(row)

        print("\nSeneste errors i databasen:")
        for row in cursor.execute(
            """
            SELECT amr_ip, timestamp, error, error_desc
            FROM error
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ):
            print(row)

        conn.close()

    def active_monitoring(self, interval_seconds=5, cycles=None, reload_from_database=True):
        """Run monitoring in a loop."""
        cycle = 0

        while True:
            print(f"\n--- Ny monitoreringscyklus {cycle + 1} | {datetime.now().isoformat()} ---")

            if reload_from_database:
                self.load_amr_database()

            for amr in self.amr_list:
                self.monitor_one_amr(amr)

            cycle += 1
            if cycles is not None and cycle >= cycles:
                print("Monitorering stoppet.")
                break

            time.sleep(interval_seconds)
