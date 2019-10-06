from flask import (
    Blueprint, flash, render_template, request, session,
    url_for)
from werkzeug import security
from werkzeug.utils import redirect

from gifted import login_required, validate, db
from gifted.models import User

bp = Blueprint('views', __name__)


@bp.route('/')
@login_required
def index():
    return render_template('index.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        validate(username, password)

        user = User.query.filter_by(username=username).first()

        if user is None:
            flash('Username does not exist!', 'error')
            return redirect(url_for('views.login'))

        # password is valid, proceed to set session cookie and redirect to index
        # otherwise, flash a friendly message
        if security.check_password_hash(pwhash=user.password, password=password):
            session['username'] = request.form.get('username')
            session['is_admin'] = user.is_admin
            flash('Logged in successfully', 'success')
            return redirect(url_for('views.index'))
        else:
            flash('Invalid password!', 'error')
            return redirect(url_for('views.login'))

    # it's a GET, render the template
    return render_template('login.html')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        validate(username, password)

        user = User(username=username, password=security.generate_password_hash(password),
                    first_name=first_name, last_name=last_name)
        db.session.add(user)
        db.session.commit()

        flash('Account created successfully!', 'success')
        return redirect(url_for('views.login'))

    # it's a GET, render the template
    return render_template('register.html')


@bp.route('/admin')
def admin():
    return render_template('admin.html')


@bp.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('views.login'))
