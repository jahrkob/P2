import json
import socket
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener

from internet_device import InternetDevice


class AMR(InternetDevice):
    """Autonomous Mobile Robot."""

    def __init__(self, ip, name="", raspi_ip="", auth_token=None, api_version="v2.0.0"):
        super().__init__(ip)
        self.name = name
        self.raspi_ip = raspi_ip
        self.auth_token = auth_token
        self.api_version = api_version
        self.base_url = f"http://{ip}/api/{api_version}"
        self.status_code = None
        self.status = {}
        self.headers = {
            "Authorization": auth_token,
            "Accept-Language": "en-US",
            "accept": "application/json",
        }

    def __str__(self):
        return f"{self.name or 'AMR'} ({self.ip}) - RasPi: {self.raspi_ip or 'ukendt'}"

    def _request_json(self, path, timeout=2):
        headers = {key: value for key, value in self.headers.items() if value}
        request = Request(f"{self.base_url}{path}", headers=headers)

        try:
            with socket.create_connection((self.ip, 80), timeout=1):
                pass
            opener = build_opener(ProxyHandler({}))
            with opener.open(request, timeout=timeout) as response:
                self.status_code = response.status
                body = response.read().decode("utf-8")
                return json.loads(body) if body else {}
        except HTTPError as e:
            self.status_code = e.code
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"AMR API returned HTTP {e.code}: {body}") from e
        except (TimeoutError, socket.timeout) as e:
            raise RuntimeError(f"Timed out while contacting AMR API at {self.ip}") from e
        except OSError as e:
            raise RuntimeError(f"Could not connect to AMR API at {self.ip}: {e}") from e
        except URLError as e:
            raise RuntimeError(f"Could not reach AMR API at {self.ip}: {e.reason}") from e

    def get_status(self):
        self.status = self._request_json("/status")
        return self.status

    def update_status(self):
        """Fetch live status from the AMR API."""
        return self.get_status()

    def get_map(self):
        return self._request_json("/map")

    def get_battery_percentage(self):
        return self.status.get("battery_percentage")

    def get_position(self):
        return self.status.get("position", {}) or {}

    def get_pos_x(self):
        return self.get_position().get("x")

    def get_pos_y(self):
        return self.get_position().get("y")

    def get_state_text(self):
        return self.status.get("state_text")

    def get_mode_text(self):
        return self.status.get("mode_text")

    def get_robot_name(self):
        return self.status.get("robot_name")

    def get_map_id(self):
        return self.status.get("map_id")

    def get_errors(self):
        return self.status.get("errors", []) or []


if __name__ == "__main__":
    amr = AMR("192.168.100.51")
    amr.get_status()
    amr.get_map()
