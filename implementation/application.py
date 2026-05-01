from network_monitorer import *
from amr import *
from data_grapher import *
from internet_device import *
from raspberry_pi_files.RaspberryPi import *

from database_files.Database_specification import app,db

if __name__ == "__main__":
    with app.app_context():
      db.drop_all() # remove current tables in database.db
      db.create_all() # create new tables in database.db

    monitor = NetworkMonitorer(
        fleet_manager_ip="192.168.100.123",
        database="database_files\instance\database.db",
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

    print(monitor)

    # # Én enkelt runde
    # for amr in monitor.amr_list:
    #     monitor.monitor_one_amr(amr=amr_1)

    # # Kontinuerlig monitorering
    # monitor.active_monitoring(interval_seconds=5)