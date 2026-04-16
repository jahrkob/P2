class InternetDevice:
    def __init__(self, device_name, ip_address):
        self.device_name = device_name
        self.ip_address = ip_address

    def __str__(self):
        return f"{self.device_name} ({self.ip_address})"
    
class AMR(InternetDevice):
    def __init__(self, device_name, ip_address, statuscode, status, amr_model, accosiated_raspberry_pi):
        super().__init__(device_name, ip_address)
        self.__status_code = statuscode
        self.__status = status
        self.__amr_model = amr_model
        self.accosiated_raspberry_pi = accosiated_raspberry_pi

    def __str__(self):
        return f"{super().__str__()} - Status Code: {self.__status_code}, Status: {self.__status}, AMR Model: {self.__amr_model}, Associated Raspberry Pi: {self.accosiated_raspberry_pi}"
    
    def get_status_code(self):
        return self.__status_code
    
    def get_status(self):
        return self.__status

class RaspberryPi(InternetDevice):
    def __init__(self, device_name, ip_address, statuscode, status, raspberry_pi_model):
        super().__init__(device_name, ip_address)
        self.__status_code = statuscode
        self.__status = status
        self.__raspberry_pi_model = raspberry_pi_model
        self.__rssi = None

    def __str__(self):
        return f"{super().__str__()} - Status Code: {self.__status_code}, Status: {self.__status}, Raspberry Pi Model: {self.__raspberry_pi_model}"
    
    def get_rssi(self):
        return self.__rssi
    
class NetworkMonitor:
    def __init__(self, fleet_manager_ip):
        self.devices = []
        self.fleet_manager_ip = fleet_manager_ip

    def add_device(self, device):
        self.devices.append(device)

    def display_devices(self):
        for device in self.devices:
            print(device)

    def get_amr_list(self):
        return [device for device in self.devices if isinstance(device, AMR)]
    
    def get_raspberry_pi_list(self):
        return [device for device in self.devices if isinstance(device, RaspberryPi)]
    
    def remove_amr(self, device_name):
        self.devices = [device for device in self.devices if not (isinstance(device, AMR) and device.device_name == device_name)]
    
    def add_amr(self, device_name, ip_address, statuscode, status, amr_model, accosiated_raspberry_pi):
        amr = AMR(device_name, ip_address, statuscode, status, amr_model, accosiated_raspberry_pi)
        self.add_device(amr)
        
    def get_wifi_metrics(self):
        wifi_metrics = {}
        for device in self.devices:
            if isinstance(device, RaspberryPi):
                wifi_metrics[device.device_name] = device.get_rssi()
        return wifi_metrics
    

class DataGrapher:
    def __init__(self):
        self.data = []

    def add_data(self, data_point):
        self.data.append(data_point)

    def display_data(self):
        for data_point in self.data:
            print(data_point)