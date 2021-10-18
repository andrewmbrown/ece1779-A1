import os 
basedir = os.path.abspath(os.path.dirname(__file__))

IMG_LOCATION = '../../dbimages/'

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'test_key'
    # SQLALCHEMY_DATABASE_URI = 'mysql://root:ece1779pass@localhost/appdb'
    IMG_FOLDER = IMG_LOCATION