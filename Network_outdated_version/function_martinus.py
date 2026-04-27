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
        """Removes an AMR from all tables in the database"""
        conn = sqlite3.connect("test_database.db")
        cursor = conn.cursor()

        try: # try except ensures that data will only be deleted if it succeeds in deleting the specific AMR from ALL tables, else nothing is deleted
            conn.execute("BEGIN")

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
    def save_network_data(self, id, amr, timestamp, rtt, jitter, packet_loss, signal_strength, noise, rssi, battery, pos_x, pos_y):
        """Saves all network data to database"""
        conn = sqlite3.connect("test_database.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO data (id, amr_, timestamp, rtt, jitter, packet_loss, signal_strength, noise, rssi, battery, pos_x, pos_y)",
            (id, amr, timestamp, rtt, jitter, packet_loss, signal_strength, noise, rssi, battery, pos_x, pos_y)
        )

        conn.commit()
        conn.close()

    # Jeg antager at det her er alt der skal i "error" table.
    def save_amr_status_log(self, id, amr, timestamp, error, error_desc):
        """Saves status of amr to database"""
        conn = sqlite3.connect("test_database.db")
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO error (id, amr_, timestamp, error, error_desc)", 
            (id, amr, timestamp, error, error_desc)
        )

        conn.commit()
        conn.close()
