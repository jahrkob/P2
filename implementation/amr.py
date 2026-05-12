import requests
from internet_device import InternetDevice
import threading

class AMR(InternetDevice):
    """Autonomous Mobile Robot."""

    def __init__(self, ip, name, raspi_ip, auth_token):
        super().__init__(ip)
        self.name = name
        self.raspi_ip = raspi_ip
        self.auth_token = auth_token
        self.base_url = f"http://{ip}/api/v2.0.0"
        self.headers = {
            "Authorization": auth_token,
            "Accept-Language": "en-US",
            "accept": "application/json"
        }
        self.status = {}
        self.is_on = True
        self.lock = threading.Lock()

    def get_status(self, timeout=2):
        response = requests.get(f"{self.base_url}/status", headers=self.headers, timeout=timeout)

        response.raise_for_status()
        status = response.json()

        with self.lock:
            self.status = status
            self.status_code = response.status_code
            self.is_on = True

        # map_id er måske ikke så vigtig

        # print("Position:", data["position"])
        # print("Battery %:", data["battery_percentage"])
        # print("State:", data["state_text"])
        # print("Errors:", data["errors"])
        # print("robot_name:", data["robot_name"])
        # print("map_id", data["map_id"])

        return self.status
        # else:
        #     return(f"Error {response.status_code}: {response.text}")
        
    def get_errors(self):
        if not self.status: # Opdaterer status hvis den ikke har en endnu, da errors ellers ville være tom. Kan evt. fjernes
            self.get_status() 
        
        with self.lock:
            return self.status.get("errors", []) or []

    def get_battery_percentage(self):
        return self.status.get("battery_percentage")

    def get_position(self):
        return self.status.get("position", {})

    def get_pos_x(self):
        return self.get_position().get("x")

    def get_pos_y(self):
        return self.get_position().get("y")

    def get_state_text(self):
        return self.status.get("state_text")

    def get_mode_text(self):
        return self.status.get("mode_text")

    # def get_map(self):
    #     response = requests.get(f"{self.base_url}/map", headers=self.headers)

    #     if response.status_code == 200:
    #         map = response.json()
            
    #         '''
    #         print("url:", map["url"])
    #         print("guid:", map["guid"])
    #         print("name:", map["name"])
    #         '''

    #         return map

    #     else:
    #         return(f"Error {response.status_code}: {response.text}")

# if __name__ == "__main__":
#     amr = AMR("192.168.100.51")
#     amr.get_status()
#     amr.get_map()
