from flask import render_template, request, flash, url_for, session
from werkzeug import security
from werkzeug.utils import redirect

from gifted import app, login_required, validate, db
from gifted.models import User


@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        validate(email, password)

        user = User.query.filter_by(email=email).first()

        if user is None:
            flash('Username does not exist!', 'error')
            return redirect(url_for('login'))

        # password is valid, proceed to set session cookie and redirect to index
        # otherwise, flash a friendly message
        if security.check_password_hash(pwhash=user.password, password=password):
            session['username'] = request.form.get('username')
            flash('Logged in successfully', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid password!', 'error')
            return redirect(url_for('login'))

    # it's a GET, render the template
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        validate(email, password)

        user = User(email=email, password=security.generate_password_hash(password),
                    first_name=first_name, last_name=last_name)
        db.session.add(user)
        db.session.commit()

        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))

    # it's a GET, render the template
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))
