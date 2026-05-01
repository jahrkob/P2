from network_monitorer import *
from amr import *
from data_grapher import *
from internet_device import *
from raspberry_pi_files.RaspberryPi import *

if __name__ == "__main__":

    monitor = NetworkMonitorer(
        fleet_manager_ip="192.168.100.123",
        database="/implementation/database_files/instance/database.db",
        auth_token="Basic ZGlzdHJpYnV0b3I6NjJmMmYwZjFlZmYxMGQzMTUyYzk1ZjZmMDU5NjU3NmU0ODJiYjhlNDQ4MDY0MzNmNGNmOTI5NzkyODM0YjAxNA"
    )

    # amr_mir3 = AMR(
    #     ip="192.168.100.51", 
    #     name="MiR 3", 
    #     raspi_ip="192.168.x.x"
    # )

    monitor.add_amr_to_database(
        ip="192.168.100.51",
        name="MiR 3",
        raspi_ip="192.168.x.x"
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

    # # Én enkelt runde
    # for amr in monitor.amr_list:
    #     monitor.monitor_one_amr(amr=amr_1)

    # # Kontinuerlig monitorering
    # monitor.active_monitoring(interval_seconds=5)