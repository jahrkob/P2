import sqlite3, json, time, subprocess, sqlalchemy # sqlite3 er ikke længere i brug, og internet_device er fjernet (bruges gennem raspi og amr)
from datetime import datetime

##### importing same project files #####
import sys

if sys.platform == "linux":
    file_sep = '/'
else:
    file_sep = '\\'
cur_parent_dirs = sys.path[0].split(file_sep)
parent_dir_index = cur_parent_dirs.index("P2")
sys.path.append(file_sep.join(cur_parent_dirs[0:parent_dir_index+1])) # allows imports from P2 folder


from implementation.amr import AMR
from implementation.raspberry_pi_files.RaspberryPi import RaspberryPi

from implementation.database_files.Database_specification import app, db
import implementation.database_files.Database_specification as db_spec

##### for testing purposes #####
import pytest
import unittest
from unittest.mock import patch, Mock
from http import HTTPStatus


import threading

class NetworkMonitorer:
    """Class to monitor the network and manage the fleet of AMRs."""

    def __init__(self, fleet_manager_ip, auth_token = None): # evt kom tilbage til init, da vi lige skal være sikre på hvilke parametre den skal bruge
        self.fleet_manager_ip = fleet_manager_ip
        self.auth_token = auth_token
        self.amr_list_lock = threading.Lock()
        with self.amr_list_lock:
            self.amr_list: list[AMR] = []
        self.load_amr_database()

    def __str__(self):
        amr_info = "\n".join([str(amr) for amr in self.amr_list])
        return (
            f"Fleet Manager IP: {self.fleet_manager_ip}\n\n"
            f"AMRs:\n{amr_info if amr_info else 'Ingen AMR fundet'}"
        )

    def load_amr_database(self):
        self.amr_list = []

        with app.app_context():
            db_amr_list = db.session.query(db_spec.AMR).all()
        
        for amr_spec in db_amr_list:
            with self.amr_list_lock:
                self.amr_list.append(AMR(amr_spec.ip, amr_spec.name, amr_spec.raspi_ip, self.auth_token))
        
        return db_amr_list

    def add_amr_to_database(self, ip, name, raspi_ip):
        try:
            with app.app_context():
                # print("DB URL:", db.engine.url) # for testing
                db.session.add(db_spec.AMR(ip=ip,name=name,raspi_ip=raspi_ip))
                db.session.commit()
            # self.amr_list.append(AMR(ip=ip,name=name,raspi_ip=raspi_ip)) # add to list in memory
        
        except sqlalchemy.exc.IntegrityError as e:
            print(str(e).replace('\n', ' '))

        with self.amr_list_lock:
            self.amr_list.append(AMR(ip, name, raspi_ip, self.auth_token))

    def remove_amr_from_database(self, ip):
        """Removes an AMR from all tables in the database"""
        # Kan evt. opdeles i flere funktioner, så den sletter fra enkelte tables i stedet for hele databasen

        try: # try except ensures that data will only be deleted if it succeeds in deleting the specific AMR from ALL tables, else nothing is deleted
            with app.app_context():
                delete_user = db.session.query(db_spec.AMR).filter_by(ip=ip).first()
                if delete_user:
                    db.session.delete(delete_user)
                    db.session.commit()
                else:
                    print(f'AMR with IP={ip} does not exist - cannot be deleted')

        except Exception as e:
            print("Error: ", e)

    # Jeg antager at det bare er alt i "data" table i databasen. Kan nemt rettes, hvis nødvendigt.
    def save_amr_data(self, amr_ip, rtt, jitter, packet_loss, quality, noise, rssi, battery, pos_x, pos_y):
        """Saves all network data to database"""
        with app.app_context():
            db.session.add(db_spec.Data(amr_ip=amr_ip,rtt=rtt,jitter=jitter,packet_loss=packet_loss,quality=quality,noise=noise,rssi=rssi,battery=battery,pos_x=pos_x,pos_y=pos_y))
            db.session.commit()

    # Jeg antager at det her er alt der skal i "error" table.
    def save_amr_error(self, amr_ip, error, error_desc):
        """Saves status of amr to database"""

        with app.app_context():
            db.session.add(db_spec.Error(amr_ip=amr_ip,error=error,error_desc=error_desc))
            db.session.commit()

    # Skal laves når AMR class er færdig
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

        # evt. tilføj noget error scoring inden den gemmer til databasen

            self.save_amr_error(amr.ip, error_name, error_desc) # id er ikke en ting mere (skal måske fjernes)

    def measure_network_metrics(self, amr: AMR): # evt. brug tshark?
        """
        Measure RTT, jitter and packet loss using ping.
        Works on typical Linux ping output.
        """
        try:
            result = subprocess.run(
                ["ping", "-c", "4", amr.ip], # sender 4 pakker. (Er det nok?) - TShark er nok bedre til packet loss
                capture_output=True,
                text=True,
                timeout=10000
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
            self.save_amr_error(amr.ip, "NETWORK_MEASUREMENT_ERROR", str(e))
            return 0.0, 0.0, 100.0

    def monitor_one_amr(self, amr: AMR): # Fix this - We get JSON with data not tuple
        """Poll one AMR, measure network/Wi-Fi, and save to database."""

        rtt = None
        jitter = None
        packet_loss = None
        quality = None
        noise = None
        rssi = None
        battery = None
        pos_x = None
        pos_y = None
        status = None

        try:
            #amr.update_status() # vi skal finde ud af om vi bruge get eller update
            # battery = amr.get_battery_percentage()
            # pos_x = amr.get_pos_x()
            # pos_y = amr.get_pos_y()
            status = amr.get_status()
            self.save_api_errors(amr)

        except Exception as e:
            self.save_amr_error(amr.ip, "POLLING_ERROR", str(e))

        try:
            rtt, jitter, packet_loss = self.measure_network_metrics(amr)
        except Exception as e:
            self.save_amr_error(amr.ip, "PING_ERROR", str(e))

        try:
            quality, noise, rssi = RaspberryPi(f"{amr.name}'s rasp", amr.raspi_ip, 5000).get_signal_metrics()
        except Exception as e:
            self.save_amr_error(amr.ip, "RASPI_METRICS_ERROR", str(e))

        if status:
            try:
                battery = status['battery_percentage'] # måske skift til at bruge get, hvis der opstår fejl (burde dog ikke være nødvendigt)
                pos_x = status['position']['x']
                pos_y = status['position']['y']
            except KeyError as e:
                self.save_amr_error(amr.ip, "STATUS_FORMAT_ERROR", f"Missing key: {e}")
        else:
            self.save_amr_error(amr.ip, "GET_STATUS_ERROR", f"{amr}.get_status() failed")

        self.save_amr_data(
            amr_ip=amr.ip,
            rtt=rtt,
            jitter=jitter,
            packet_loss=packet_loss,
            quality=quality,
            noise=noise,
            rssi=rssi,
            battery=battery,
            pos_x=pos_x,
            pos_y=pos_y
        )

        print(
            f"{amr.name} ({amr.ip}) | "
            f"Pos: ({pos_x}, {pos_y}) | "
            f"RTT: {rtt} ms | "
            f"Jitter: {jitter} ms | "
            f"Packet loss: {packet_loss}% | "
            f"RSSI: {rssi} | "
            f"Battery: {battery}"
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
    
    def get_map(self, testing=False):
        if not testing:
            for amr in self.amr_list:
                try:
                    map_data = amr.get_working_map()
                    if isinstance(map_data, dict):
                        return map_data["base_map"]
                    print(map_data)
                except Exception as e:
                    print(e)
            print("WARNING: No map could be loaded from any AMR in the database.")
            return
        else:
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                response_dict = {"guid": "7ecbf116-0d8e-11f1-b640-000129922d00", "session_id": "1a7b2063-0bed-11f1-8343-000129922d00", "name": "AAU SmartLab 2026_02", "base_map": "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", "resolution": 0.05, "origin_x": -23.122, "origin_y": -11.061, "origin_theta": 0.0, "positions": "/v2.0.0/maps/7ecbf116-0d8e-11f1-b640-000129922d00/positions", "paths": "/v2.0.0/maps/7ecbf116-0d8e-11f1-b640-000129922d00/paths", "path_guides": "/v2.0.0/maps/7ecbf116-0d8e-11f1-b640-000129922d00/path_guides", "created_by_id": "mirconst-guid-0000-0004-users0000000", "created_by": "/v2.0.0/users/mirconst-guid-0000-0004-users0000000", "allowed_methods": ["PUT", "GET", "DELETE"], "created_by_name": "Distributor"}
                mock_response.json.return_value = response_dict
                mock_get.return_value = mock_response

                return self.get_map(testing=False) #runs this function but with mock now

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
