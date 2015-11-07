# -*- coding: utf-8 -*-
# Hawken Tracker - Exceptions


class InvalidLogin(Exception):
    pass


class InactiveAccount(Exception):
    pass


class EmailAlreadyExists(Exception):
    pass


class UsernameAlreadyExists(Exception):
    pass


class InterfaceException(Exception):
    pass


class TokenExpired(ValueError):
    pass


class TokenInvalid(ValueError):
    pass
