from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api, reqparse, fields, marshal_with, abort
import sqlalchemy as sql
from datetime import datetime


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
api = Api(app)

# class UserModel(db.Model):
#     # make sure the json POST and Get requests match the capitalization of these variables
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(80), unique=True, nullable=False)
#     email = db.Column(db.String(80), unique=True, nullable=False)


#     def __repr__(self):
#         return f"User(id = {self.id}, name = {self.name}, email = {self.email})"

class Data(db.Model):
    __tablename__ = 'data'
    id = sql.Column(sql.Integer, primary_key=True)
    amr_id = sql.Column(sql.Integer,sql.ForeignKey('amr.id'), nullable=False)
    amr = db.relationship('amr', back_populates='data')
    timestamp = sql.Column(sql.DateTime, default=datetime.now, nullable=False)
    rtt = sql.Column(sql.Float)
    jitter = sql.Column(sql.Float)
    packet_loss = sql.Column(sql.Float)
    signal_strength = sql.Column(sql.Float)
    noise = sql.Column(sql.Float)
    rssi = sql.Column(sql.Float)
    battery = sql.Column(sql.Float)
    pos_x = sql.Column(sql.Float)
    pos_y = sql.Column(sql.Float)


class AMR(db.Model):
    __tablename__ = 'amr'
    # make sure the json POST and Get requests match the capitalization of these variables
    id = sql.Column(sql.Integer, primary_key=True)
    ip = sql.Column(sql.String(39), unique=True, nullable=False) #accepts ip as string support up to IPv6 length
    name = sql.Column(sql.String(80), nullable=True) #name is optional
    data = db.relationship('data',back_populates='amr')
    error = db.relationship('error',back_populates='amr')
    associated_raspberry_pi = sql.Column(sql.String(80), unique=True, nullable=False)

    def __repr__(self):
        return f'[{id}]: name="{self.name}", ip={self.ip}, raspberry_pi={self.associated_raspberry_pi}'

class Error(db.Model):
    __tablename__ = 'error'
    id = sql.Column(sql.Integer, primary_key=True)
    amr_id = sql.Column(sql.Integer,sql.ForeignKey('amr.id'), nullable=False)
    amr = db.relationship('error', back_populates='data')
    timestamp = sql.Column(sql.DateTime, default=datetime.now, nullable=False)
    error = sql.Column(sql.Text, nullable=False)
    error_desc = sql.Column(sql.Text)




# user_args = reqparse.RequestParser()
# user_args.add_argument('name', type=str, required=True, help='Name cannot be blank') # if this isnt fulfilled we return 400 (bad request)
# user_args.add_argument('email', type=str, required=True, help='Email cannot be blank') # if this isnt fulfilled we return 400 (bad request)

# userFields = {
#     'id':fields.Integer,
#     'name':fields.String(80),
#     'email':fields.String(80)
# }

# class Users(Resource):
#     @marshal_with(userFields)
#     def get(self): # request list of all users
#         users = UserModel.query.all()
#         return users
    
#     @marshal_with(userFields)
#     def post(self): # create new user
#         args = user_args.parse_args() # use the user_args we defined
#         user = UserModel(name=args['name'], email=args['email'])
#         db.session.add(user)
#         db.session.commit()
#         users = UserModel.query.all() # get all users (for debugging purposes, wouldnt be there in real scenarios)
#         return users, 201 # returns list of users and the status 201 which means 'created'
    

# class User(Resource):
#     @marshal_with(userFields) # marshal_with seems to make functions correlate to the different interactions with servers (get,post,put,patch,delete)
#     def get(self,id): # request information about ONE user
#         user = UserModel.query.filter_by(id=id).first()
#         if not user:
#             abort(404)
#         return user
    
#     @marshal_with(userFields)
#     def delete(self,id):
#         user = UserModel.query.filter_by(id=id).first()
#         if not user:
#             abort(404)
#         db.session.delete(user)
#         db.session.commit() # this updates the database
#         users = UserModel.query.all() # get all users (for debugging purposes, wouldnt be there in real scenarios)
#         return users # returns list of users and the status 201 which means 'created'

# api.add_resource(Users, '/api/users/') # runs the get function in Users and sends the response to the client
# api.add_resource(User, '/api/users/<int:id>') # <int:id> mean we expect an integer at this location and we parse it into the get User get function

# @app.route('/')
# def home():
#     return '<h1>Flask REST API</h1>'

if __name__ == '__main__':
    app.run(debug=True)
