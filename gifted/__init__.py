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

if not app.debug:
    if app.config['LOG_TO_STDOUT']:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        app.logger.addHandler(stream_handler)
    else:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/gifted.log',
                                           maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Gifted startup')


def template_function(func):
    app.jinja_env.globals[func.__name__] = func
    return func


@template_function
def pretty_date(d):
    return d.strftime('%x') if isinstance(d, date) else d


@template_function
def pretty_datetime(d):
    return d.strftime('%c') if isinstance(d, date) else d


@template_function
def get_image_url_from_metadata(url):
    if is_amazon_domain(url):
        return get_amazon_image_url(url)
    else:
        try:
            page = metadata_parser.MetadataParser(url=url, search_head_only=False)
            return page.get_metadata_link('image')
        except Exception as e:
            app.logger.warn(f'Could not fetch image metadata from {url}. {e}')
            return None


def is_amazon_domain(s):
    url = urlparse(s)
    return True if url is not None and url.hostname == 'www.amazon.com' else False


def get_amazon_image_url(url):
    img_url = 'https://ws-na.amazon-adsystem.com/widgets/q?_encoding=UTF8&MarketPlace=US' \
              '&ASIN={}&ServiceVersion=20070822&ID=AsinImage&WS=1&Format=SL150'
    asin_dp = re.search(r'(?<=dp/)[A-Z0-9]{10}', url)
    asin_gp = re.search(r'(?<=gp/product/)[A-Z0-9]{10}', url)

    if asin_dp:
        return img_url.format(asin_dp.group(0))
    elif asin_gp:
        return img_url.format(asin_gp.group(0))
    else:
        return None


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
