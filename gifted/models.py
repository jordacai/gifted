from datetime import datetime

from gifted.__init__ import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(240), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    registered_on = db.Column(db.DateTime(), default=datetime.now())
    updated_on = db.Column(db.DateTime(), default=datetime.now())

    def __repr__(self):
        return '<User id=%r, email=%r>' % (self.id, self.email)
