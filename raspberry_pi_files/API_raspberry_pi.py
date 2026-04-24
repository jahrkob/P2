from flask import Flask
from flask_restful import Resource, Api, reqparse, fields, marshal_with, abort
from datetime import datetime
from flask_jwt_extended import JWTManager, jwt_required, create_access_token

app = Flask(__name__)
jwt = JWTManager(app)
api = Api(app)

app.config['JWT_SECRET_KEY'] = 'distributor'

##### creating api key #####
# with app.app_context():
#     print(str(create_access_token('distributor')))

######## REQUESTS ########

#The format in which the API responses will be given
statusFields = { # for requesting which AMR's there are
    'rssi':fields.String,
    'signal_strength':fields.String,
    'noise':fields.String
}


class Status(Resource):
    @marshal_with(statusFields)
    def get(self): # request status
        return get_wireless_info()

@jwt_required()
def get_wireless_info(interface="wlan0"):
    with open("/proc/net/wireless") as f:
        lines = f.readlines()

    for line in lines[2:]:
        if line.strip().startswith(interface):
            parts = line.split()

            signal = float(parts[3])
            noise = float(parts[4])

            return {
                "rssi": signal,
                "signal_strength": signal,
                "noise": noise if noise != -256.0 else None
            }

api.add_resource(Status, '/api/status')

@app.route('/')
def home():
    return '<h1>Flask REST API</h1>'

if __name__ == '__main__':
     app.run(debug=True,host='0.0.0.0')
