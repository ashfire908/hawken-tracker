# -*- coding: utf-8 -*-
# Hawken Tracker - Forms

from flask import current_app
from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, HiddenField, BooleanField, ValidationError
from wtforms.validators import DataRequired, Length, EqualTo, Email, Optional


def username_character_check(form, field):
    if "@" in field.data:
        raise ValidationError("Usernames cannot contain the '@' symbol.")


class LoginForm(Form):
    username = StringField("Username", [DataRequired(message="Username missing.")])
    password = PasswordField("Password", [DataRequired(message="Password missing.")])
    remember = BooleanField("Remember Me", default=False)
    login = SubmitField("Login", [DataRequired()])


class RegistrationForm(Form):
    username = StringField("Username", [
        DataRequired(message="You must provide a username."),
        Length(min=current_app.config["USERNAME_MIN_LENGTH"], max=current_app.config["USERNAME_MAX_LENGTH"],
               message="Usernames must be between %(min)d and %(max)d characters long."),
        username_character_check
    ])
    password = PasswordField("Password", [
        DataRequired(message="You must provide a password."),
        Length(min=current_app.config["PASSWORD_MIN_LENGTH"], max=current_app.config["PASSWORD_MAX_LENGTH"],
               message="Passwords must be between %(min)d and %(max)d characters long."),
        EqualTo("password_confirm", message="The password and confirmation password must match.")
    ])
    password_confirm = PasswordField("Confirm Password")
    email = StringField("Email", [
        DataRequired(message="You must provide an email."),
        Email(message="You must provide a valid email.")
    ])
    register = SubmitField("Register")


class ForgotAccountForm(Form):
    email = StringField("Email")
    recover_username = SubmitField("Recover Account", [
        Optional(),
        EqualTo("email", message="Email required to recover your username.")
    ])
    username = StringField("Username")
    recover_password = SubmitField("Request Password Reset", [
        Optional(),
        EqualTo("username", message="Username required to reset your password.")
    ])


class PasswordResetForm(Form):
    email = HiddenField("email", [
        DataRequired()
    ])
    token = HiddenField("token", [
        DataRequired()
    ])
    password = PasswordField("New Password", [
        DataRequired(message="You must provide a password."),
        Length(min=current_app.config["PASSWORD_MIN_LENGTH"], max=current_app.config["PASSWORD_MAX_LENGTH"],
               message="Passwords must be between %(min)d and %(max)d characters long."),
        EqualTo("password_confirm", message="The password and confirmation password must match.")
    ])
    password_confirm = PasswordField("Confirm Password")
