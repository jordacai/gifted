from functools import wraps

from flask import session, url_for
from werkzeug.utils import redirect


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('username') is None:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
