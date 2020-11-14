from datetime import datetime

from flask import Blueprint, render_template, request, flash, url_for, current_app, session
from flask_mail import Message
from werkzeug.utils import redirect

from gifted import db, mail
from gifted.models import Invite, Event, User, generate_code

admin = Blueprint('admin', __name__,
                  template_folder='templates',
                  static_folder='static')


@admin.route('/admin')
def index():
    events = Event.query.order_by(Event.id.desc()).all()
    return render_template('admin.html', events=events)


@admin.route('/admin/events/<event_id>')
def manage_event(event_id):
    # todo: this is pretty hacky, is there a way to push this onto the db?
    event = Event.query.get(event_id)
    ids = []
    for user in event.users:
        ids.append(user.id)
    users = User.query.filter(User.id.notin_(ids)).all()
    return render_template('manage_event.html', event=event, users=users)


@admin.route('/admin/events', methods=['POST'])
def create_event():
    title = request.form.get('title')
    description = request.form.get('description')
    starts_on = datetime.strptime(request.form.get('startsOn'), '%Y-%m-%d').date()
    ends_on = datetime.strptime(request.form.get('endsOn'), '%Y-%m-%d').date()

    event = Event(title=title, description=description, starts_on=starts_on, ends_on=ends_on)
    user = User.query.filter_by(id=session['user_id']).first()
    event.users.append(user)
    db.session.add(event)
    db.session.commit()

    flash('Event created successfully!', 'success')
    return redirect(url_for('admin.index'))


@admin.route('/admin/events/<event_id>/matchmake', methods=['POST'])
def matchmake(event_id):
    users_to_shuffle = request.form.getlist('shuffledUsers')
    if len(users_to_shuffle) < 2:
        flash('A minimum of two are required to shuffle!', 'warning')
        return redirect(url_for('admin.event', event_id=event_id))
    event = Event.query.get(event_id)
    event.matchmake(users_to_shuffle)
    flash('Shuffled users!', 'success')
    return redirect(url_for('admin.manage_event', event_id=event_id))


@admin.route('/admin/events/<event_id>/delete', methods=['POST'])
def delete_event(event_id):
    event = Event.query.get(event_id)
    db.session.delete(event)
    db.session.commit()
    flash(f'Deleted event {event}!', 'success')
    return redirect(url_for('admin.index'))


# @admin.route('/admin/events/<event_id>/users', methods=['POST'])
# def create_user(event_id):
#     username = request.form.get('username')
#     password = request.form.get('password')
#     password_confirm = request.form.get('passwordConfirm')
#     first_name = request.form.get('firstName')
#     last_name = request.form.get('lastName')
#
#     if password != password_confirm:
#         flash('Passwords must match!', 'warning')
#         return redirect(url_for('admin.event', event_id=event_id))
#
#     user = User(username=username, password=security.generate_password_hash(password),
#                 first_name=first_name, last_name=last_name)
#
#     event = Event.query.get(event_id)
#     event.users.append(user)
#     db.session.add(user)
#     db.session.commit()
#     flash(f'Created user {user}!', 'success')
#     return redirect(url_for('admin.event', event_id=event_id))


@admin.route('/admin/events/<event_id>/users', methods=['POST'])
def add_users(event_id):
    event = Event.query.get(event_id)
    users = request.form.getlist('users')
    for user_id in users:
        user = User.query.get(user_id)
        event.users.append(user)
        db.session.commit()

    return redirect(url_for('admin.manage_event', event_id=event_id))


@admin.route('/admin/users/<user_id>/delete', methods=['POST'])
def delete_user(user_id):
    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'Deleted user {user}!', 'success')
    return redirect(url_for('admin.index'))


@admin.route('/admin/invites', methods=['POST'])
def invite():
    email = request.form.get('email')
    event_id = request.form.get('eventId')
    code = generate_code()
    invitation = Invite(email=email, event_id=event_id, code=code)
    db.session.add(invitation)
    db.session.commit()
    flash(f'Invited {email}!', 'success')

    message = Message('You have been invited to participate in a Gifted exchange!',
                      sender=current_app.config.get("MAIL_USERNAME"),
                      recipients=[email])

    message.html = render_template('register_email.html', email=invitation.email, code=invitation.code)
    mail.send(message)
    return redirect(url_for('admin.manage_event', event_id=event_id))


@admin.route('/admin/invites/<invite_id>/revoke', methods=['POST'])
def revoke(invite_id):
    invitation = Invite.query.filter_by(id=invite_id).first()
    invitation.is_valid = 0
    db.session.commit()
    flash(f'Revoked {invitation.email}\'s invitation', 'success')
    return redirect(url_for('admin.index'))
