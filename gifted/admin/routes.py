import uuid
from copy import deepcopy
from datetime import datetime

from flask import Blueprint, render_template, request, flash, url_for, current_app, g
from flask_mail import Message
from werkzeug import security
from werkzeug.exceptions import abort
from werkzeug.utils import redirect

from gifted import db, mail, app
from gifted.helpers import generate_code, login_required
from gifted.models import Invite, Event, User, SiteAdmin

admin = Blueprint('admin', __name__,
                  template_folder='templates',
                  static_folder='static')


@admin.route('/admin/events')
@login_required
def index():
    if SiteAdmin.contains(g.user.id):
        events = Event.query.all()
    else:
        events = g.user.administration
    return render_template('admin.html', events=events)


@admin.route('/admin/events/<event_id>')
@login_required
def manage_event(event_id):
    event = Event.query.get(event_id)
    if event is None:
        abort(404)
    if g.user not in event.admins and SiteAdmin.contains(g.user.id) is False:
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

    event = Event(title=title, description=description, starts_on=starts_on, ends_on=ends_on)
    event.admins.append(g.user)
    if add_me:
        event.users.append(g.user)
    db.session.add(event)
    db.session.commit()

    flash('Event created successfully!', 'success')
    app.logger.info(f'{g.user.username} created {event}')
    return redirect(url_for('admin.index'))


@admin.route('/admin/events/<event_id>/matchmake', methods=['POST'])
@login_required
def matchmake(event_id):
    users_to_shuffle = request.form.getlist('shuffledUsers')
    if len(users_to_shuffle) < 2:
        flash('A minimum of two are required to shuffle!', 'warning')
        return redirect(url_for('admin.manage_event', event_id=event_id))
    event = Event.query.get(event_id)
    event.matchmake(users_to_shuffle)
    flash('Shuffled users!', 'success')
    app.logger.info(f'{g.user.username} shuffled {event}')
    return redirect(url_for('admin.manage_event', event_id=event_id))


@admin.route('/admin/events/<event_id>/delete', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get(event_id)
    db.session.delete(event)
    db.session.commit()
    flash(f'Deleted event "{event.title}"!', 'success')
    app.logger.info(f'{g.user.username} deleted {event}')
    return redirect(url_for('admin.index'))


@admin.route('/admin/events/<event_id>/users', methods=['POST'])
@login_required
def add_users(event_id):
    event = Event.query.get(event_id)
    users = request.form.getlist('users')
    is_admin_add = request.form.get('isAdminAdd')
    usernames = []
    for user_id in users:
        user = User.query.get(user_id)
        event.users.append(user)
        if is_admin_add:
            event.admins.append(user)
        if user.parent:
            event.children.append(user)
        db.session.commit()
        app.logger.info(f'{g.user.username} added {user} to {event}')
        usernames.append(user.username)

    username_list = ', '.join(usernames)
    flash(f'Added {username_list} to {event.title}!', 'success')
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
    app.logger.info(f'{g.user.username} created child {child} of {child.parent}')
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
    app.logger.info(f'{g.user.username} removed {user} from {event}')
    return redirect(url_for('admin.manage_event', event_id=event_id))


@admin.route('/admin/users/<user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get(user_id)
    copy = deepcopy(user)
    db.session.delete(user)
    db.session.commit()
    flash(f'Deleted {copy.username}\'s account!', 'success')
    app.logger.info(f'{g.user.username} deleted {copy}')
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
    mail.send(message)

    db.session.add(invitation)
    db.session.commit()
    flash(f'Invited {email} to {invitation.event.title}!', 'success')
    app.logger.info(f'{g.user.username} invited {user} to {event_id}')
    return redirect(url_for('admin.manage_event', event_id=event_id))


@admin.route('/admin/invites/<invite_id>/revoke', methods=['POST'])
@login_required
def revoke(invite_id):
    invitation = Invite.query.get(invite_id)
    invite_copy = deepcopy(invitation)
    db.session.delete(invitation)
    db.session.commit()
    flash(f'Revoked {invite_copy.email}\'s invitation!', 'success')
    app.logger.info(f'{g.user.username} revoked {invite_copy}')
    return redirect(url_for('admin.manage_event', event_id=invitation.event_id))
