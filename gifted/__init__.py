import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman

from config import Config
from gifted.helpers import validate, login_required


app = Flask(__name__)
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
