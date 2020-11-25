import random
from copy import copy
from datetime import datetime, timedelta

from sqlalchemy import func

from gifted import db

event_user = db.Table('event_user',
                      db.Column('event_id', db.Integer, db.ForeignKey('event.id')),
                      db.Column('user_id', db.Integer, db.ForeignKey('user.id')))

event_admin = db.Table('event_admin',
                       db.Column('event_id', db.Integer, db.ForeignKey('event.id')),
                       db.Column('user_id', db.Integer, db.ForeignKey('user.id')))

event_child = db.Table('event_child',
                       db.Column('event_id', db.Integer, db.ForeignKey('event.id')),
                       db.Column('user_id', db.Integer, db.ForeignKey('user.id')))


class Pair(db.Model):
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), primary_key=True)
    gifter_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    giftee_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Pair event_id=%r, gifter_id=%r, giftee_id=%r>' % (self.event_id, self.gifter_id, self.giftee_id)


class Reset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    code = db.Column(db.String(80), nullable=False)
    created_on = db.Column(db.DateTime(), default=datetime.now())
    expires_on = db.Column(db.DateTime(), default=datetime.now() + timedelta(days=1))

    def __repr__(self):
        return '<Reset id=%r, user_id=%r, code=%r>' % (self.id, self.user_id, self.code)

    def is_expired(self):
        now = datetime.now()
        return True if now > self.expires_on else False


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    registrar_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(240), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    registered_on = db.Column(db.DateTime(), default=datetime.now())
    is_admin = db.Column(db.Integer, default=0)
    pair = db.relationship('Pair', backref='gifter', uselist=False, foreign_keys=[Pair.gifter_id])
    registrar = db.relationship('User', remote_side=id, foreign_keys=[registrar_id])
    parent = db.relationship('User', remote_side=id, foreign_keys=[parent_id])
    children = db.relationship('User', primaryjoin='User.id == User.parent_id', foreign_keys=[parent_id],
                               remote_side=[parent_id])

    def __repr__(self):
        return '<User id=%r, username=%r, name=%r>' % (self.id, self.username, self.get_full_name())

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    item_id = db.Column(db.Integer, db.ForeignKey('item.id', ondelete='CASCADE'))
    gifter_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    giftee_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    transacted_on = db.Column(db.DateTime(), default=datetime.now())
    gifter = db.relationship('User', uselist=False, foreign_keys=[gifter_id])
    giftee = db.relationship('User', uselist=False, foreign_keys=[giftee_id])

    def __repr__(self):
        return '<Transaction id=%r, event_id=%r, item_id=%r, gifter_id=%r, giftee_id=%r>' % \
               (self.id, self.event_id, self.item_id, self.gifter_id, self.giftee_id)

    @classmethod
    def get_user_liability(cls, event_id, user_id):
        stmt = func.sum(Item.price).filter(Item.event_id == event_id, Item.id == Transaction.item_id,
                                           Transaction.gifter_id == user_id)
        total_result = db.session.query(stmt).first()
        if total_result is not None and total_result[0] is not None:
            return total_result[0]
        else:
            return 0

    @classmethod
    def get_user_total(cls, event_id, user_id):
        stmt = func.sum(Item.price).filter(Item.event_id == event_id, Item.id == Transaction.item_id,
                                           Item.user_id == user_id)
        total_result = db.session.query(stmt).first()
        if total_result is not None and total_result[0] is not None:
            return total_result[0]
        else:
            return 0


class Invite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    invited_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    email = db.Column(db.String(80), nullable=False)
    created_on = db.Column(db.DateTime(), default=datetime.now())
    expires_on = db.Column(db.DateTime(), default=datetime.now() + timedelta(days=7))
    code = db.Column(db.String(80), nullable=False)
    is_admin = db.Column(db.Integer, default=0)
    is_used = db.Column(db.Integer, default=0)

    def __repr__(self):
        return '<Invite id=%r, email=%r, code=%r, is_admin=%r>' % (self.id, self.email, self.code, self.is_admin)

    def is_expired(self):
        now = datetime.now()
        return True if now > self.expires_on else False


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
    admins = db.relationship('User',
                             secondary=event_admin,
                             backref=db.backref('administration', lazy=True),
                             lazy=True)
    children = db.relationship('User',
                               secondary=event_child,
                               backref=db.backref('child_events', lazy=True),
                               lazy=True)
    pairs = db.relationship('Pair', backref='event', lazy=True)
    invites = db.relationship('Invite', backref='event', lazy=True)

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

        if len(users) == 0 or len(users) == 1:
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
    location = db.Column(db.String(1024))
    image_url = db.Column(db.String(1024))
    image = db.Column(db.LargeBinary)
    priority = db.Column(db.String(40), default='medium')
    notes = db.Column(db.String(1024))
    transaction = db.relationship('Transaction', uselist=False, backref='item', cascade='all,delete')

    def __repr__(self):
        return '<Item id=%r, description=%r, price=%r, transaction=%r>' % \
               (self.id, self.description, self.price, self.transaction)

    @classmethod
    def get_wishlist_total(cls, event_id, user_id):
        stmt = func.sum(Item.price).filter(Item.event_id == event_id, Item.user_id == user_id)
        total_result = db.session.query(stmt).first()
        if total_result is not None and total_result[0] is not None:
            return total_result[0]
        else:
            return 0

    @classmethod
    def get_wishlist_totals(cls, event_id):
        return Item.query.with_entities(Item.user_id, func.sum(Item.price).label('total')).filter_by(
            event_id=event_id).group_by(Item.user_id).all()
