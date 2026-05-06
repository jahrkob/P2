from API_raspberry_pi import app
from RaspberryPi import RaspberryPi
import threading
import os,sys
import time

def run_test():
    app_thread = threading.Thread(
        target=app.run,
        kwargs={"host":'127.0.0.1',"debug":True,"use_reloader":False}, 
        daemon=True
    )
    app_thread.start()

    time.sleep(2) # avoid request being made before server is up
    
    """
    We dont have to think about the case in which the server boots up slower than requests 
    as this is the same as a user requesting something without the server being up
    """

    for i in range(10):
        rasp = RaspberryPi(device_name='test_device',ip='127.0.0.1',port=5000)
        result = rasp.get_signal_metrics()
        if list(result.keys()) != ['rssi','quality','noise']:
            raise KeyError(f"Result keys do not match expected keys ['rssi','quality','noise'] got {list(result.keys())}")
        for key in result.keys():
            if type(result[key]) != float:
                raise ValueError(f"Result from raspberry pi for key '{key}' is of type {type(result[key])} but float type was expected")
        time.sleep(0.5)

run_test()
