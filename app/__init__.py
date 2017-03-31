from flask import Flask
from flask_mail import Mail, Message
import pyrebase
import os
import json

app = Flask(__name__)
mail = Mail(app)
app.config.from_object('config')
app.secret_key = os.urandom(24)

with open('config/databaseConfig.json', 'r') as databaseConfig:
    config = json.load(databaseConfig)

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()

with open('config/emailConfig.json','r') as email:
    emailConfig = json.load(email)

app.config.update(emailConfig)
mail = Mail(app)

with open('majors.json', 'r') as majorsFile:
    majors = json.load(majorsFile)

from app import views
