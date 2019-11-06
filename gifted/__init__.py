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
csp = {
 'default-src': [
        '\'self\'',
        '*.bootstrapcdn.com',
        '*.jquery.com',
        '*.cloudflare.com'
    ]
}
Talisman(app, content_security_policy=csp)

from gifted import models
from .admin.routes import admin
from .main.routes import main
app.register_blueprint(admin)
app.register_blueprint(main)


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
