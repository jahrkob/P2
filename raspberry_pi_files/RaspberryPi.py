import requests
from typing import Optional, TypedDict

class SignalData(TypedDict): # So pylance knows what each key in json has as value
    rssi: float
    signal_strength: float
    noise: Optional[float]

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
        self.__api_key = {
            "Authorization": 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc3NzAyODk3OCwianRpIjoiZTdlOWRhMmEtMDY1NS00NzQxLTliNjktZDgwY2E1MGZmMmU0IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6ImRpc3RyaWJ1dG9yIiwibmJmIjoxNzc3MDI4OTc4LCJjc3JmIjoiOTI0MmM1ZDAtZTA3MC00Mzc0LWIwNTQtOGZmM2VkZDExZTJkIiwiZXhwIjoxNzc3MDI5ODc4fQ.z6pxf4CNbpKieDmQKCMo2LPYrroQcsy_5aBui_Oem-0'
        }

    def get_signal_metrics(self) -> SignalData:
        """
        Returns:
            json: A json containing:
                rssi (float)
                signal_strength (float)
                noise (Optional[float]): Noise level, null if unavailable.
        """
        api_response = requests.get(f'http://{self.ip}:{self.port}/api/status',headers=self.__api_key)
        return api_response.json()

##### TESTING #####
name = 'testing_rasp' # can be whatever
ip = '192.168.200.243'
port = 5000 # Only 5000 for testing in reality should be 80
rasp = RaspberryPi(name,ip,port)

print(rasp)

print(rasp.get_signal_metrics())
