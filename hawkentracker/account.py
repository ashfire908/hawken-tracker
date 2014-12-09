# -*- coding: utf-8 -*-
# Hawken Tracker - Accounts

import random

from datetime import datetime
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import func
from flask import current_app, session
from hawkentracker.model import db, User, Player
from hawkentracker.mailer import mail, welcome_email
from hawkentracker.mappings import LinkStatus, CoreRole

serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


class ValidationError(ValueError):
    pass


@current_app.before_request
def active_login_check():
    active_user = session.get("user", None)
    if active_user is not None and User.query.get(active_user) is None:
        # User is logged into an account that doesn't exist!
        logout_user()


def get_user(user=None):
    user = user or session.get("user", None)
    if user is None:
        return None

    return User.query.get(user)


def login_user(username, password):
    user = User.query.filter(func.lower(User.username) == username.lower()).first()
    if user is None or not user.verify_password(password):
        return False

    # Setup session
    session["user"] = user.id

    return True


def logout_user():
    if "user" in session:
        session.pop("user", None)
        return True
    return False


def create_user(username, password, email, role_id):
    # Create the user
    user = User()
    user.username = username
    user.password = password
    user.creation = datetime.now()
    user.email = email
    user.role_id = role_id
    db.session.add(user)
    db.session.commit()

    # Send the welcome email
    token = generate_email_verify_token(user)
    mail.send(welcome_email(user, token))


def delete_user(id):
    # Unlink players
    Player.query.filter(Player.link_user == id).update({Player.link_status: LinkStatus.none, Player.link_user: None})

    # Delete account
    User.query.filter(User.id == id).delete()


def set_password(id, password):
    user = get_user(id)
    user.password = password
    user.password_reset_token = None
    db.session.add(user)
    db.session.commit()


def confirm_email(user):
    user.email_confirmed = True
    if user.role == CoreRole.unconfirmed.value:
        user.role = CoreRole.user.value
    db.session.add(user)
    db.session.commit()


def generate_email_verify_token(user):
    payload = {
        "user": user.id,
        "email": user.email
    }
    return serializer.dumps(payload)


def load_email_verify_token(token):
    data = serializer.loads(token, max_age=current_app.config["EMAIL_TOKEN_MAX_AGE"])

    user = get_user(data["user"])
    if user is None:
        raise ValidationError("User does not exist")

    if user.email_address != data["email"]:
        raise ValidationError("Email given does not match the current email")

    return user


def generate_password_reset_token(user):
    user.password_reset_token = "%030x" % random.randrange(16**30)
    db.session.add(user)
    db.session.commit()

    payload = {
        "user": user.id,
        "token": user.password_reset_token
    }
    return serializer.dumps(payload)


def load_password_reset_token(token):
    data = serializer.loads(token, max_age=current_app.config["RESET_TOKEN_MAX_AGE"])

    user = get_user(data["user"])
    if user is None:
        raise ValidationError("User does not exist")

    if user.password_reset_token != data["token"]:
        raise ValidationError("Password reset token does not match the stored token")

    return user


def link_player(id, player):
    player.link_user = id
    player.link_status = LinkStatus.linked
    db.session.add(player)
    db.session.commit()


def unlink_player(player):
    player.link_user = None
    player.link_status = LinkStatus.none
    db.session.add(player)
    db.session.commit()
