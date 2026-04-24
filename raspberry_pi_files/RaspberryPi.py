import requests

class InternetDevice:
    """Base class for all internet-connected devices."""

    def __init__(self, device_name, ip):
        self.device_name = device_name
        self.ip = ip # ip address

    def __str__(self):
        return f"{self.device_name} ({self.ip})"


class RaspberryPi(InternetDevice):
    def __init__(self, device_name, ip, port=80):
        super().__init__(device_name, ip)
        self.port = port
        self.__rssi = None
        self.__signal_strength = None
        self.__noise = None

    def get_status(self):
        api_response = requests.get(f'http://{self.ip}:{self.port}/api/status')
        return api_response.json()

##### TESTING #####
name = 'testing_rasp' # can be whatever
ip = '192.168.200.243'
port = 5000 # Only 5000 for testing in reality should be 80
rasp = RaspberryPi(name,ip,port)

print(rasp)

print(rasp.get_status())
