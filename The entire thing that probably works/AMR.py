import requests

class MiR200:
    def __init__(self):
        self.base_url = "http://192.168.100.51/api/v2.0.0"
        self.headers = {
            "Authorization": "Basic ZGlzdHJpYnV0b3I6NjJmMmYwZjFlZmYxMGQzMTUyYzk1ZjZmMDU5NjU3NmU0ODJiYjhlNDQ4MDY0MzNmNGnmOTI5NzkyODM0YjAxNA==",
            "Accept-Language": "en-US",
            "accept": "application/json"
        }

    def get_status(self):
        response = requests.get(f"{self.base_url}/status", headers=self.headers)

        if response.status_code == 200:
            data = response.json()

            print("Position:", data["position"])
            print("Battery %:", data["battery_percentage"])
            print("State:", data["state_text"])
            return data
        else:
            print(f"Error {response.status_code}: {response.text}")
    
    def get_map(self):
        response = requests.get(f"{self.base_url}/map", headers=self.headers)

        if response.status_code == 200:
            map = response.json()
            
            print("url:", map["position"])
            print("guid:", map["battery_percentage"])
            print("name:", map["state_text"])

        else:
            print(f"Error {response.status_code}: {response.text}")

MiR200.get_status()