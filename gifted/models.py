from datetime import datetime, timedelta

from gifted import db
from gifted.helpers import generate_code


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(240), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    registered_on = db.Column(db.DateTime(), default=datetime.now())
    is_admin = db.Column(db.Integer, default=0)

    def __repr__(self):
        return '<User id=%r, username=%r>' % (self.id, self.username)


class Invite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), nullable=False)
    valid = db.Column(db.Integer, default=1)
    created = db.Column(db.DateTime(), default=datetime.now())
    expires = db.Column(db.DateTime(), default=datetime.now() + timedelta(days=7))
    code = db.Column(db.String(80), default=generate_code())

    def __repr__(self):
        return '<Invite id=%r, email=%r, code=%r>' % (self.id, self.email, self.code)
