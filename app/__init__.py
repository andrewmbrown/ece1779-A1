from flask import Flask
from config import Config 

app = Flask(__name__)  # create app of instance Flask
app.config.from_object(Config)

from app import routes