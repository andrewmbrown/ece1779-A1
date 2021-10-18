from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    user = StringField('user', validators=[DataRequired()])
    pwd = PasswordField('pass', validators[DataRequired()])
    remember = BooleanField('remember me')
    submit = SubmitField('login')

