import os

from flask import Flask
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from gifted.helpers import validate, login_required

db = SQLAlchemy()
mail = Mail()
migrate = Migrate()


def create_app():
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    with app.app_context():
        app.config.from_pyfile('config.py')
    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    with app.app_context():
        from .admin.routes import admin
        from .main.routes import main
        app.register_blueprint(admin)
        app.register_blueprint(main)
        return app


if __name__ == '__main__':
    create_app().run()
