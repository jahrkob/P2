import json
import socket
from typing import Optional, TypedDict
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener

from internet_device import InternetDevice


class SignalData(TypedDict):
    rssi: float
    signal_strength: float
    noise: Optional[float]


class RaspberryPi(InternetDevice):
    def __init__(self, device_name, ip, port=80):
        super().__init__(ip, device_name)
        self.port = port
        self.__api_key = {
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc3NzAzMDA4NSwianRpIjoiMmQ4YmRjMzUtOWU5ZC00NjdiLWIzZmEtMDA5ODBmYTY3NTBmIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6ImRpc3RyaWJ1dG9yIiwibmJmIjoxNzc3MDMwMDg1LCJjc3JmIjoiZWQ1NTkxNmQtNDg3OS00NjZmLTlhMDctZGJlY2Y0N2Y0OTM3In0.-ndt5YYzRl7YvSUk76CSOsn163Plx9NTYEYf0YRneNs"
        }

    def get_signal_metrics(self) -> tuple[float, Optional[float], float]:
        """
        Returns signal_strength, noise and rssi from the Raspberry Pi status API.
        """
        request = Request(f"http://{self.ip}:{self.port}/api/status", headers=self.__api_key)

        try:
            with socket.create_connection((self.ip, self.port), timeout=1):
                pass
            opener = build_opener(ProxyHandler({}))
            with opener.open(request, timeout=2) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Raspberry Pi API returned HTTP {e.code}: {body}") from e
        except (TimeoutError, socket.timeout) as e:
            raise RuntimeError(f"Timed out while contacting Raspberry Pi API at {self.ip}:{self.port}") from e
        except OSError as e:
            raise RuntimeError(f"Could not connect to Raspberry Pi API at {self.ip}:{self.port}: {e}") from e
        except URLError as e:
            raise RuntimeError(f"Could not reach Raspberry Pi API at {self.ip}:{self.port}: {e.reason}") from e

        rssi = data.get("rssi")
        signal_strength = data.get("signal_strength", data.get("quality", rssi))
        noise = data.get("noise")

        return signal_strength, noise, rssi


if __name__ == "__main__":
    rasp = RaspberryPi("testing_rasp", "192.168.200.243", 5000)
    print(rasp.get_signal_metrics())
