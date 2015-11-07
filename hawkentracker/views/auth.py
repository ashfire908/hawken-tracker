# -*- coding: utf-8 -*-
# Hawken Tracker - Login views

from flask import Blueprint, render_template, request, flash
from flask.ext.login import current_user

from hawkentracker.account import login_user, logout_user, create_user, force_login
from hawkentracker.database import User, db
from hawkentracker.exceptions import InvalidLogin, InactiveAccount, EmailAlreadyExists, UsernameAlreadyExists,\
    TokenExpired, TokenInvalid
from hawkentracker.forms import LoginForm, RegistrationForm, ForgotAccountForm, PasswordResetForm
from hawkentracker.helpers import to_next, to_index, access_denied
from hawkentracker.mailer import mail, password_reset_email, reminder_email
from hawkentracker.mappings import CoreRole
from hawkentracker.permissions import permissions_view

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        flash("You are already logged in.", "info")
        return to_next("account.overview")

    form = LoginForm()

    if form.validate_on_submit():
        try:
            login_user(form.username.data, form.password.data, form.remember.data)
        except InvalidLogin:
            flash("Invalid login.", "error")
        except InactiveAccount:
            flash("Account has been deactivated. Contact an admin for more info.", "error")
        else:
            flash("Successfully logged in!", "success")
            return to_next()

    return render_template("auth/login.jade", form=form)


@auth.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.", "success")

    return to_next()


@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        flash("You are already logged in.", "info")
        return to_next("account.overview")
    elif permissions_view.user.create.self:
        return access_denied("You do not have permission to create a user.")

    form = RegistrationForm()

    if form.validate_on_submit():
        try:
            user = create_user(form.username.data, form.password.data, form.email.data, CoreRole.unconfirmed)
        except UsernameAlreadyExists:
            flash("Username already in use. Please choose another.", "error")
        except EmailAlreadyExists:
            flash("Email already in use. If you forgot your password, please use the forgot password feature.", "error")
        else:
            force_login(user)

            flash("Successfully registered!", "success")
            return to_next("account.overview")

    return render_template("auth/register.jade", form=form)


@auth.route("/forgot", methods=["GET", "POST"])
def forgot():
    if current_user.is_authenticated:
        flash("You are already logged in.", "info")
        return to_next("account.overview")

    form = ForgotAccountForm()

    if form.validate_on_submit():
        if form.recover_username.data:
            user = User.by_email(form.email.data)

            if user is not None:
                mail.send(reminder_email(user))
                flash("A reminder email with your account details has been sent.", "success")
                return to_next("auth.login")

            flash("No user was found with that email. If you have a email change pending, use your old email address instead.", "error")
        elif form.recover_password.data:
            user = User.by_username(form.username.data)

            if user is not None:
                user.generate_password_reset_token()

                db.session.add(user)
                db.session.commit()

                mail.send(password_reset_email(user))

            # Mask invalid username as success
            flash("Password reset email sent.", "success")
            return to_next("auth.login")
        else:
            flash("Please specify either your username or email.", "error")

    return render_template("auth/forgot.jade", form=form)


@auth.route("/password_reset", methods=["GET", "POST"])
def password_reset():
    form = PasswordResetForm()

    if request.method == "GET":
        email = request.args.get("email")
        token = request.args.get("token")

        if email is None or token is None:
            flash("Invalid parameters given.", "error")
            return to_index()

        # Locate the user
        user = User.by_email(email)

        if user is None:
            flash("No such user found with given email.", "error")
            return to_index()

        # Verify the token
        try:
            user.verify_password_reset(token)
        except TokenInvalid:
            flash("Invalid token given.", "error")
            return to_index()
        except TokenExpired:
            flash("This token has expired. Please request another password reset.", "error")
            return to_index()

        form.email.data = email
        form.token.data = token
    elif form.validate_on_submit():
        # Get the user
        user = User.by_email(form.email.data)

        # Reset password
        try:
            user.reset_password(form.token.data, form.password.data)
        except TokenInvalid:
            flash("Invalid token given.", "error")
            return to_index()
        except TokenExpired:
            flash("This token has expired. Please request another password reset.", "error")
            return to_index()

            # Commit change
        db.session.add(user)
        db.session.commit()

        flash("Password successfully reset!", "success")
        return to_next("auth.login")

    return render_template("auth/password_reset.jade", form=form)


@auth.route("/verify")
def verify_email():
    email = request.args.get("email")
    token = request.args.get("token")

    if email is None or token is None:
        flash("Invalid parameters given.", "error")
        return to_index()

    # Locate the user
    user = User.by_email(email)
    if user is None:
        user = User.by_pending_email(email)

    if user is None:
        flash("No such user found with that email.", "error")
        return to_index()

    try:
        # Confirm email
        user.verify_email_confirmation(email, token)
    except TokenInvalid:
        flash("Invalid token given.", "error")
        return to_index()
    except TokenExpired:
        flash("This token has expired. Please request another verification email.", "error")
        return to_index()

    # Commit change
    db.session.add(user)
    db.session.commit()

    flash("Email successfully verified!", "success")

    if current_user.user_id == user.user_id:
        return to_next("account.overview")

    return to_next("auth.login")
