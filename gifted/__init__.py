import logging
import os
import re
from datetime import date
from logging.handlers import RotatingFileHandler
from urllib.parse import urlparse

import metadata_parser
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
Talisman(app, content_security_policy=None)

from gifted import models, errors
from .admin.routes import admin
from .main.routes import main

app.register_blueprint(admin)
app.register_blueprint(main)


def template_function(func):
    app.jinja_env.globals[func.__name__] = func
    return func


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
