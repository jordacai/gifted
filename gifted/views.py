from datetime import datetime

from flask import (
    Blueprint, flash, render_template, request, session,
    url_for, current_app)
from flask_mail import Message
from werkzeug import security
from werkzeug.utils import redirect

from gifted import login_required, validate, db, mail
from gifted.helpers import randomize
from gifted.models import User, Invite

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
        validate(username=username, password=password, redirect_to='views.login')
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
        password_confirm = request.form.get('passwordConfirm')
        code = request.form.get('code')
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')

        if password != password_confirm:
            flash('Passwords must match!', 'error')
            return redirect(url_for('views.register'))

        invitation = Invite.query.filter_by(email=username, code=code).first()
        if invitation is None:
            flash('This code and email combination is invalid!', 'error')
            return redirect(url_for('views.register'))

        user = User(username=username, password=security.generate_password_hash(password),
                    first_name=first_name, last_name=last_name)
        db.session.add(user)
        invitation.is_used = 1
        db.session.commit()

        flash('Account created successfully!', 'success')
        return redirect(url_for('views.login'))

    # it's a GET, render the template
    return render_template('register.html', email=request.args.get('email'), code=request.args.get('code'))


@bp.route('/admin')
def admin():
    users = User.query.order_by(User.id.desc()).all()
    invites = Invite.query.filter_by(is_valid=1).order_by(Invite.id.desc()).all()
    return render_template('admin.html', users=users, invites=invites)


@bp.route('/admin/users/delete', methods=['POST'])
def delete():
    user_id = request.form.get('id')
    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'Deleted user {user}!', 'success')
    return redirect(url_for('views.admin'))


@bp.route('/admin/invites', methods=['POST'])
def invite():
    email = request.form.get('email')
    invitation = Invite(email=email)
    db.session.add(invitation)
    db.session.commit()
    flash(f'Invited {email}!', 'success')

    message = Message('You have been invited to participate in a Gifted exchange!',
                      sender=current_app.config.get("MAIL_USERNAME"),
                      recipients=[current_app.config.get("MAIL_USERNAME")])

    message.html = render_template('email.html', email=invitation.email, code=invitation.code)
    mail.send(message)

    return redirect(url_for('views.admin'))


@bp.route('/admin/invites/revoke', methods=['POST'])
def revoke():
    invitation_id = request.form.get('id')
    invitation = Invite.query.filter_by(id=invitation_id).first()
    invitation.valid = 0
    db.session.commit()
    flash(f'Revoked {invitation.email}\'s invitation', 'success')
    return redirect(url_for('views.admin'))


@bp.route('/admin/randomize')
def matchmake():
    users = User.query.order_by(User.id.asc()).all()
    matches = randomize(users)
    print(matches)
    return redirect(url_for('views.admin'))


@bp.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('views.login'))


@bp.app_template_filter('pretty_boolean')
def pretty_boolean(i):
    return True if i is 1 else False


@bp.app_template_filter('is_expired')
def is_expired(expires_on):
    now = datetime.now()
    return True if now > expires_on else False
