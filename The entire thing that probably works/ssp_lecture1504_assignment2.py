"""
This code defines classes to represent internet-connected devices, specifically Autonomous Mobile Robots (AMRs) and Raspberry Pi devices. It also includes a NetworkMonitorer class to manage the fleet of AMRs and a DataGrapher class to handle data visualization.

Classes:
- InternetDevice: A base class for all internet-connected devices.
- AMR: A class representing Autonomous Mobile Robots.
- RaspberryPi: A class representing Raspberry Pi devices.
- NetworkMonitorer: A class to monitor the network and manage the fleet of AMRs.
- DataGrapher: A class to graph the data collected from the AMRs and Raspberry Pi.

Example usage is provided at the end of the code to demonstrate how to create instances of these classes and interact with them.

Doctest:
>>> device = InternetDevice("Test Device", "192.168.1.10")
>>> print(device)
Test Device (192.168.1.10)
"""

class InternetDevice:
    """Base class for all internet-connected devices."""
    def __init__(self, device_name, ip_address):
        self.device_name = device_name
        self.ip_address = ip_address

    def __str__(self):
        return f"{self.device_name} ({self.ip_address})"
    
class AMR(InternetDevice):
    """Autonomous Mobile Robot (AMR) class inheriting from InternetDevice."""
    def __init__(self, device_name, ip_address, status_code, status, amr_model, associated_raspberry_pi):
        super().__init__(device_name, ip_address)
        self.__status_code = status_code
        self.__status = status
        self.__amr_model = amr_model
        self.associated_raspberry_pi = associated_raspberry_pi

    def __str__(self):
        return f"{super().__str__()} - Status Code: {self.__status_code}, Status: {self.__status}, AMR Model: {self.__amr_model}, Associated Raspberry Pi: {self.associated_raspberry_pi}"
    
    def get_status_code(self):
        return self.__status_code
    
    def get_status(self):
        """Get battery percentage and position of the AMR."""
        battery_percentage = self.__status.get('battery_percentage', 'Unknown')
        position = self.__status.get('position', 'Unknown')
        return battery_percentage, position

class RaspberryPi(InternetDevice):
    """Raspberry Pi class inheriting from InternetDevice."""
    def __init__(self, device_name, ip_address, status_code, status, raspberry_pi_model):
        super().__init__(device_name, ip_address)
        self.__status_code = status_code
        self.__status = status
        self.__raspberry_pi_model = raspberry_pi_model
        self.__rssi = None

    def __str__(self):
        return f"{super().__str__()} - Status Code: {self.__status_code}, Status: {self.__status}, Raspberry Pi Model: {self.__raspberry_pi_model}"
    
    def get_rssi(self):
        return self.__rssi
    
class NetworkMonitorer:
    """Class to monitor the network and manage the fleet of AMRs."""
    def __init__(self, fleet_manager_ip, raspberry_pi):
        self.__amr_list = []
        self.__raspberry_pi = raspberry_pi
        self.fleet_manager_ip = fleet_manager_ip

    def __str__(self):
        amr_info = "\n".join(str(amr) for amr in self.__amr_list)
        base_info = f"Fleet Manager IP: {self.fleet_manager_ip}\nRaspberry Pi: {self.__raspberry_pi}\nAMRs:"
        if amr_info:
            return f"{base_info}\n{amr_info}"
        return base_info

    def get_amr_list(self):
        return self.__amr_list

    def add_amr(self, amr):
        self.__amr_list.append(amr)

    def remove_amr(self, amr):
        if amr in self.__amr_list:
            self.__amr_list.remove(amr)

    def get_wifi_metrics(self):
        """Simulate retrieval of Wi-Fi metrics such as RSSI."""
        # In a real implementation, this would involve network calls to the Raspberry Pi
        # For simulation purposes, we will just return a random RSSI value
        import random
        rssi_value = random.randint(-100, -30)  # Simulated RSSI value in dBm
        self.__raspberry_pi._RaspberryPi__rssi = rssi_value  # Update the Raspberry Pi's RSSI value

class DataGrapher:
    """Class to graph the data collected from the AMRs and Raspberry Pi."""
    def __init__(self):
        self.data = []

    def add_data(self, data_point):
        self.data.append(data_point)

    def display_data(self):
        for data_point in self.data:
            print(data_point)

# Example usage
if __name__ == "__main__":
    import doctest
    doctest.testmod()

    # Create instances and demonstrate functionality
    raspberry_pi = RaspberryPi("Raspberry Pi 4", "192.168.1.100", 200, {"status": "online"}, "Model B")
    amr = AMR("AMR 1", "192.168.1.101", 200, {"status": "online", "battery_percentage": 80, "position": (10, 20)}, "Model X", raspberry_pi)
    network_monitorer = NetworkMonitorer("192.168.1.1", raspberry_pi)
    network_monitorer.add_amr(amr)
    print(network_monitorer)
    network_monitorer.get_wifi_metrics()
    print(f"Updated RSSI: {raspberry_pi.get_rssi()} dBm")
    data_grapher = DataGrapher()
    data_grapher.add_data({"timestamp": "2024-06-01 12:00:00", "battery_percentage": 80, "position": (10, 20), "rssi": raspberry_pi.get_rssi()})
    data_grapher.display_data()
