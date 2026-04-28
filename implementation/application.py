"""
Monitor AMRs and Raspberry Pi devices using real HTTP APIs.

Classes:
- InternetDevice
- AMR
- RaspberryPi
- NetworkMonitorer
- DataGrapher
"""

import sqlite3, json, time, subprocess, requests
from datetime import datetime
from internet_device import InternetDevice
    
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
        if not self.status: # Opdaterer status hvis den ikke har en endnu, da errors ellers ville være tom. Kan evt. fjernes
            self.update_status() 
        return self.status.get("errors", [])

class NetworkMonitorer:
    """Class to monitor the network and manage the fleet of AMRs."""

    def __init__(self, fleet_manager_ip, database = "database.db", auth_token = None):
        self.fleet_manager_ip = fleet_manager_ip
        self.database = database
        self.auth_token = auth_token
        self.amr_list = []
        self.load_amr_database()

    def __str__(self):
        amr_info = "\n".join(str(amr) for amr in self.amr_list)
        return (
            f"Fleet Manager IP: {self.fleet_manager_ip}\n\n"
            f"AMRs:\n{amr_info if amr_info else 'Ingen AMR fundet'}"
        )

    def load_amr_database(self):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM amr")

        self.amr_list = cursor.fetchall()

        conn.commit()
        conn.close()

    def add_amr_to_database(self, ip, name, raspi_ip):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO amr (ip, name, raspi_ip) VALUES (?, ?, ?)", 
            (ip, name, raspi_ip))

        conn.commit()
        conn.close()

    def remove_amr_from_database(self, ip):
        """Removes an AMR from all tables in the database"""
        # Kan evt. opdeles i flere funktioner, så den sletter fra enkelte tables i stedet for hele databasen
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()

        try: # try except ensures that data will only be deleted if it succeeds in deleting the specific AMR from ALL tables, else nothing is deleted
            cursor.execute("BEGIN")

            cursor.execute("DELETE FROM amr WHERE ip = ?", (ip,))
            cursor.execute("DELETE FROM data WHERE amr_ip = ?", (ip,))
            cursor.execute("DELETE FROM error WHERE amr_ip = ?", (ip,))
        
            conn.commit()

        except Exception as e:
            conn.rollback()
            print("Error: ", e)
        
        finally:
            conn.close()

    # Jeg antager at det bare er alt i "data" table i databasen. Kan nemt rettes, hvis nødvendigt.
    def save_amr_data(self, id, amr_ip, rtt, jitter, packet_loss, signal_strength, noise, rssi, battery, pos_x, pos_y):
        """Saves all network data to database"""
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()

        timestamp = datetime.now().isoformat()

        cursor.execute(
            "INSERT INTO data (id, amr_ip, timestamp, rtt, jitter, packet_loss, signal_strength, noise, rssi, battery, pos_x, pos_y)",
            (id, amr_ip, timestamp, rtt, jitter, packet_loss, signal_strength, noise, rssi, battery, pos_x, pos_y)
        )

        conn.commit()
        conn.close()

    # Jeg antager at det her er alt der skal i "error" table.
    def save_amr_error(self, id, amr_ip, error, error_desc):
        """Saves status of amr to database"""
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()

        cursor.execute(
            "INSERT INTO error (id, amr_ip, timestamp, error, error_desc)", 
            (id, amr_ip, timestamp, error, error_desc)
        )

        conn.commit()
        conn.close()

    # Skal laves når AMR class er færdig
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

            self.save_amr_error(amr.id, amr.amr_ip, error_name, error_desc)

    def measure_network_metrics(self, amr): # Der skal laves amr objekter med AMR classen
        """
        Measure RTT, jitter and packet loss using ping.
        Works on typical Linux ping output.
        """
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
            self.save_amr_error(amr.id, amr.amr_ip, "NETWORK_MEASUREMENT_ERROR", str(e))
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
            self.save_amr_error(amr.id, amr.amr_ip, "POLLING_ERROR", str(e))

        try:
            rtt, jitter, packet_loss = self.measure_network_metrics(amr)
        except Exception as e:
            self.save_amr_error(amr.id, amr.amr_ip, "PING_ERROR", str(e))

        try:
            signal_strength, noise, rssi = self.get_raspi_metrics(amr)
        except Exception as e:
            self.save_amr_error(amr.id, amr.amr_ip, "RASPI_METRICS_ERROR", str(e))

        self.save_amr_data(
            id=amr.id,
            amr_ip=amr.amr_ip,
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

    def active_monitoring(self, interval_seconds=5, cycles=None, reload_from_database=True):
        """
        Run monitoring in a loop.

        reload_from_database=True means new AMRs added to DB
        are automatically included next cycle.
        """
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

# Til GUI
class DataGrapher:
    """Class to graph the data collected from the AMRs and Raspberry Pi."""
    def __init__(self):
        self.data = []

    def add_data(self, data_point):
        self.data.append(data_point)

    def display_data(self):
        for data_point in self.data:
            print(data_point)

# til test
# if __name__ == "__main__":
#     monitor = NetworkMonitorer(
#         fleet_manager_ip="192.168.1.1",
#         database="database.db",
#         auth_token="DIN_BASIC_AUTH_TOKEN"
#     )

#     # Eksempel:
#     # monitor.add_amr_to_database(
#     #     ip="192.168.1.51",
#     #     name="AMR #1",
#     #     raspi_ip="192.168.1.101"
#     # )

#     print(monitor)

#     # Én enkelt runde
#     for amr in monitor.amr_list:
#         monitor.monitor_one_amr(amr)

#     # Kontinuerlig monitorering
#     # monitor.active_monitoring(interval_seconds=5)
