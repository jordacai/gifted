from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from gifted.helpers import validate, login_required

app = Flask(__name__)
app.secret_key = b',w\xac\x87\xee\x9e\x83gf46s\x8c\xdbU\x1d'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
db.create_all()
migrate = Migrate(app, db)

import gifted.views


if __name__ == '__main__':
    app.run()
