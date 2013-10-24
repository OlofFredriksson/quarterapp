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

import json
import functools
import tornado.web
from tornado.options import options
from ..domain import NotLoggedInError, User


def authenticated_user(method):
    """
    Decorate methods with this to require that the user be logged in.
    """
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        user = self.get_current_user()
        if not user or not user.active() or not self.application.storage.authenticate_user(user.id):
            if self.request.method in ("GET", "HEAD"):
                url = self.get_login_url()
                self.redirect(url)
                return
            raise tornado.web.HTTPError(403)
        return method(self, *args, **kwargs)
    return wrapper


def authenticated_admin(method):
    """
    Decorate methods with this to require that user is admin.
    """
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        user = self.get_current_user()
        if not user or not self.application.storage.authenticate_admin(user.id):
            raise tornado.web.HTTPError(403)
        elif not user.is_admin():
            raise tornado.web.HTTPError(403)
        return method(self, *args, **kwargs)
    return wrapper


class QuarterUserEncoder(json.JSONEncoder):
    """
    JSON encoder for quarterapp's User object
    """
    def default(self, obj):
        if isinstance(obj, User):
            return {"id": obj.id, "username": obj.username, "password": obj.password, "last_login": obj.last_login, "type": obj.type, "state": obj.state}


class QuarterUserDecoder(json.JSONDecoder):
    """
    JSON decoder for quarterapp's User object
    """
    def decode(self, user_string):
        user_json = json.loads(user_string)
        user = User(id=user_json["id"], username=user_json["username"], password=user_json["password"],
                    last_login=user_json["last_login"], type=user_json["type"], state=user_json["state"])
        return user


class BaseHandler(tornado.web.RequestHandler):
    """
    All handlers in quarterapp should be derived from this handler. Contains utility
    functions regarding logging in and reading options.
    """
    def get_current_user(self):
        user_json = self.get_secure_cookie("user")
        if not user_json:
            return None
        return QuarterUserDecoder().decode(user_json)

    def set_current_user(self, user):
        if user:
            self.set_secure_cookie("user", QuarterUserEncoder().encode(user))
        else:
            self.clear_cookie("user")
    
    def logged_in(self):
        """
        Check if the user of the current requests is logged in or not.

        @return True if logged in, else False
        """
        user = self.get_secure_cookie("user")
        if user:
            return True
        else:
            return False

    def enabled(self, setting):
        """
        Check if the given setting is enabled

        Args:
            setting - The setting to check

        Returns:
            True if setting is enabled, else False
        """
        return self.application.quarter_settings.get_value(setting) == "1"


class AuthenticatedHandler(BaseHandler):
    """
    Base class for any handler that needs user to be authenticated
    """
    
    def user(self):
        """
        Get the current user as a User object, or raises a NotLoggedInError
        """
        user = self.get_current_user()
        if not user:
            raise NotLoggedInError("Unauthorized")
        return user


class NoCacheHandler(tornado.web.RequestHandler):
    def set_extra_headers(self, path):
        self.set_header('Cache-Control', 'no-cache, must-revalidate')
        self.set_header('Expires', '0')


class Http404Handler(BaseHandler):
    def get(self):
        self.set_status(404)
        self.render(u"../resources/templates/404.html",
                    path=self.request.path,
                    options=options)
