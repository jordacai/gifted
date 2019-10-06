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


def validate(username, password):
    if not username:
        flash('Username is required!', 'error')
        return redirect(url_for('views.login'))
    if not password:
        flash('Password is required!', 'error')
        return redirect(url_for('views.login'))
