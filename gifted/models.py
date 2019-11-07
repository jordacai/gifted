import random
import string
from copy import copy
from datetime import datetime, timedelta

from gifted import db

event_user = db.Table('event_user',
                      db.Column('event_id', db.Integer, db.ForeignKey('event.id')),
                      db.Column('user_id', db.Integer, db.ForeignKey('user.id')))


def generate_code(size=8, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    item_id = db.Column(db.Integer, db.ForeignKey('item.id', ondelete='CASCADE'))
    gifter_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    giftee_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    transacted_on = db.Column(db.DateTime(), default=datetime.now())

    def __repr__(self):
        return '<Transaction id=%r, event_id=%r, item_id=%r, gifter_id=%r, giftee_id=%r>' % \
               (self.id, self.event_id, self.item_id, self.gifter_id, self.giftee_id)


class Pair(db.Model):
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), primary_key=True)
    gifter_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    giftee_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Pair event_id=%r, gifter_id=%r, giftee_id=%r>' % (self.event_id, self.gifter_id, self.giftee_id)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(240), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    registered_on = db.Column(db.DateTime(), default=datetime.now())
    is_admin = db.Column(db.Integer, default=0)
    transactions = db.relationship('Transaction', backref='user', foreign_keys=[Transaction.gifter_id])
    pair = db.relationship('Pair', backref='gifter', uselist=False, foreign_keys=[Pair.gifter_id])

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
    users = db.relationship('User',
                            secondary=event_user,
                            backref=db.backref('events', lazy=True),
                            lazy=True)
    pairs = db.relationship('Pair', backref='event', lazy=True)

    def __repr__(self):
        return '<Event id=%r, title=%r>' % (self.id, self.title)

    def is_active(self):
        now = datetime.now()
        return True if self.starts_on < now < self.ends_on else False

    def is_expired(self):
        now = datetime.now()
        return True if now > self.ends_on else False

    def matchmake(self, users):
        giftees = copy(users)
        random.shuffle(giftees)

        if len(users) == 0:
            return None

        if users[-1] == giftees[0]:
            return self.matchmake(users)

        for gifter in users:
            # treat recipients as a stack: if the user is shuffled as the recipient, grab the next (i.e. pop(-2))
            if gifter == giftees[-1]:
                giftee = giftees.pop(-2)
            else:
                giftee = giftees.pop()

            pair = Pair.query.filter_by(event_id=self.id, gifter_id=gifter).first()
            if pair is not None:
                pair.giftee_id = giftee
            else:
                pair = Pair(event_id=self.id, gifter_id=gifter, giftee_id=giftee)

            db.session.add(pair)
            db.session.commit()


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    description = db.Column(db.String(240), nullable=False)
    price = db.Column(db.Numeric(5, 2), nullable=False)
    location = db.Column(db.String(1024), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    priority = db.Column(db.Integer, default=3)
    is_purchased = db.Column(db.Integer, default=0)
    transaction = db.relationship('Transaction', uselist=False, backref='item', cascade='all,delete')

    def __repr__(self):
        return '<Item id=%r, description=%r, price=%r>' % (self.id, self.description, self.price)
