# -*- coding: utf-8 -*-
# Hawken Tracker - Accounts

import random
from datetime import datetime
from passlib.context import CryptContext
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import func
from flask import current_app, session, url_for
from hawkentracker.interface import send_email
from hawkentracker.model import db, User, Player
from hawkentracker.mappings import LinkStatus, CoreRole

pwd_context = CryptContext(schemes=["sha256_crypt"])
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
    if user is None or not pwd_context.verify(password, user.password):
        return False

    # Setup session
    session["user"] = user.id

    return True


def logout_user():
    if "user" in session:
        session.pop("user", None)
        return True
    return False


def validate_username(username):
    if username == "":
        raise ValidationError("Username cannot be blank")

    if User.query.filter(func.lower(User.username) == username.lower()).count() > 0:
        raise ValidationError("Username already in use")


def validate_password(password):
    if password == "":
        raise ValidationError("Password cannot be blank")

    if len(password) < current_app.config.get("PASSWORD_MIN_LENGTH", 0):
        raise ValidationError("Password is too short")


def validate_email(email, ignore_existing=False):
    if email == "":
        raise ValidationError("Email cannot be blank")

    at_sign = email.find("@")
    if at_sign == -1 or email.find(".") < at_sign:
        raise ValidationError("Email address is not valid")

    if ignore_existing or User.query.filter(func.lower(User.email) == email.lower()).count() > 0:
        raise ValidationError("Email already in use")


def create_user(username, password, email, role_id):
    # Validate fields
    validate_username(username)
    validate_password(password)
    validate_email(email)

    # Create the user
    user = User()
    user.username = username
    user.password = pwd_context.encrypt(password)
    user.creation = datetime.now()
    user.email = email
    user.role_id = role_id
    db.session.add(user)
    db.session.commit()

    # Send the welcome email
    #send_welcome_email(user)


def delete_user(id):
    # Unlink players
    Player.query.filter(Player.link_user == id).update({Player.link_status: LinkStatus.none, Player.link_user: None})

    # Delete account
    User.query.filter(User.id == id).delete()


def verify_password(user, password):
    if isinstance(user, User):
        current_password = user.password
    else:
        current_password = db.session.query(User.password).filter(User.id == user).scalar()

    return pwd_context.verify(password, current_password)


def set_password(id, password, silent=False):
    validate_password(password)

    user = get_user(id)
    user.password = pwd_context.encrypt(password)
    user.password_reset_token = None
    db.session.add(user)
    db.session.commit()

    if not silent:
        send_password_changed_email(user)


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


def send_welcome_email(user):
    token = generate_email_verify_token(user)

    message = """Hello {user.username},

Welcome to the Hawken Tracker and Leaderboards. To verify your email, please follow this link: {verify_url}

If you did not register this account, you can simply ignore this message.

Thanks,
Hawken Tracker
{site_url}""".format(user=user, verify_url=current_app.config["SITE_ADDRESS"] + url_for("account.verify_email", token=token), site_url=current_app.config["SITE_ADDRESS"])

    send_email(user.email_address, "Welcome to the Hawken Leaderboards", message)


def send_reminder_email(user):
    message = """Hello {user.username},

This is a reminder of your account details, by request. If you did not request this email, you can safely ignore it.

Username: {user.username}
Email: {user.email}

Thanks,
Hawken Tracker
{site_url}""".format(user=user, site_url=current_app.config["SITE_ADDRESS"])

    send_email(user.email_address, "Hawken Leaderboards - Account details", message)


def send_verification_email(user):
    token = generate_email_verify_token(user)

    message = """Hello {user.username},

Email verification for your account has been requested. To verify your email, please follow this link: {verify_url}

If this is not your account, you can simply ignore this message.

Thanks,
Hawken Tracker
{site_url}""".format(user=user, verify_url=current_app.config["SITE_ADDRESS"] + url_for("account.verify_email", token=token), site_url=current_app.config["SITE_ADDRESS"])

    send_email(user.email_address, "Hawken Leaderboards - Verify your email address", message)


def send_password_reset_email(user):
    token = generate_password_reset_token(user)

    message = """Hello {user.username},

A password reset has been requested. To reset your password, please follow this link: {reset_url}

If you did not request this, you can safely ignore this message.

Thanks,
Hawken Tracker
{site_url}""".format(user=user, reset_url=current_app.config["SITE_ADDRESS"] + url_for("account.password_reset", token=token), site_url=current_app.config["SITE_ADDRESS"])

    send_email(user.email_address, "Hawken Leaderboards - Password reset requested", message)


def send_password_changed_email(user):
    message = """Hello {user.username},

This is a notification that your password was recently changed. If this was you, then you can safely ignore this email.

If you did not change it, please contact us at {support_email} right away.

Thanks,
Hawken Tracker
{site_url}""".format(user=user, support_email=current_app.config["SUPPORT_EMAIL"], site_url=current_app.config["SITE_ADDRESS"])

    send_email(user.email_address, "Hawken Leaderboards - Password changed", message)


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
