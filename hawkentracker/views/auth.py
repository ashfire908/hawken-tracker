# -*- coding: utf-8 -*-
# Hawken Tracker - Login views

from sqlalchemy import func
from flask import Blueprint, current_app, render_template, request, session, flash
from hawkentracker.account import ValidationError, login_user, logout_user, create_user, send_password_reset_email, send_reminder_email
from hawkentracker.helpers import to_next, load_globals, access_denied
from hawkentracker.mappings import CoreRole
from hawkentracker.model import User
from hawkentracker.permissions import permissions_view


auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in", False):
        flash("You are already logged in.", "info")
        return to_next("account")

    if request.method == "POST":
        if not login_user(request.form["username"], request.form["password"]):
            flash("Invalid login.", "error")
        else:
            flash("Successfully logged in!", "success")
            return to_next()

    load_globals()
    return render_template("auth/login.jade")


@auth.route("/logout")
def logout():
    if logout_user():
        flash("You have been logged out.", "success")

    return to_next()


@auth.route("/forgot", methods=["GET", "POST"])
def forgot():
    if session.get("logged_in", False):
        flash("You are already logged in.", "info")
        return to_next("account")

    if request.method == "POST":
        if request.form["username"] != "":
            user = User.query.filter(func.lower(User.username) == request.form["username"].lower()).first()
            if user is not None:
                send_password_reset_email(user)

            flash("Password reset email sent.", "success")
            return to_next("login")

        if request.form["email"] != "":
            user = User.query.filter(func.lower(User.email) == request.form["email"].lower()).first()
            if user is not None:
                send_reminder_email(user)
                flash("A reminder email with your account details has been sent.", "success")
                return to_next("login")

            flash("No user was found with that email.", "error")
        else:
            flash("Please specify either your username or email.", "error")

    load_globals()
    return render_template("auth/forgot.jade")


@auth.route("/register", methods=["GET", "POST"])
def register():
    if session.get("logged_in", False):
        flash("You are already logged in.", "info")
        return to_next("account")
    elif permissions_view.user.create.self:
        return access_denied("You do not have permission to create a user.")

    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()

        if request.form["password"] != request.form["confirm"]:
            flash("The passwords must match.", "error")
        else:
            try:
                create_user(username, request.form["password"], email, CoreRole.unconfirmed.value)
                flash("Successfully registered!", "success")
                if not login_user(username, request.form["password"]):
                    current_app.logger.error("Failed to automatically login user '{0}' with their own password".format(username))
                    flash("Failed to log you in. Please contact the administrator.", "error")
                else:
                    return to_next("account")
            except ValidationError as e:
                flash(str(e), "error")

    load_globals()
    return render_template("auth/register.jade")
