# -*- coding: utf-8 -*-
# Hawken Tracker - Accounts

from flask.ext.login import LoginManager, login_user as login, logout_user as logout
from sqlalchemy.exc import IntegrityError
from hawkentracker.mappings import CoreRole
from hawkentracker.mailer import mail, welcome_email
from hawkentracker.model import User, UserRole, AnonymousUser, db


class InvalidLogin(Exception):
    pass


class InactiveAccount(Exception):
    pass


class EmailAlreadyExists(Exception):
    pass


class UsernameAlreadyExists(Exception):
    pass


login_manager = LoginManager()
login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    try:
        user_id = int(user_id)
    except:
        return None
    else:
        return User.query.get(user_id)


def force_login(user):
    login(user, remember=False, force=True)


def login_user(username, password, remember):
    user = User.by_username(username)
    if user is None:
        user = User.by_email(username)
        if user is None:
            raise InvalidLogin()

    if not user.verify_password(password):
        raise InvalidLogin()

    if not login(user, remember=remember):
        raise InactiveAccount()


def logout_user():
    logout()


def create_user(username, password, email, role=None):
    # Load role
    if role is None:
        role = CoreRole.unconfirmed

    if isinstance(role, CoreRole):
        role = UserRole.query.get(role.value)

    # Create user
    user = User()
    user.username = username
    user.password = password
    user.email = email
    user.role = role

    user.generate_email_confirmation(email)

    # Commit user
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()

        if e.orig.diag.constraint_name == "users_username_key":
            raise UsernameAlreadyExists

        if e.orig.diag.constraint_name == "users_email_key":
            raise EmailAlreadyExists

    # Send welcome email
    mail.send(welcome_email(user))

    return user


def delete_user(user):
    # Unlink players
    for player in user.players:
        player.unlink()
        db.session.add(player)

    # Delete user and commit
    db.session.delete(user)
    db.session.commit()
