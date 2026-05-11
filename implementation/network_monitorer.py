import sqlite3, json, time, subprocess, sqlalchemy # sqlite3 er ikke længere i brug, og internet_device er fjernet (bruges gennem raspi og amr)
from datetime import datetime
from amr import AMR
from raspberry_pi_files.RaspberryPi import RaspberryPi

from database_files.Database_specification import app, db
import database_files.Database_specification as db_spec

class NetworkMonitorer:
    """Class to monitor the network and manage the fleet of AMRs."""

    def __init__(self, fleet_manager_ip, database, auth_token = None): # evt kom tilbage til init, da vi lige skal være sikre på hvilke parametre den skal bruge
        self.fleet_manager_ip = fleet_manager_ip
        self.database = database
        self.auth_token = auth_token
        self.amr_list = []
        self.load_amr_database()

    def __str__(self):
        amr_info = "\n".join([str(amr) for amr in self.amr_list])
        return (
            f"Fleet Manager IP: {self.fleet_manager_ip}\n\n"
            f"AMRs:\n{amr_info if amr_info else 'Ingen AMR fundet'}"
        )

    def load_amr_database(self):
        with app.app_context():
            print(db.session.query(db_spec.AMR).all())

    def add_amr_to_database(self, ip, name, raspi_ip):
        try:
            with app.app_context():
                # print("DB URL:", db.engine.url) # for testing
                db.session.add(db_spec.AMR(ip=ip,name=name,raspi_ip=raspi_ip))
                db.session.commit()
            # self.amr_list.append(AMR(ip=ip,name=name,raspi_ip=raspi_ip)) # add to list in memory
        
        except sqlalchemy.exc.IntegrityError as e:
            print(str(e).replace('\n', ' '))

        self.amr_list.append(name) # Kan også være ip, men er i tvivl om hvad der er smartest, eller om det reelt set bare kan være ligegyldigt

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

            self.save_amr_error(amr.ip, error_name, error_desc) # id er ikke en ting mere (skal måske fjernes)

    def measure_network_metrics(self, amr: AMR): # Der skal laves amr objekter med AMR classen
        """
        Measure RTT, jitter and packet loss using ping.
        Works on typical Linux ping output.
        """
        try:
            result = subprocess.run(
                ["ping", "-c", "4", amr.ip], # sender 4 pakker. (Er det nok?)
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
            quality, noise, rssi = RaspberryPi.get_signal_metrics(amr) # this line
        except Exception as e:
            self.save_amr_error(amr.ip, "RASPI_METRICS_ERROR", str(e))

        self.save_amr_data(
            amr_ip=amr.ip,
            rtt=rtt,
            jitter=jitter,
            packet_loss=packet_loss,
            quality=quality,
            noise=noise,
            rssi=None,
            battery=status['battery_percentage'],
            pos_x=status['position']['x'],
            pos_y=status['position']['x']
        )

        print(
            f"{amr.name} | "
            f"Battery: {battery} | "
            f"Pos: ({status['position']['x']}, {status['position']['y']}) | "
            f"RTT: {rtt} ms | "
            f"Jitter: {jitter} ms | "
            f"Packet loss: {packet_loss}% | "
            f"RSSI: {rssi} | "
            f"Battery: {status['battery_percentage']}"
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
