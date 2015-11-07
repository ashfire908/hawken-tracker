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


class ServerNotFound(Exception):
    def __init__(self, server_id, match_id=None):
        self.server_id = server_id
        self.match_id = match_id
        super().__init__("Server {0} not found".format(self.server_id))
