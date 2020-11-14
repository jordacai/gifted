import random
import string
from collections import defaultdict
from functools import wraps

from flask import session, url_for, flash
from werkzeug.utils import redirect


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_id') is None:
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function


def generate_code(size=10, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def group_by(iterable, projection):
    result = defaultdict(list)
    for item in iterable:
        result[projection(item)].append(item)
    return result


def validate(username, password, password_confirm=None, redirect_to='main.login'):
    if not username:
        flash('Username is required!', 'warning')
        return redirect(url_for(redirect_to))
    if not password:
        flash('Password is required!', 'warning')
        return redirect(url_for(redirect_to))
    if password_confirm is not None and password != password_confirm:
        flash('Passwords must match!', 'warning')
        return redirect(url_for(redirect_to))
