import sqlite3
import json
import time
from datetime import datetime
import requests

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

    def add_amr_to_database(self, id, ip, name, raspi_ip):
        conn = sqlite3.connect("test_database.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO amr (id, ip, name, raspi_ip) VALUES (?, ?, ?, ?)", 
            (id, ip, name, raspi_ip)
        )

        conn.commit() # MANGLER I APPLICATION KODEN
        conn.close()

    def remove_amr_from_database(self, id):
        conn = sqlite3.connect("test_database.db")
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM amr WHERE id = ?", (id,)
        )

        conn.commit()
        conn.close()

    def save_network_data(self): # Bør nok først laves, når vi har en måde at få data på
        pass

    def save_amr_status_log(self): # Er lidt i tvivl om den her er nødvendig
        pass
