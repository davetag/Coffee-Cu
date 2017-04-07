from flask import Flask
from flask_mail import Mail, Message
import pyrebase
import os
import json

app = Flask(__name__)
app.config.from_object('config')
app.secret_key = os.urandom(24)

with open('config/databaseConfig.json', 'r') as database_config:
    config = json.load(database_config)

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()

with open('config/emailConfig.json', 'r') as email:
    email_config = json.load(email)

app.config.update(email_config)
mail = Mail(app)

with open('majors.json', 'r') as majors_file:
    majors = json.load(majors_file)

from app import views
