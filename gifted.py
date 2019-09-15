from flask import Flask, render_template, request, session, url_for
from werkzeug.utils import redirect

from helpers import login_required

app = Flask(__name__)
app.secret_key = b',w\xac\x87\xee\x9e\x83gf46s\x8c\xdbU\x1d'


@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['username'] = request.form.get('username')
        print(session)
        return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

