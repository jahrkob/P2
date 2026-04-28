from network_monitorer import *
from amr import *
from data_grapher import *
from internet_device import *
from raspberry_pi_files.RaspberryPi import *

if __name__ == "__main__":
    monitor = NetworkMonitorer(
        fleet_manager_ip="192.168.1.1",
        database="database_files/instance/database.db",
        auth_token="Basic ZGlzdHJpYnV0b3I6NjJmMmYwZjFlZmYxMGQzMTUyYzk1ZjZmMDU5NjU3NmU0ODJiYjhlNDQ4MDY0MzNmNGNmOTI5NzkyODM0YjAxNA"
    )

    amr_1 = AMR(
        id=1, 
        amr_ip="192.168.0.100", 
        name="AMR TEST OBJECT", 
        raspi_ip="192.168.1.101"
    )

    monitor.add_amr_to_database(
        ip="192.168.0.100",
        name="AMR #1",
        raspi_ip="192.168.1.101"
    )

    print(monitor)