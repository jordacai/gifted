import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ['FLASK_KEY']
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'gifted.sqlite')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_TO_STDOUT = os.environ.get('FLASK_LOG_TO_STDOUT')
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USERNAME = os.environ['FLASK_MAIL_USER']
    MAIL_PASSWORD = os.environ['FLASK_MAIL_PASSWORD']
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
