import requests
from typing import Optional, TypedDict
from internet_device import InternetDevice

class SignalData(TypedDict): # So pylance knows what each key in json has as value
    rssi: float
    signal_strength: float
    noise: Optional[float]

class RaspberryPi(InternetDevice):
    def __init__(self, device_name, ip, port=80):
        super().__init__(ip=ip, device_name=device_name)
        self.port = port
        self.__api_key = {
            "Authorization": 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc3ODA1MTMwMywianRpIjoiMmJiYTUyMjEtZWE2Ni00ZjRmLTk5ZDgtYTIwYjNjZDQzNTRlIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6ImRpc3RyaWJ1dG9yIiwibmJmIjoxNzc4MDUxMzAzLCJjc3JmIjoiODQ2OGQzYjktYWEyYi00OWQ2LWIzMjEtZTZiYzJiYWUyY2YwIn0.UTr3yRfM3xxwJzOQ63YNGEHyFJDIpj8bKpnnL-7-m3I'
        }

    def get_signal_metrics(self) -> SignalData:
        """
        Returns:
            json: A json containing:
                rssi (float)
                signal_strength (float)
                noise (Optional[float]): Noise level, null if unavailable.
        """
        url = f'http://{self.ip}:{self.port}/api/status'
        print(f'{self}: get {url}')
        api_response = requests.get(url,headers=self.__api_key)
        api_response.raise_for_status() # Raises an HTTPError if the response was an error

        return api_response.json()

if __name__ == "__main__":
    ##### TESTING #####
    name = 'testing_rasp' # can be whatever
    ip = '192.168.0.96'
    port = 5000 # Only 5000 for testing in reality should be 80
    rasp = RaspberryPi(device_name=name,ip=ip,port=port)

    print(rasp.get_signal_metrics())
