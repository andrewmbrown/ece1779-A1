from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User
from app.apputilities import *

"""
File to create different types of form fillers for the web application
"""

# Login form specifies data input when logging into the site
class LoginForm(FlaskForm):
    '''
    LoginForm doc string test
    '''
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

class URLPictureForm(FlaskForm):
    urlpicture = StringField('URL to Upload Picture', validators=[DataRequired()])
    submit = SubmitField('Upload')

    def validate_urlpicture(self, urlpicture):
        new_url = urlpicture.data
        if urlpicture.data[:8] != "https://" and urlpicture.data[:7] != "http://":
            new_url = "https://" + urlpicture.data 
        viable_image = check_img_url(new_url)
        viable_image_truth = viable_image[0]
        if not viable_image_truth:
            raise ValidationError("The image URL you entered was not viable: either it has a typo, is not a png, jpg, or jpeg, is not accessible for security reasons, or is not registered as one of these image types in its file header. Please try another URL.")
        
