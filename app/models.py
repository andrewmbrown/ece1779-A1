from app import db 
# hashing passwords
from werkzeug.security import check_password_hash, generate_password_hash
# authenticating users, checking active status, anonyimity, id
from flask_login import UserMixin
from app import login

# File that specifies the database tables and behaviour
# Each class is a table, with some logic implemented to ensure proper usage
# NOTE: anytime db classes are changed you must: 
# either delete the migrations folder or properly migrate and upgrade database

class User(UserMixin, db.Model):
    '''
    Model for User table entry

    id -> user ID 
    username -> unique username
    email -> unique email
    password_hash -> stored hash of provided password
    '''
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    # gallery = db.relationship('ImageLocation', backref='uploader', lazy='dynamic')
    def __repr__(self):
        return '<User {}>'.format(self.username)
    
    # Class now has method to do secure password verification
    # also to check password (hash again and check if they match)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)



@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class ImageLocation(db.Model):
    '''
    Model for ImageLocation table entry

    id -> image location ID 
    location -> full path location of image (in /static/images/...)
    htmlpath -> html safe path
    filename -> true filename
    user_id -> user associated to this image (user with this id will have this img
        appear in their gallery)
    '''
    id = db.Column(db.Integer, primary_key=True)
    # we do not store images in DB, we instead store the path to the image
    location = db.Column(db.String(2048), index=True)
    htmlpath = db.Column(db.String(2048), index=True)
    filename = db.Column(db.String(2048), index=True)
    # user_id is foreign key
    user_id = db.Column(db.Integer)
    def __repr__(self):
        return '<Image Path: {}>'.format(self.location)