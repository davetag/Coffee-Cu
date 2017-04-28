from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed, FileField
from wtforms import (StringField, PasswordField, validators, Form, TextField,
    TextAreaField, SubmitField, BooleanField, SelectField)
from app import majors


class LoginForm(FlaskForm):
    email = StringField('email', [validators.Email()])
    password = PasswordField('password')


class SignupForm(FlaskForm):
    firstname = StringField('First Name', [validators.Length(min=1, max=50)])
    lastname = StringField('Last Name', [validators.Length(min=1, max=50)])
    email = StringField('Email Address', [
        validators.Email(),
        validators.Regexp(r'.+(columbia|barnard)\.edu$',
        message="Please fill in a Columbia-affiliated email")
    ])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match'),
        validators.Length(min=6) # Firebase will complain otherwise
    ])
    confirm = PasswordField('Repeat Password')


class ContactForm(Form):
  message = TextAreaField("Message",  [validators.Required("Please enter a message.")])
  submit = SubmitField("Send")


class ResetPasswordForm(FlaskForm):
    email = StringField('email', [validators.Email()])


class ProfileForm(FlaskForm):
    photo = FileField('Profile picture', validators=[
            FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
        ])
    school = SelectField('School', choices=[
            ('cc', 'Columbia College'),
            ('seas', 'Columbia Engineering'),
            ('barnard', 'Barnard College'),
            ('gs', 'General Studies')
        ])
    year = SelectField('Year', choices=[
            ('2017', '2017'),
            ('2018', '2018'),
            ('2019', '2019'),
            ('2020', '2020')
        ])
    major = SelectField('Major', [validators.DataRequired()],
        choices=[(key, majors[key]) for key in majors])
    about = TextAreaField('Tell the world a little bit more about yourself',
        [validators.Length(max=400), validators.DataRequired()])
    likes = TextAreaField('What do you like?',
        [validators.Length(max=150), validators.DataRequired()])
    contactfor = TextAreaField('What are some things people should contact you for?',
        [validators.Length(max=250), validators.DataRequired()])
