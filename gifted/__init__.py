import logging
import os
from datetime import date
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman

from config import Config
from gifted.helpers import validate, login_required

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)
app.extensions['mail'].debug = 0
Talisman(app, content_security_policy=None)

from gifted import models, errors
from .admin.routes import admin
from .main.routes import main

app.register_blueprint(admin)
app.register_blueprint(main)

if app.config['LOG_TO_STDOUT']:
    del app.logger.handlers[:]
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s'))
    stream_handler.setLevel(logging.INFO)
    app.logger.addHandler(stream_handler)
else:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/gifted.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

app.logger.setLevel(logging.INFO)
app.logger.info('Gifted startup')


def template_function(func):
    app.jinja_env.globals[func.__name__] = func
    return func


@template_function
def child_check(event_children, my_children):
    return any(child in event_children for child in my_children)


@template_function
def pretty_date(d):
    return d.strftime('%x') if isinstance(d, date) else d


@template_function
def pretty_datetime(d):
    return d.strftime('%c') if isinstance(d, date) else d


@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'Transaction': models.Transaction,
        'Pair': models.Pair,
        'User': models.User,
        'Invite': models.Invite,
        'Event': models.Event,
        'Item': models.Item
    }
