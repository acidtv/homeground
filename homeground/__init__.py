from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# init flask app
app = Flask(__name__)

# configure flask
app.config.from_envvar('HOMEGROUND_SETTINGS')
app.config['SQLALCHEMY_DATABASE_URI'] = app.config['DB_ENGINE']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

# init db
db = SQLAlchemy(app)

from . import views, cli
