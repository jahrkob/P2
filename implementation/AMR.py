import requests
from internet_device import InternetDevice

class AMR(InternetDevice):
    def __init__(self, id, ip, amr_ip, name, raspi_ip):
        super().__init__(ip)
        self.id = id
        self.amr_ip = amr_ip
        self.name = name
        self.raspi_ip = raspi_ip
        self.base_url = f"http://{ip}/api/v2.0.0"
        self.headers = {
            "Authorization": "Basic ZGlzdHJpYnV0b3I6NjJmMmYwZjFlZmYxMGQzMTUyYzk1ZjZmMDU5NjU3NmU0ODJiYjhlNDQ4MDY0MzNmNGNmOTI5NzkyODM0YjAxNA==",
            "Accept-Language": "en-US",
            "accept": "application/json"
        }

    # __init__ kan evt. se sådan ud hvis update status skal bruges
    # def __init__(self, id, amr_ip, name, raspi_ip, api_version="v2.0.0"):
    #     super().__init__(name, amr_ip)
    #     self.id = id
    #     self.amr_ip = amr_ip
    #     self.name = name
    #     self.raspi_ip = raspi_ip
    #     self.auth_token = "ZGlzdHJpYnV0b3I6NjjmMmYwZjFlZmYxMGQzMTUyYzk1ZjZmMDU5NjU3NmU0ODJiYjhINDQ4MDY0MzNmNGNmOTI5NzkyODM0YjAxNA=="
    #     self.api_version = api_version

    #     self.status_code = None
    #     self.status = {}

    # Måske overflødigt
    # def __str__(self):
    #     battery = self.get_battery_percentage()
    #     state = self.get_state_text()
    #     mode = self.get_mode_text()
    #     return (
    #         f"{self.name} ({self.amr_ip}) - "
    #         f"RasPi IP: {self.raspi_ip}, "
    #         f"Battery: {battery}, State: {state}, Mode: {mode}"
    #     )

    def get_status(self):
        response = requests.get(f"{self.base_url}/status", headers=self.headers)

        if response.status_code == 200:
            data = response.json()

            # map_id er måske ikke så vigtig
            '''
            print("Position:", data["position"])
            print("Battery %:", data["battery_percentage"])
            print("State:", data["state_text"])
            print("Errors:", data["errors"])
            print("robot_name:", data["robot_name"])
            print("map_id", data["map_id"])
            '''

            return data
        else:
            return(f"Error {response.status_code}: {response.text}")
    
    # status funktionen kan evt. se således ud. Vi skal lige finde ud af om vi bruge get eller update
    def update_status(self):
        """Fetch live status from the AMR API."""
        headers = {
            "accept": "application/json",
            "Accept-Language": "en_US"
        }

        if self.auth_token:
            headers["Authorization"] = f"Basic {self.auth_token}"

        url = f"http://{self.amr_ip}/api/{self.api_version}/status"
        response = requests.get(url, headers=headers, timeout=5)

        self.status_code = response.status_code
        response.raise_for_status()
        self.status = response.json()
    
    def get_map(self):
        response = requests.get(f"{self.base_url}/map", headers=self.headers)

        if response.status_code == 200:
            map = response.json()
            
            '''
            print("url:", map["url"])
            print("guid:", map["guid"])
            print("name:", map["name"])
            '''

            return map

        else:
            return(f"Error {response.status_code}: {response.text}")
        
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

    def get_errors(self):
        if not self.status: # Opdaterer status hvis den ikke har en endnu, da errors ellers ville være tom. Kan evt. fjernes
            self.update_status() 
        return self.status.get("errors", [])

if __name__ == "__main__":
    amr = AMR("192.168.100.51")
    amr.get_status()
    amr.get_map()
