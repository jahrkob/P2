import MiR_REST_base
import json
import time
import csv
import os
from datetime import datetime

header = ['x','y','orientation','mission_text','hh:mm:ss']

log_file_name = time.strftime("%d_%m_%y__%H_%M_%S", time.localtime()) + ".csv"

file_path = os.path.join("status_logs",log_file_name)

writeFile = open(file_path,'w')
errorFile = open(file_path + "_errors", 'w')

def LogPositionData():
    writer = csv.writer(writeFile)
    writer.writerow(header)

    while True:
        status_json = json.loads(MiR_REST_base.getMiRStatus())

        t = datetime.now()

        try:
            tempRow = [round(status_json['position']['x'],2),round(status_json['position']['y'],2),round(status_json['position']['orientation'],2), status_json['mission_text'], t.isoformat()]

            writer.writerow(tempRow)

            print(tempRow)

            time.sleep(.1)
        except KeyError as e:
            print("failed get position: {}".format(e))
            errorFile.write("{}: {}".format(t.isoformat(), json.dumps(status_json)))

try:
    LogPositionData()
except KeyboardInterrupt:
    print(" You pressed ctrl c!")
    print("saved to",file_path)
    writeFile.close()
    errorFile.close()