from app import app
from flask_mail import Mail, Message


def send_contact_email(recipient, firstname, lastname, message):
    mail = Mail(app)
    msg = Message(subject='Coffee@CU Email', sender='coffeeatcu@gmail.com',
        recipients=[recipient])

    msg.body = """
    New Message from %s %s
    %s
    """ % (firstname, lastname, message)

    mail.send(msg)
