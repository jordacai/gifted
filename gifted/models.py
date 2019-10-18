from datetime import datetime, timedelta

from gifted import db

participants = db.Table('participants',
                        db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
                        db.Column('event_id', db.Integer, db.ForeignKey('event.id'), primary_key=True))


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(240), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    registered_on = db.Column(db.DateTime(), default=datetime.now())
    is_admin = db.Column(db.Integer, default=0)

    def __repr__(self):
        return '<User id=%r, username=%r, name=%r>' % (self.id, self.username, self.first_name + ' ' + self.last_name)


class Invite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    email = db.Column(db.String(80), nullable=False)
    is_valid = db.Column(db.Integer, default=1)
    created_on = db.Column(db.DateTime(), default=datetime.now())
    expires_on = db.Column(db.DateTime(), default=datetime.now() + timedelta(days=7))
    code = db.Column(db.String(80), nullable=False)
    is_used = db.Column(db.Integer, default=0)

    def __repr__(self):
        return '<Invite id=%r, email=%r, code=%r>' % (self.id, self.email, self.code)


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(240), nullable=False)
    description = db.Column(db.String(1024))
    created_on = db.Column(db.DateTime(), default=datetime.now())
    starts_on = db.Column(db.DateTime())
    ends_on = db.Column(db.DateTime())
    participants = db.relationship('User', secondary=participants, lazy='subquery',
                                   backref=db.backref('events', lazy=True))

    def __repr__(self):
        return '<Event id=%r, title=%r>' % (self.id, self.title)
