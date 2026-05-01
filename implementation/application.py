from pathlib import Path

from network_monitorer import NetworkMonitorer


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    database_path = base_dir / "database_files" / "instance" / "database.db"

    monitor = NetworkMonitorer(
        fleet_manager_ip="192.168.100.123",
        database=str(database_path),
        auth_token="Basic ZGlzdHJpYnV0b3I6ZTNiMGM0NDI5OGZjMWMxNDlhZmJmNGM4OTk2ZmI5MjQyN2FlNDFlNDY0OWI5MzRjYTQ5NTk5MWI3ODUyYjg1NQ==",
        raspi_port=5000,
        monitor_wifi=False,
    )
    monitor.initialize_database(drop_existing=False)

    monitor.add_amr_to_database(
        ip="192.168.100.51",
        name="MiR 3",
        raspi_ip="",
    )

    print(monitor)
    print(f"\nDatabase: {monitor.database}\n")

    if monitor.amr_list:
        monitor.monitor_one_amr(monitor.amr_list[0])
        monitor.print_latest_database_rows()
