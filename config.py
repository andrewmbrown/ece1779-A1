import os 
basedir = os.path.abspath(os.path.dirname(__file__))

IMG_LOCATION = '../../dbimages/'

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    #SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    #    'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:ece1779pass@ece1779-db-1.cnsxozjecorh.us-east-1.rds.amazonaws.com:3306/ece1779-db-1"
    SQLALCHEMY_TRACK_MODIFICATIONS = False