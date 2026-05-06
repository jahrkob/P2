from flask import Flask, request
from flask_restful import Resource, Api, reqparse, fields, marshal_with, abort
from datetime import datetime
from flask_jwt_extended import JWTManager, jwt_required, create_access_token

interface_to_monitor = 'wlan0'

app = Flask(__name__)
jwt = JWTManager(app)
api = Api(app)

app.config['JWT_SECRET_KEY'] = 'distributor_distributor_distributor'

# ##### creating api key #####
# with app.app_context():
#     print(str(create_access_token('distributor',expires_delta=False)))

######## REQUESTS ########

#The format in which the API responses will be given
statusFields = { # for requesting which AMR's there are
    'rssi':fields.Float,
    'quality':fields.Float,
    'noise':fields.Float
}

class Status(Resource):
    @jwt_required()
    @marshal_with(statusFields)
    def get(self): # request status
        return get_wireless_info(interface_to_monitor)


def get_wireless_info(interface="wlan0"):
    with open("/proc/net/wireless") as f:
        lines = f.readlines()

        if not lines[2:]:
            print(f'could not find match for "{interface}" in "/proc/net/wireless"')
            abort(404)

    for line in lines[2:]:
        line.strip().startswith(interface)
        parts = line.split()

        quality = float(parts[2])
        signal = float(parts[3])
        noise = float(parts[4])

        return {
            "rssi": signal,
            "quality": quality,
            "noise": noise if noise != -256.0 else None
        }
            

api.add_resource(Status, '/api/status')

@app.route('/')
def home():
    return '<h1>Flask REST API</h1>'



if __name__ == '__main__':
    @app.before_request
    def log_request_info():
        print("----- Incoming Request -----")
        print("Method:", request.method)
        print("URL:", request.url)
        print("Headers:", dict(request.headers))
        print("Body:", request.get_data())
        print("----------------------------")

    app.run(debug=True,host='0.0.0.0')