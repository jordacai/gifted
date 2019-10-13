import itertools
import random
import string
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


def randomize(users):
    pairs = []
    ids = [user.id for user in users]
    count = len(ids)
    while count:
        gifter = random.choice(ids)
        giftee = random.choice(ids)
        if gifter != giftee:
            pairs.append({
                'gifter': gifter,
                'giftee': giftee
            })
            ids.remove(giftee)
            count = count - 2
    return pairs

