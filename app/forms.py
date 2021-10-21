from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User

"""
File to create different types of form fillers for the web application
"""

# Login form specifies data input when logging into the site
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


# Registration form specifies data innput for registering new users,
# Only accessed by admin
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    # check to see if username is valid and is unique
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    # check to see if email is valid and is unique
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

    # a command the admin can run to see all userids and usernames
    def print_users(self):
        users = User.query.all()
        for u in users:
            print(u.id, u.username)

class RecoveryForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    newpassword = PasswordField('New Password', validators=[DataRequired()])
    submit = SubmitField('Reset Account')


class PictureForm(FlaskForm):
    picture = FileField('Upload picture', validators=[FileRequired(), 
                                    FileAllowed(['jpg', 'jpeg', 'png'], "You can upload only JPG, JPEG and PNG") ])
    submit = SubmitField('Upload')
