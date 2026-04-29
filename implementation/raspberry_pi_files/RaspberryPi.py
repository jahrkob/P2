import requests
from typing import Optional, TypedDict
from internet_device import InternetDevice

class SignalData(TypedDict): # So pylance knows what each key in json has as value
    rssi: float
    signal_strength: float
    noise: Optional[float]

class RaspberryPi(InternetDevice):
    def __init__(self, device_name, ip, port=80):
        super().__init__(device_name, ip)
        self.port = port
        self.__api_key = {
            "Authorization": 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc3NzAzMDA4NSwianRpIjoiMmQ4YmRjMzUtOWU5ZC00NjdiLWIzZmEtMDA5ODBmYTY3NTBmIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6ImRpc3RyaWJ1dG9yIiwibmJmIjoxNzc3MDMwMDg1LCJjc3JmIjoiZWQ1NTkxNmQtNDg3OS00NjZmLTlhMDctZGJlY2Y0N2Y0OTM3In0.-ndt5YYzRl7YvSUk76CSOsn163Plx9NTYEYf0YRneNs'
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
        api_response.raise_for_status() # Raises an HTTPError if the response was an error

        rssi = api_response.json().get('rssi')
        signal_strength = api_response.json().get('signal_strength')
        noise = api_response.json().get('noise')

        return api_response.json(), rssi, signal_strength, noise

##### TESTING #####
name = 'testing_rasp' # can be whatever
ip = '192.168.200.243'
port = 5000 # Only 5000 for testing in reality should be 80
rasp = RaspberryPi(name,ip,port)

print(rasp.get_signal_metrics())
