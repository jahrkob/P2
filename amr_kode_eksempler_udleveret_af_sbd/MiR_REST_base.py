import requests
import json
import random
import time

x_coord = 0.0
y_coord = 0.0

mir_ip = "http://192.168.100.2"

headers = { 
    'Accept-Language': 'en-US',
    'Accept': 'application,json',
    'Authorization' : 'Basic RGlzdHJpYnV0b3I6NjJmMmYwZjFlZmYxMGQzMTUyYzk1ZjZmMDU5NjU3NmU0ODJiYjhlNDQ4MDY0MzNmNGNmOTI5NzkyODM0YjAxNA==', 
}

data = {
    'mission_id': '1766ba7e-f650-11e9-a9a2-94c691a4a502',
    'parameters': [
    	{
        'input_name': 'namedPlace', 'value': 'eddec850-f55d-11e9-95fe-94c691a4a502'
    	}
    ],
    'message': '',
    'priority': 1
}

move = {
    'mission_id': 'db913046-0a06-11eb-8521-0001299f16e3',
    'parameters': [
    	{
        'input_name': 'x', 'value': x_coord
        },
        {
        'input_name': 'y', 'value': y_coord
    	}
    ],
    'message': '',
    'priority': 1
}

moveRelative = {
    "mission_id": "973f4c30-5311-11ea-87f7-000129922d00",
    "parameters": [
    	{"input_name": "x", "value":0 }, 
    	{"input_name": "y", "value":0 }, 
    	{"input_name": "ori", "value":179}
    ],
    "message": "",
    "priority": 1
}

namedLocation = {
    "mission_id": "08c8eb8a-5311-11ea-87f7-000129922d00",
    "parameters": [
    	{
        "input_name": "namedPlace", "value": "b2318e91-0d04-11ea-87ad-94c691a4a502"
    	}
    ],
    "message": "",
    "priority": 1
}

clear_error = {
    'clear_error' : True,
}

un_pause = {
    'state_id' : 3
}


class Robot_State(object):
    def __init__(self,json_def):
        s = json.loads(json_def)
        self.battery_percentage = None if 'battery_percentage' not in s else s['battery_percentage']
        self.state_text = None if 'state_text' not in s else s['state_text']
        self.errors = None if 'errors' not in s else s['errors']

def setMiRIP(_ip):
    global mir_ip
    mir_ip = "http://"+_ip
    print("set mir ip to: ",mir_ip)

def jprint(obj):
    text = json.dumps(obj, sort_keys=True, indent=4)
    print(text)

def set_position(_x,_y): # _x_coord,_y_coord
    print("x y", _x,_y)

    move['parameters'] = [
    	{
        'input_name': 'x', 'value': _x
        },
        {
        'input_name': 'y', 'value': _y
    	}
    ]

def setMissionGuid(guid):
    namedLocation['parameters'] = [
        {"input_name": "namedPlace", "value": guid}
    ]

def getMiRStatus():
    return requests.get(mir_ip+"/api/v2.0.0/status", headers=headers).text
    #print(response.status_code)
    #jprint(response.json())

def getMiR(apiArgument):
    response = requests.get(mir_ip+"/api/v2.0.0/"+apiArgument, headers=headers)
    print(response.status_code)
    jprint(response.json())

def getMiRPositions():
    response = requests.get(mir_ip+"/api/v2.0.0/positions", headers=headers)
    print(response.status_code)
    #jprint(response.json())
    return response.text

# def hasError():
#     print("error")

def isPaused():
    response = requests.get(mir_ip+"/api/v2.0.0/status", headers=headers)
    print("Pause STATUS",response.status_code)
    robot_state = Robot_State(response.text)
    return robot_state.state_text == "Pause"

def isReady():
    time.sleep(0.5)
    response = requests.get(mir_ip+"/api/v2.0.0/status", headers=headers)
    robot_state = Robot_State(response.text)
    print(robot_state.state_text)
    return robot_state.state_text == "Ready"

def hasError():
    response = requests.get(mir_ip+"/api/v2.0.0/status", headers=headers)
    robot_state = Robot_State(response.text)
    #print robot_state.errors
    return "obstacle" in str(robot_state.errors) or "Failed" in str(robot_state.errors)

def unPause():
    response = requests.put(mir_ip+"/api/v2.0.0/status", headers=headers,json=un_pause)
    print(response.status_code, "un paused")

def clearError():
    response = requests.put(mir_ip+"/api/v2.0.0/status", headers=headers,json=clear_error)
    print(response.status_code, "error cleared")

def postMiR(_json_string): 
    response = requests.post(mir_ip+"/api/v2.0.0/mission_queue", headers=headers,json=_json_string)
    
    time.sleep(1)
    # print("has error",hasError())

    if(hasError()):
        clearError()
        unPause()
        time.sleep(.3)
        # postMiR("mission_queue")
    #print(response.status_code)
    jprint(response.json())
    
    print("------------")
    # getMiR("status")


def postMiRLocation(guid):
    setMissionGuid(guid)
    response = requests.post(mir_ip+"/api/v2.0.0/mission_queue", headers=headers,json=namedLocation)
    print(response.status_code)

def postMiRRotation():
    response = requests.post(mir_ip+"/api/v2.0.0/mission_queue", headers=headers,json=moveRelative)
    time.sleep(1)
    print(response.status_code,"rotating...")
