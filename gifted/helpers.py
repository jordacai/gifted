import random
import string
from functools import wraps

from flask import session, url_for, flash
from werkzeug.utils import redirect


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('username') is None:
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function


# todo: test redirection and ensure flow is broken on invalid input
def validate(username, password, password_confirm=None, redirect_to='main.login'):
    if not username:
        flash('Username is required!', 'error')
        return redirect(url_for(redirect_to))
    if not password:
        flash('Password is required!', 'error')
        return redirect(url_for(redirect_to))
    if password_confirm is not None and password != password_confirm:
        flash('Passwords must match!', 'error')
        return redirect(url_for(redirect_to))


