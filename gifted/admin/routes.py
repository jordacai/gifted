import uuid
from datetime import datetime

from flask import Blueprint, render_template, request, flash, url_for, current_app, session, g
from flask_mail import Message
from werkzeug import security
from werkzeug.exceptions import abort
from werkzeug.utils import redirect

from gifted import db, mail
from gifted.helpers import generate_code, login_required
from gifted.models import Invite, Event, User

admin = Blueprint('admin', __name__,
                  template_folder='templates',
                  static_folder='static')


@admin.route('/admin/events')
@login_required
def index():
    return render_template('admin.html', events=g.user.administration)


@admin.route('/admin/events/<event_id>')
@login_required
def manage_event(event_id):
    # todo: this is pretty hacky, is there a way to push this onto the db?
    event = Event.query.get(event_id)
    if g.user not in event.admins:
        abort(401)

    existing_ids = []
    for user in event.users:
        existing_ids.append(user.id)

    available_users = User.query\
        .filter(User.id.notin_(existing_ids))\
        .filter(User.registrar_id == g.user.id)\
        .all()

    return render_template('manage_event.html', event=event, available_users=available_users)


@admin.route('/admin/events', methods=['POST'])
@login_required
def create_event():
    title = request.form.get('title')
    description = request.form.get('description')
    starts_on = datetime.strptime(request.form.get('startsOn'), '%Y-%m-%d').date()
    ends_on = datetime.strptime(request.form.get('endsOn'), '%Y-%m-%d').date()
    add_me = request.form.get('addMe')

    # todo: implement add_me logic, and maybe the concept of a super admin/site admin? this list of users could get auto-added to all events

    event = Event(title=title, description=description, starts_on=starts_on, ends_on=ends_on)
    event.admins.append(g.user)
    if add_me:
        event.users.append(g.user)
    db.session.add(event)
    db.session.commit()

    flash('Event created successfully!', 'success')
    return redirect(url_for('admin.index'))


@admin.route('/admin/events/<event_id>/matchmake', methods=['POST'])
@login_required
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
@login_required
def delete_event(event_id):
    event = Event.query.get(event_id)
    db.session.delete(event)
    db.session.commit()
    flash(f'Deleted event "{event.title}"!', 'success')
    return redirect(url_for('admin.index'))


@admin.route('/admin/events/<event_id>/users', methods=['POST'])
@login_required
def add_users(event_id):
    event = Event.query.get(event_id)
    users = request.form.getlist('users')
    is_admin_add = request.form.get('isAdminAdd')
    for user_id in users:
        user = User.query.get(user_id)
        event.users.append(user)
        if is_admin_add:
            event.admins.append(user)
        if user.parent:
            event.children.append(user)
        db.session.commit()
        flash(f'{user.get_full_name()} was added to {event.title}!', 'success')

    return redirect(url_for('admin.manage_event', event_id=event_id))


@admin.route('/admin/add-user-child', methods=['POST'])
@login_required
def add_user_child():
    parent_id = request.form.get('parent')
    event_id = request.form.get('eventId')
    first_name = request.form.get('firstName')
    last_name = request.form.get('lastName')
    event = Event.query.get(event_id)
    child = User(username=str(uuid.uuid4()) + '@gifted.jcaimano.com',
                 password=security.generate_password_hash(str(uuid.uuid4())),
                 parent_id=parent_id,
                 registrar_id=parent_id,
                 first_name=first_name,
                 last_name=last_name)

    event.users.append(child)
    event.children.append(child)
    db.session.add(child)
    db.session.commit()
    flash(f'Successfully added {child.get_full_name()} as a child of { child.parent.get_full_name()}!', 'success')
    return redirect(url_for('admin.manage_event', event_id=event_id))


@admin.route('/admin/remove-user', methods=['POST'])
@login_required
def remove_user():
    event_id = request.form.get('eventId')
    user_id = request.form.get('userId')
    event = Event.query.get(event_id)
    user = User.query.get(user_id)
    if user.parent_id:
        event.children.remove(user)
    event.users.remove(user)
    db.session.commit()
    flash(f'Removed {user.get_full_name()} from {event.title}!', 'success')
    return redirect(url_for('admin.manage_event', event_id=event_id))


@admin.route('/admin/users/<user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'Deleted {user.username}\'s account!', 'success')
    return redirect(url_for('admin.index'))


@admin.route('/admin/invites', methods=['POST'])
@login_required
def invite():
    email = request.form.get('email')
    event_id = request.form.get('eventId')
    is_admin_invite = request.form.get('isAdminInvite')
    user = User.query.filter_by(username=email).first()

    if user is not None:
        flash('A user already exists with that email!', 'warning')
        return redirect(url_for('admin.manage_event', event_id=event_id))

    code = generate_code()
    if is_admin_invite:
        invitation = Invite(email=email, event_id=event_id, code=code, is_admin=1, invited_by=g.user.id)
    else:
        invitation = Invite(email=email, event_id=event_id, code=code, invited_by=g.user.id)

    message = Message('You have been invited to participate in a Gifted exchange!',
                      sender=current_app.config.get("MAIL_USERNAME"),
                      recipients=[email])
    message.html = render_template('invitation_email.html', email=invitation.email, code=invitation.code, admin=g.user)
    #mail.send(message)

    db.session.add(invitation)
    db.session.commit()
    flash(f'Invited {email} to {invitation.event.title}!', 'success')
    return redirect(url_for('admin.manage_event', event_id=event_id))


@admin.route('/admin/invites/<invite_id>/revoke', methods=['POST'])
@login_required
def revoke(invite_id):
    invitation = Invite.query.filter_by(id=invite_id).first()
    db.session.delete(invitation)
    db.session.commit()
    flash(f'Revoked {invitation.email}\'s invitation!', 'success')
    return redirect(url_for('admin.manage_event', event_id=invitation.event_id))
