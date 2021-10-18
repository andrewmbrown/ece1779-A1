from app import db 

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    salt = db.Column(db.Integer, nullable=False)
    gallery = db.relationship('ImageLocation', backref='uploader', lazy='dynamic')
    def __repr__(self):
        return '<User {}>'.format(self.username)

class ImageLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(1024), index=True, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    def __repr__(self):
        return '<Image Path: {}>'.format(self.location)