from network_monitorer import NetworkMonitorer
from amr import AMR

nm = NetworkMonitorer("", "database.db", "ZGlzdHJpYnV0b3I6NjJmMmYwZjFlZmYxMGQzMTUyYzk1ZjZmMDU5NjU3NmU0ODJiYjhlNDQ4MDY0MzNmNGNmOTI5NzkyODM0YjAxNA==")

# nm.add_amr_to_database("192.168.100.123", "AMR_1", "192.168.200.123")
# nm.add_amr_to_database("192.168.100.135", "AMR_2", "192.168.200.126")
# nm.add_amr_to_database("192.168.100.121", "AMR_3", "192.168.200.125")

# nm.remove_amr_from_database("192.168.100.123")
# nm.remove_amr_from_database("192.168.100.135")
# nm.remove_amr_from_database("192.168.100.121")

# nm.save_amr_data("192.168.100.123", 10, 20, 30, 40, 50, 60, 70, 3, 6)

# nm.save_amr_error("192.168.100.123", "low battery", "battery is under 5%")

print(nm)

nm.load_amr_database()

amr_mir3 = AMR(
    ip="192.168.100.51", 
    name="MiR 3", 
    raspi_ip="192.168.x.x",
    auth_token="ZGlzdHJpYnV0b3I6NjJmMmYwZjFlZmYxMGQzMTUyYzk1ZjZmMDU5NjU3NmU0ODJiYjhlNDQ4MDY0MzNmNGNmOTI5NzkyODM0YjAxNA=="
)

print(nm.amr_list)

nm.monitor_one_amr(amr_mir3)
