from datetime import datetime

from flask import Flask, render_template, request, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug import security
from werkzeug.utils import redirect

from helpers import login_required

app = Flask(__name__)
app.secret_key = b',w\xac\x87\xee\x9e\x83gf46s\x8c\xdbU\x1d'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gifted.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(240), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    registered_on = db.Column(db.DateTime(), default=datetime.now())
    updated_on = db.Column(db.DateTime(), default=datetime.now())

    def __init__(self, username, password, first_name, last_name):
        self.username = username
        self.password = password
        self.first_name = first_name
        self.last_name = last_name

    def __repr__(self):
        return '<User id=%r, username=%r>' % (self.id, self.username)


@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        validate(username, password)

        user = User.query.filter_by(username=username).first()

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
        username = request.form.get('username')
        password = request.form.get('password')
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        validate(username, password)

        user = User(username, security.generate_password_hash(password), first_name, last_name)
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


def validate(username, password):
    if not username:
        flash('Username is required!', 'error')
        return redirect(url_for('login'))
    if not password:
        flash('Password is required!', 'error')
        return redirect(url_for('login'))

