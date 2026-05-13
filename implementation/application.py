from network_monitorer import *
from amr import *
from data_grapher import *
from internet_device import *
from raspberry_pi_files.RaspberryPi import *
import time
import requests


def monitor_amr_status(monitor: NetworkMonitorer, amr: AMR, interval_seconds=1, response_timeout_seconds=2):
    while True:
        try:
            amr.get_status(timeout=response_timeout_seconds)
            amr.is_on = True

            for error in amr.get_errors():
                monitor.save_amr_error(amr.ip, "API_ERROR", str(error))

        except requests.exceptions.Timeout:
            amr.is_on = False
            monitor.save_amr_error(
                amr.ip,
                "AMR_OFF",
                f"No response received within {response_timeout_seconds} seconds"
            )

        except Exception as error:
            try:
                errors = amr.get_errors()
            except Exception:
                errors = []

            if errors:
                for api_error in errors:
                    monitor.save_amr_error(amr.ip, "API_ERROR", str(api_error))
            else:
                monitor.save_amr_error(amr.ip, "POLLING_ERROR", str(error))

        time.sleep(interval_seconds)

if __name__ == "__main__":

    monitor = NetworkMonitorer(
        fleet_manager_ip="192.168.100.123",
        database="/implementation/database_files/instance/database.db",
        auth_token="Basic ZGlzdHJpYnV0b3I6NjJmMmYwZjFlZmYxMGQzMTUyYzk1ZjZmMDU5NjU3NmU0ODJiYjhlNDQ4MDY0MzNmNGNmOTI5NzkyODM0YjAxNA"
    )

    amr_mir3 = AMR(
        ip="192.168.100.51", 
        name="MiR 3", 
        raspi_ip="192.168.x.x",
        auth_token=monitor.auth_token
    )

    monitor.add_amr_to_database(
        ip=amr_mir3.ip,
        name=amr_mir3.name,
        raspi_ip=amr_mir3.raspi_ip
    )

    monitor.add_amr_to_database(
        ip="192.168.100.52",
        name="MiR 4",
        raspi_ip="192.168.x.y"
    )

    #monitor.save_amr_data()

    print(monitor)

    monitor.remove_amr_from_database("192.168.100.52")

    print(monitor)

    # Én enkelt runde
    monitor.monitor_one_amr(amr=amr_mir3)

    # Kontinuerlig monitorering af AMR-status hvert sekund
    monitor_amr_status(monitor, amr_mir3)