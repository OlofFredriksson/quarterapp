#
#  Copyright (c) 2013 Markus Eliasson, http://www.quarterapp.com/
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
# 
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import tornado.web
import logging

from tornado.options import options
from base import AuthenticatedHandler, authenticated_admin
from ..domain import BaseError, User, UserType, UserState
from ..utils import *

# TODO Move to configuration file?
DEFAULT_PAGINATION_ITEMS_PER_PAGE = 5
DEFAULT_PAGINATION_PAGES = 10

class ViewError(BaseError):
    """
    Represents a view error that is displayed in the view
    """
    def __init__(self, code, message):
        self.code = code
        self.message = message

ERROR_UNKNOWN                       = ViewError(10000, "Unknown error occured")
ERROR_USERNAME_NOT_UNIQUE           = ViewError(10001, "Not logged in")
ERROR_INVALID_USERNAME              = ViewError(10002, "Not logged in")
ERROR_PASSWORDS_NOT_MATCHING        = ViewError(10003, "Not implemented")
ERROR_NOT_ALLOWED                   = ViewError(10004, "Not allowed")

def verify_username(storage, username):
    if len(username) == 0:
        raise ERROR_INVALID_USERNAME
    if not storage.unique_username(username):
        raise ERROR_USERNAME_NOT_UNIQUE

def verify_password(first, second):
    if not first == second:
        raise ERROR_PASSWORDS_NOT_MATCHING

class AdminDefaultHandler(AuthenticatedHandler):
    """
    Renders the admin first view
    """
    @authenticated_admin
    def get(self):
        allow_signups = self.application.quarter_settings.get_value("allow-signups")
        allow_activations = self.application.quarter_settings.get_value("allow-activations")

        self.render(u"../resources/templates/admin/general.html",
            options = options,
            current_user = self.get_current_user(),
            allow_signups = allow_signups,
            allow_activations = allow_activations)

class AdminUsersHandler(AuthenticatedHandler):
    """
    Renders the admin users view
    """

    @authenticated_admin
    def get(self):
        start = self.get_argument("start", "")
        count = self.get_argument("count", "")
        query_filter = self.get_argument("filter", "")

        users = []
        pagination_links = []
        error = False

        if len(start) > 0:
            if not start.isdigit():
                error = True
        else:
            start = 0 # Default start index

        if len(count) > 0:
            if not count.isdigit():
                error = True
        else:
            count = DEFAULT_PAGINATION_ITEMS_PER_PAGE
        
        try:
            if query_filter:
                logging.info("Getting filtered users %s" % (query_filter))
                user_count = self.application.storage.get_filtered_user_count(query_filter)
                pagination_links = generate_pagination(user_count, start, count, DEFAULT_PAGINATION_PAGES, query_filter = query_filter)
                users = self.application.storage.get_filtered_users(query_filter, start, count)
            else:
                user_count = self.application.storage.user_count()
                pagination_links = generate_pagination(user_count, start, count, DEFAULT_PAGINATION_PAGES)
                users = self.application.storage.get_users(start, count)
        except:
            error = True

        self.render(u"../resources/templates/admin/users.html",
            options = options,
            current_user = self.get_current_user(),
            users = users,
            pagination = pagination_links,
            error = error,
            query_filter = query_filter)

    @authenticated_admin
    def post(self):
        self.get()

class AdminNewUserHandler(AuthenticatedHandler):
    """
    Renders the view to create a new user
    """

    @authenticated_admin
    def get(self):
        self.render(u"../resources/templates/admin/new-user.html",
            options = options,
            current_user = self.get_current_user(),
            completed = False,
            error = False)

    @authenticated_admin
    def post(self):
        username = self.get_argument("username", "")
        password = self.get_argument("password", "")
        repeat_password = self.get_argument("verify-password", "")
        user_type = self.get_argument("user-type", "")
        error = None

        try:
            verify_username(self.application.storage, username)
            verify_password(password, repeat_password)
            hashed_password = hash_password(password, username)

            new_user = User(username = username, password = hashed_password, type = UserType.from_string(user_type), state= UserState.Active)
            if not self.application.storage.save_user(new_user):
                error = ERROR_UNKNOWN
        except ViewError, e:
            logging.error("Could not create user:")
            logging.exception(e)
            error = e
        except Exception, e:
            logging.error("Unknown error occured:")
            logging.exception(e)
            error = ERROR_UNKNOWN

        self.render(u"../resources/templates/admin/new-user.html",
            options = options,
            current_user = self.get_current_user(),
            completed = not error,
            error = error)

class AdminEditUserHandler(AuthenticatedHandler):
    """
    Renders the view to edit and delete a new user
    """

    @authenticated_admin
    def get(self, user_id):
        user = self.application.storage.get_user(user_id)
        self.render(u"../resources/templates/admin/edit-user.html",
            options = options,
            current_user = self.get_current_user(),
            user = user,
            completed = False,
            error = False)

    @authenticated_admin
    def post(self, user_id):
        username = self.get_argument("username", "")
        password = self.get_argument("password", "")
        repeat_password = self.get_argument("verify-password", "")
        user_type = self.get_argument("user-type", "")
        user_state = self.get_argument("user-state", "")
        error = None
        user = None

        try:
            current_user = self.application.storage.get_user(user_id)

            # Trying to update username
            if not current_user.username == username: 
                raise ERROR_NOT_ALLOWED

            # Trying to update password need to rehash
            if not current_user.password == password:
                verify_password(password, repeat_password)
                password = hash_password(password, username)

            user = User(id = user_id, username = username, password = password,
                type = UserType.from_string(user_type), state= UserState.from_string(user_state))
            if not self.application.storage.save_user(user):
                error = ERROR_UNKNOWN
        except ViewError, e:
            logging.error("Could not update user:")
            logging.exception(e)
            error = e
        except Exception, e:
            logging.error("Unknown error occured:")
            logging.exception(e)
            error = ERROR_UNKNOWN

        self.render(u"../resources/templates/admin/edit-user.html",
            options = options,
            current_user = self.get_current_user(),
            user = user,
            completed = not error,
            error = error)

class AdminDeleteUserHandler(AuthenticatedHandler):
    @authenticated_admin
    def get(self, user_id):
        self.application.storage.delete_user(User("", user_id))
        self.redirect(u"/admin/users")

class AdminMetricsHandler(AuthenticatedHandler):
    @authenticated_admin
    def get(self):
        user_count = self.application.storage.user_count()
        signup_count = 0
        quarter_count = 0

        self.render(u"../resources/templates/admin/metrics.html",
            options = options,
            current_user = self.get_current_user(),
            user_count = user_count,
            signup_count = signup_count,
            quarter_count = quarter_count)

class AdminSettingsHandler(AuthenticatedHandler):
    """
    Used by the admin view via HTTP API to retrieve and update application settings.
    """
    @authenticated_admin
    def get(self, key):
        try:
            if key:
                value = self.application.quarter_settings.get_value(key)
                if value:
                    self.write({"key" : key, "value" : value})
                else:
                    logging.info("No value found for key")
                    self.set_status(500)
            else:
                logging.info("No key given")
                self.set_status(500)
        except Exception, e:
            logging.exception(e)
            self.set_status(500)
        self.finish()

    @authenticated_admin
    def post(self, key):
        logging.info("Updating setting")
        try:
            if key:
                value = self.get_argument("value", "")
                self.application.quarter_settings.put_value(key, value)
                self.write({"key" : key, "value" : value})
            else:
                logging.info("No key given")
                self.set_status(500)
        except Exception, e:
            logging.warn("Could not update setting")
            logging.exception(e)
            self.set_status(500)
        self.finish()
