from flask import Flask
from flask_mail import Mail, Message
import pyrebase
import os

app = Flask(__name__)
mail = Mail(app)
app.config.from_object('config')
app.secret_key = os.urandom(24)

mail = Mail(app)

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()

from app import views