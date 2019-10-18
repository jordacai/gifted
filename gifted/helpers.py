import random
import string
from copy import deepcopy
from functools import wraps

from flask import session, url_for, flash
from werkzeug.utils import redirect


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('username') is None:
            return redirect(url_for('views.login'))
        return f(*args, **kwargs)
    return decorated_function


def generate_code(size=8, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


# todo: test redirection and ensure flow is broken on invalid input
def validate(username, password, password_confirm=None, redirect_to='views.login'):
    if not username:
        flash('Username is required!', 'error')
        return redirect(url_for(redirect_to))
    if not password:
        flash('Password is required!', 'error')
        return redirect(url_for(redirect_to))
    if password_confirm is not None and password != password_confirm:
        flash('Passwords must match!', 'error')
        return redirect(url_for(redirect_to))


def matchmake(gifters):
    pairs = []
    giftees = deepcopy(gifters)
    random.shuffle(giftees)

    if gifters[-1].id == giftees[0].id:
        return matchmake(gifters)

    for gifter in gifters:
        # treat giftees as a stack: if the gifter is shuffled as the giftee, grab the next (i.e. pop(-2))
        if gifter.id == giftees[-1].id:
            giftee = giftees.pop(-2)
        else:
            giftee = giftees.pop()
        pair = {
            'gifter': gifter,
            'giftee': giftee
        }
        pairs.append(pair)
    return pairs
