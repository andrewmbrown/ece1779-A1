from app import db 
# hashing passwords
from werkzeug.security import check_password_hash, generate_password_hash
# authenticating users, checking active status, anonyimity, id
from flask_login import UserMixin
from app import login

# NOTE: anytime db classes are changed you must: 
# either delete the migrations folder or properly migrate and upgrade database

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    gallery = db.relationship('ImageLocation', backref='uploader', lazy='dynamic')
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
    id = db.Column(db.Integer, primary_key=True)
    # we do not store images in DB, we instead store the path to the image
    location = db.Column(db.String(1024), index=True, unique=True)
    # user_id is foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    def __repr__(self):
        return '<Image Path: {}>'.format(self.location)