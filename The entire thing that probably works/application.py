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

class InternetDevice:
    """Base class for all internet-connected devices."""

    def __init__(self, device_name, ip_address):
        self.device_name = device_name
        self.ip_address = ip_address

    def __str__(self):
        return f"{self.device_name} ({self.ip_address})"
    
class AMR(InternetDevice):
    """Autonomous Mobile Robot (AMR) class inheriting from InternetDevice."""

    def __init__(self, device_name, ip_address, status_code, status, amr_model, associated_raspberry_pi):
        super().__init__(device_name, ip_address)
        self.__status_code = status_code
        self.__status = status
        self.__amr_model = amr_model
        self.associated_raspberry_pi = associated_raspberry_pi

    def __str__(self):
        return f"{super().__str__()} - Status Code: {self.__status_code}, Status: {self.__status}, AMR Model: {self.__amr_model}, Associated Raspberry Pi: {self.associated_raspberry_pi}"
    
    def get_status_code(self):
        return self.__status_code
    
    def get_status(self):
        """Get battery percentage and position of the AMR."""
        battery_percentage = self.__status.get('battery_percentage', 'Unknown')
        position = self.__status.get('position', 'Unknown')
        return battery_percentage, position

class RaspberryPi(InternetDevice):
    """Raspberry Pi class inheriting from InternetDevice."""

    def __init__(self, device_name, ip_address, status_code, status, raspberry_pi_model):
        super().__init__(device_name, ip_address)
        self.__status_code = status_code
        self.__status = status
        self.__raspberry_pi_model = raspberry_pi_model
        self.__rssi = None

    def __str__(self):
        return f"{super().__str__()} - Status Code: {self.__status_code}, Status: {self.__status}, Raspberry Pi Model: {self.__raspberry_pi_model}"
    
    def get_rssi(self):
        return self.__rssi
    
class NetworkMonitorer:
    """Class to monitor the network and manage the fleet of AMRs."""

    def __init__(self, fleet_manager_ip, database = "database.db", auth_token = None):
        self.fleet_manager_ip = fleet_manager_ip
        self.database = database
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

    def load_amr_database(self):
        conn = sqlite3.connect("test_database.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM amr")

        self.amr_list = cursor.fetchall()

        conn.commit()
        conn.close()

    def add_amr_to_database(self, id, ip, name, raspi_ip):
        conn = sqlite3.connect("test_database.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO amr (id, ip, name, raspi_ip) VALUES (?, ?, ?, ?)", 
            (id, ip, name, raspi_ip))

        conn.commit()
        conn.close()

    def remove_amr_from_database(self, id):
        """Removes an AMR from all tables in the database"""
        # Kan evt. opdeles i flere funktioner, så den sletter fra enkelte tables i stedet for hele databasen
        conn = sqlite3.connect("test_database.db")
        cursor = conn.cursor()

        try: # try except ensures that data will only be deleted if it succeeds in deleting the specific AMR from ALL tables, else nothing is deleted
            cursor.execute("BEGIN")

            cursor.execute("DELETE FROM amr WHERE id = ?", (id,))
            cursor.execute("DELETE FROM data WHERE id = ?", (id,))
            cursor.execute("DELETE FROM error WHERE id = ?", (id,))
        
            conn.commit()

        except Exception as e:
            conn.rollback()
            print("Error: ", e)
        
        finally:
            conn.close()

    # Jeg antager at det bare er alt i "data" table i databasen. Kan nemt rettes, hvis nødvendigt.
    def save_amr_data(self, id, amr_ip, rtt, jitter, packet_loss, signal_strength, noise, rssi, battery, pos_x, pos_y):
        """Saves all network data to database"""
        conn = sqlite3.connect("test_database.db")
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
        conn = sqlite3.connect("test_database.db")
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()

        cursor.execute(
            "INSERT INTO error (id, amr_ip, timestamp, error, error_desc)", 
            (id, amr_ip, timestamp, error, error_desc)
        )

        conn.commit()
        conn.close()

    # Skal laves når AMR class er færdig
    # def save_api_errors(self):
    #     errors = AMR.get_errors()

    #     if not errors:
    #         return

    #     for err in errors:
    #         if isinstance(err, dict):
    #             error_name = str(err.get("code", err.get("error", "API_ERROR")))
    #             error_desc = str(err.get("description", err.get("message", json.dumps(err))))
    #         else:
    #             error_name = "API_ERROR"
    #             error_desc = str(err)

    #         self.save_amr_error(amr.amr_id, error_name, error_desc)

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
                self.load_amrs_from_database()

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
