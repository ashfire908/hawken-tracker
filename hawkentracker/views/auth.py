# -*- coding: utf-8 -*-
# Hawken Tracker - Login views

from flask import Blueprint, render_template, request, flash, current_app
from flask.ext.login import current_user
from hawkentracker.account import InvalidLogin, InactiveAccount, UsernameAlreadyExists, EmailAlreadyExists, login_user,\
    logout_user, create_user, force_login
from hawkentracker.helpers import to_next, to_index, access_denied
from hawkentracker.mailer import mail, password_reset_email, reminder_email
from hawkentracker.mappings import CoreRole
from hawkentracker.model import User, TokenInvalid, TokenExpired, db
from hawkentracker.permissions import permissions_view
from hawkentracker.util import email_re


auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated():
        flash("You are already logged in.", "info")
        return to_next("account.overview")

    if request.method == "POST":
        try:
            login_user(request.form["username"], request.form["password"], request.form["remember"] == "yes")
        except InvalidLogin:
            flash("Invalid login.", "error")
        except InactiveAccount:
            flash("Account has been deactivated. Contact an admin for more info.", "error")
        else:
            flash("Successfully logged in!", "success")
            return to_next()

    return render_template("auth/login.jade")


@auth.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.", "success")

    return to_next()


@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated():
        flash("You are already logged in.", "info")
        return to_next("account.overview")
    elif permissions_view.user.create.self:
        return access_denied("You do not have permission to create a user.")

    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]
        password_confirm = request.form["password_confirm"]

        if len(username) < current_app.config.get("MIN_USERNAME_LENGTH", 1):
            flash("Your username must be at least {0} characters long.".format(current_app.config.get("USERNAME_MIN_LENGTH", 1)), "error")
        elif "@" in username:
            flash("Usernames cannot contain a @ symbol.", "error")
        elif password != password_confirm:
            flash("The passwords must match.", "error")
        elif len(password) < current_app.config.get("PASSWORD_MIN_LENGTH", 1):
            flash("Your password must be at least {0} characters long.".format(current_app.config.get("PASSWORD_MIN_LENGTH", 1)), "error")
        elif email_re.match(email) is None:
            flash("Your email is not valid.", "error")
        else:
            try:
                user = create_user(username, request.form["password"], email, CoreRole.unconfirmed)
            except UsernameAlreadyExists:
                flash("Username already in use. Please choose another.", "error")
            except EmailAlreadyExists:
                flash("Email already in use. If you forgot your password, please use the forgot password feature.", "error")
            else:
                force_login(user)

                flash("Successfully registered!", "success")
                return to_next("account.overview")

    return render_template("auth/register.jade")


@auth.route("/forgot", methods=["GET", "POST"])
def forgot():
    if current_user.is_authenticated():
        flash("You are already logged in.", "info")
        return to_next("account.overview")

    if request.method == "POST":
        if request.form["username"] != "":
            user = User.by_username(request.form["username"])
            if user is not None:
                user.generate_password_reset_token()

                db.session.add(user)
                db.session.commit(user)

                mail.send(password_reset_email(user))

            # Mask invalid username as success
            flash("Password reset email sent.", "success")
            return to_next("auth.login")

        if request.form["email"] != "":
            user = User.by_email(request.form["email"])
            if user is not None:
                mail.send(reminder_email(user))
                flash("A reminder email with your account details has been sent.", "success")
                return to_next("auth.login")

            flash("No user was found with that email. If you have a email change pending, use your old email address instead.", "error")
        else:
            flash("Please specify either your username or email.", "error")

    return render_template("auth/forgot.jade")


@auth.route("/password_reset", methods=["GET", "POST"])
def password_reset():
    if request.method == "GET":
        email = request.args.get("email")
        token = request.args.get("token")
    else:
        email = request.form.get("email")
        token = request.form.get("token")
        password = request.form.get("password")
        password_confirm = request.form.get("password_confirm")

    # Locate the user
    user = User.by_email(email)

    if user is None:
        flash("No such user found with that email.", "error")
        return to_index()

    if request.method == "GET":
        try:
            # Verify the token
            user.verify_password_reset(token)
        except TokenInvalid:
            flash("Invalid token given.", "error")
            return to_index()
        except TokenExpired:
            flash("This token has expired. Please request another password reset.", "error")
            return to_index()
    else:
        # Check password
        if password != password_confirm:
            flash("The passwords must match.", "error")
        else:
            try:
                # Reset password
                user.reset_password(token, password)
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

    return render_template("auth/password_reset.jade")


@auth.route("/verify")
def verify_email():
    email = request.args.get("email")
    token = request.args.get("token")

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

    if current_user.id == user.id:
        return to_next("account.overview")

    return to_next("auth.login")
