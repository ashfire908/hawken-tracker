# -*- coding: utf-8 -*-
# Hawken Tracker - Mailer

from flask import render_template
from flask_mail import Mail, Message

mail = Mail()


def welcome_email(user, verify_token):
    subject = "Welcome to the Hawken Leaderboards"
    body = render_template("mailer/welcome.txt", user=user, verify_token=verify_token)
    html = render_template("mailer/welcome.jade", user=user, verify_token=verify_token)

    return Message(subject=subject, recipients=[(user.username, user.email)], body=body, html=html)


def reminder_email(user):
    subject = "Hawken Leaderboards - Account details"
    body = render_template("mailer/reminder.txt", user=user)
    html = render_template("mailer/reminder.jade", user=user)

    return Message(subject=subject, recipients=[(user.username, user.email)], body=body, html=html)


def verification_email(user, verify_token):
    subject = "Hawken Leaderboards - Verify your email address"
    body = render_template("mailer/verification.txt", user=user, verify_token=verify_token)
    html = render_template("mailer/verification.jade", user=user, verify_token=verify_token)

    return Message(subject=subject, recipients=[(user.username, user.email)], body=body, html=html)


def password_reset_email(user, reset_token):
    subject = "Hawken Leaderboards - Password reset"
    body = render_template("mailer/password_reset.txt", user=user, reset_token=reset_token)
    html = render_template("mailer/password_reset.jade", user=user, reset_token=reset_token)

    return Message(subject=subject, recipients=[(user.username, user.email)], body=body, html=html)
