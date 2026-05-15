from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api, reqparse, fields, marshal_with, abort
import sqlalchemy as sql
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

INSTANCE_PATH = BASE_DIR / 'instance'
INSTANCE_PATH.mkdir(exist_ok=True)

DB_PATH = INSTANCE_PATH / "database.db"

app = Flask(__name__, instance_relative_config=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'

db = SQLAlchemy(app)
#api = Api(app) # dont need API anymore since it runs on the fleet managers device

###############################################################################################################
########################## Defining tables(classes), their columns and relationships ##########################
###############################################################################################################

class Data(db.Model):
    __tablename__ = 'data'
    id = sql.Column(sql.Integer, primary_key=True)
    amr_ip = sql.Column(sql.String(39),sql.ForeignKey('amr.ip'), nullable=False)
    amr = db.relationship('AMR', back_populates='data')
    timestamp = sql.Column(sql.DateTime, default=datetime.now, nullable=False)
    rtt = sql.Column(sql.Float)
    jitter = sql.Column(sql.Float)
    packet_loss = sql.Column(sql.Float)
    quality = sql.Column(sql.Float)
    noise = sql.Column(sql.Float)
    rssi = sql.Column(sql.Float)
    battery = sql.Column(sql.Float)
    pos_x = sql.Column(sql.Float)
    pos_y = sql.Column(sql.Float)


class AMR(db.Model):
    __tablename__ = 'amr'
    ip = sql.Column(sql.String(39), unique=True, nullable=False, primary_key=True) #accepts ip as string support up to IPv6 length
    name = sql.Column(sql.String(80), nullable=True) #name is optional
    data = db.relationship('Data',back_populates='amr')
    error = db.relationship('Error',back_populates='amr')
    dev_eui = sql.Column(sql.String(80), unique=True, nullable=False)

    def __repr__(self):
        return f'[{id}]: name="{self.name}", ip={self.ip}, device EUI={self.dev_eui}'

class Error(db.Model):
    __tablename__ = 'error'
    id = sql.Column(sql.Integer, primary_key=True)
    amr_ip = sql.Column(sql.String(39),sql.ForeignKey('amr.ip'), nullable=False)
    amr = db.relationship('AMR', back_populates='error')
    timestamp = sql.Column(sql.DateTime, default=datetime.now, nullable=False)
    error = sql.Column(sql.Text, nullable=False)
    error_desc = sql.Column(sql.Text)
