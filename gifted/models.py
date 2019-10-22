import random
from copy import copy
from datetime import datetime, timedelta

from gifted import db

participants = db.Table('participants',
                        db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
                        db.Column('event_id', db.Integer, db.ForeignKey('event.id'), primary_key=True))

wishlist = db.Table('wishlist',
                    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
                    db.Column('event_id', db.Integer, db.ForeignKey('event.id'), primary_key=True),
                    db.Column('item_id', db.Integer, db.ForeignKey('item.id'), primary_key=True))


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(240), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    registered_on = db.Column(db.DateTime(), default=datetime.now())
    is_admin = db.Column(db.Integer, default=0)
    wishlist = db.relationship('Item', secondary=wishlist, lazy='subquery', backref=db.backref('items', lazy=True))

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
    users = db.relationship('User', secondary=participants, lazy='subquery',
                            backref=db.backref('events', lazy=True))
    gifters = db.relationship('Gifter', lazy='subquery',
                              backref=db.backref('event', lazy='subquery'))

    def __repr__(self):
        return '<Event id=%r, title=%r>' % (self.id, self.title)

    def is_active(self):
        now = datetime.now()
        return True if self.starts_on < now < self.ends_on else False

    def is_expired(self):
        now = datetime.now()
        return True if now > self.ends_on else False

    def matchmake(self):
        matches = {}
        recipients = copy(self.users)
        random.shuffle(recipients)

        if len(self.users) == 0:
            return None

        if self.users[-1].id == recipients[0].id:
            return self.matchmake()

        for user in self.users:
            # treat recipients as a stack: if the user is shuffled as the recipient, grab the next (i.e. pop(-2))
            if user.id == recipients[-1].id:
                recipient = recipients.pop(-2)
            else:
                recipient = recipients.pop()
            matches[user.id] = recipient.id
        return matches


class Gifter(db.Model):
    gifter_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True, nullable=False)
    giftee_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True, nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), primary_key=True, nullable=False)

    def __repr__(self):
        return '<Gifter %r buys for %r>' % (self.gifter_id, self.giftee_id)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(240), nullable=False)
    price = db.Column(db.Numeric(4, 2), nullable=False)
    location = db.Column(db.String(1024), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    priority = db.Column(db.Integer, default=3)
    is_purchased = db.Column(db.Integer, default=0)

    def __repr__(self):
        return '<Item id=%r, description=%r, price=%r>' % (self.id, self.description, self.price)

