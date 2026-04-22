import requests

BASE_URL = "http://192.168.100.51/api/v2.0.0"

HEADERS = {
    "Authorization": "Basic ZGlzdHJpYnV0b3I6NjJmMmYwZjFlZmYxMGQzMTUyYzk1ZjZmMDU5NjU3NmU0ODJiYjhlNDQ4MDY0MzNmNGnmOTI5NzkyODM0YjAxNA==",
    "Accept-Language": "en-US",
    "accept": "application/json"
}

def get_status():
    response = requests.get(f"{BASE_URL}/status", headers=HEADERS)
    
    if response.status_code == 200:
        data = response.json()
        print("Position:", data["position"])
        print("Battery %:", data["battery_percentage"])
        print("State:", data["state_text"])
        return data
    else:
        print(f"Error {response.status_code}: {response.text}")

get_status()