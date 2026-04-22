"""
Monitor AMRs and Raspberry Pi devices using real HTTP APIs.

Classes:
- InternetDevice
- AMR
- RaspberryPi
- NetworkMonitorer
- DataGrapher
"""

import sqlite3
import requests

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

    def __init__(self, fleet_manager_ip, database = "database.db"):
        self.fleet_manager_ip = fleet_manager_ip
        self.databbase = database
        self.amr_list = []
        self.raspberry_pi = []

        self.initialize_database()
        self.load_devices_from_database()

    def __str__(self):
        pi_info = "\n".join(str(pi) for pi in self.raspberry_pi_list)
        amr_info = "\n".join(str(amr) for amr in self.amr_list)

        return (
            f"Fleet Manager IP: {self.fleet_manager_ip}\n\n"
            f"Raspberry Pis:\n{pi_info if pi_info else 'Ingen Raspberry Pi fundet'}\n\n"
            f"AMRs:\n{amr_info if amr_info else 'Ingen AMR fundet'}"
        )

    def initialize_database(self):
        conn = sqlite3.connect(self.databbase)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS raspberry_pis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_name TEXT NOT NULL,
                ip_address TEXT NOT NULL UNIQUE,
                raspberry_pi_model TEXT,
                metrics_url TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS amrs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_name TEXT NOT NULL,
                ip_address TEXT NOT NULL UNIQUE,
                amr_model TEXT,
                api_version TEXT DEFAULT 'v2.0.0',
                auth_token TEXT,
                raspberry_pi_id INTEGER,
                FOREIGN KEY (raspberry_pi_id) REFERENCES raspberry_pis(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS amr_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amr_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                battery_percentage REAL,
                x REAL,
                y REAL,
                orientation REAL,
                linear_velocity REAL,
                angular_velocity REAL,
                state_text TEXT,
                mode_text TEXT,
                raw_status TEXT,
                FOREIGN KEY (amr_id) REFERENCES amrs(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pi_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                raspberry_pi_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                rssi INTEGER,
                raw_status TEXT,
                FOREIGN KEY (raspberry_pi_id) REFERENCES raspberry_pis(id)
            )
        """)

        conn.commit()
        conn.close()
    
    def load_devices_from_database(self):
        pass

    def add_raspberry_pi_to_database(self, raspberry_pi):
        pass

    def add_amr_to_database(self, amr):
        pass

    def remove_amr_from_database(self, amr):
        pass

    def remove_raspberry_pi_from_database(self, raspberry_pi):
        pass

    def save_amr_log(self, amr):
        pass

    def save_pi_log(self, raspberry_pi):
        pass

    def poll_all_amrs(self):
        pass

    def poll_all_raspberry_pis(self):
        pass

    def active_monitoring(self):
        pass


    # gammelt:
    # def __str__(self):
    #     amr_info = "\n".join(str(amr) for amr in self.__amr_list)
    #     base_info = f"Fleet Manager IP: {self.fleet_manager_ip}\nRaspberry Pi: {self.__raspberry_pi}\nAMRs:"
    #     if amr_info:
    #         return f"{base_info}\n{amr_info}"
    #     return base_info

    # def get_amr_list(self):
    #     return self.__amr_list

    # def add_amr(self, amr):
    #     self.__amr_list.append(amr)

    # def remove_amr(self, amr):
    #     if amr in self.__amr_list:
    #         self.__amr_list.remove(amr)

    # def get_wifi_metrics(self):
    #     pass

    # def active_monitoring(self):
    #     pass

class DataGrapher:
    """Class to graph the data collected from the AMRs and Raspberry Pi."""
    def __init__(self):
        self.data = []

    def add_data(self, data_point):
        self.data.append(data_point)

    def display_data(self):
        for data_point in self.data:
            print(data_point)

# Example usage
if __name__ == "__main__":
    import doctest
    doctest.testmod()

    # Create instances and demonstrate functionality
    raspberry_pi = RaspberryPi("Raspberry Pi 4", "192.168.1.100", 200, {"status": "online"}, "Model B")
    amr_1 = AMR("AMR 1", "192.168.0.100", 200, {"status": "online", "battery_percentage": 80, "position": (10, 20)}, "Model X", raspberry_pi)
    network_monitorer = NetworkMonitorer("192.168.1.1", raspberry_pi)
    network_monitorer.add_amr(amr_1)
    print(network_monitorer)
    # network_monitorer.get_wifi_metrics()
    # print(f"Updated RSSI: {raspberry_pi.get_rssi()} dBm")
    # data_grapher = DataGrapher()
    # data_grapher.add_data({"timestamp": "2024-06-01 12:00:00", "battery_percentage": 80, "position": (10, 20), "rssi": raspberry_pi.get_rssi()})
    # data_grapher.display_data()
