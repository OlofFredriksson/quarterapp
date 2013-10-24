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

from tornado.options import options
from base import BaseHandler, AuthenticatedHandler, authenticated_user
from ..utils import *
from ..email_utils import *


class LoginViewHandler(AuthenticatedHandler):
    """
    The handler responsible for login
    """
    def get(self):
        self.render(u"../resources/templates/account/login.html",
                    options=options,
                    current_user=self.get_current_user(),
                    error=False,
                    username=None,
                    allow_signups=False)

    def post(self):
        username = self.get_argument("username", "")
        password = self.get_argument("password", "")

        hashed_password = hash_password(password, username)
        user = self.application.storage.get_user_by_username(username)

        if user and user.password == hashed_password:
            # TODO This should check if active or not
            logging.info("User authenticated")
            self.set_current_user(user)
            self.redirect(u"/application/timesheet")
        else:
            logging.info("User not authenticated")
            self.set_current_user(None)
            self.render(u"../resources/templates/account/login.html",
                        options=options,
                        current_user=self.get_current_user(),
                        error=True,
                        username=username,
                        allow_signups=False)


class LogoutViewHandler(BaseHandler):
    """
    The handler responsible for login
    """
    def get(self):
        self.clear_cookie("user")
        self.redirect(u"/")  # TODO Make this configurable


class ChangePasswordHandler(AuthenticatedHandler):
    @authenticated_user
    def get(self):
        self.render(u"../resources/templates/account/change_password.html",
                    options=options,
                    current_user=self.get_current_user(),
                    error=False,
                    done=False)

    @authenticated_user
    def post(self):
        user = self.user()

        current_password = self.get_argument("current-password", None)
        new_password = self.get_argument("new-password", None)
        verify_password = self.get_argument("verify-password", None)

        error = None
        done = False
        if not user:
            error = True
        elif not new_password == verify_password:
            error = True
        else:
            hashed_password = hash_password(current_password, user.username)
            user = self.application.storage.get_user(user.id)
            if not hashed_password == user.password:
                error = True

        if not error:
            user.password = hash_password(new_password, user.username)
            self.application.storage.save_user(user)
            done = True
        
        self.render(u"../resources/templates/account/change_password.html",
                    options=options,
                    current_user=self.get_current_user(),
                    error=error,
                    done=done)


class DeleteAccountHandler(AuthenticatedHandler):
    @authenticated_user
    def post(self):
        user = self.user()
        password = self.get_argument("password", None)

        error = None
        if not user or not password:
            error = True
        else:
            hashed_password = hash_password(password, user.username)
            user = self.application.storage.get_user(user.id)
            if not hashed_password == user.password:
                error = True

        if error:
            logging.error("Could not delete account")
            self.render(u"../resources/templates/app/profile.html",
                        options=options,
                        current_user=self.get_current_user(),
                        delete_account_error=True)
        else:
            self.application.storage.delete_user(user)
            self.set_current_user(None)
            self.redirect(u"/")


class ForgotPasswordHandler(BaseHandler):
    def get(self):
        self.render(u"../resources/templates/account/forgot.html",
                    options=options,
                    current_user=self.get_current_user(),
                    error=None,
                    username=None)

    def post(self):
        username = self.get_argument("username", "")
        error = None
        if len(username) == 0:
            error = True
        else:
            reset_code = activation_code()
            if self.application.storage.set_user_reset_code(username, reset_code):
                send_reset_email(username, reset_code)
                self.redirect(u"/reset")
            else:
                error = True
        if error:
            self.render(u"../resources/templates/account/forgot.html",
                        options=options,
                        current_user=self.get_current_user(),
                        error=True,
                        username=username)


class ResetPasswordHandler(BaseHandler):
    def get(self, code_parameter = None):
        code = None
        if code_parameter:
            code = code_parameter

        self.render(u"../resources/templates/account/reset.html",
                    options=options,
                    current_user=self.get_current_user(),
                    error=None,
                    code=code)

    def post(self):
        code = self.get_argument("code", "")
        password = self.get_argument("password", "")
        verify_password = self.get_argument("verify-password", "")

        error = None
        if len(code) == 0:
            error = True
        if len(password) == 0:
            error = True
        if not password == verify_password:
            error = True

        if not error:
            salt = self.application.storage.username_for_reset_code(code)
            salted_password = hash_password(password, salt)
            if self.application.storage.reset_password(code, salted_password):
                self.redirect(u"/login")
            else:
                error = True

        if error:
            self.render(u"../resources/templates/account/reset.html",
                        options=options,
                        current_user=self.get_current_user(),
                        error=True,
                        code=code)


class SignupHandler(BaseHandler):
    def get(self):
        if self.enabled("allow-signups"):
            self.render(u"../resources/templates/account/signup.html",
                        options=options,
                        current_user=self.get_current_user(),
                        error=None,
                        username="")
        else:
            raise tornado.web.HTTPError(404)

    def post(self):
        if not self.enabled("allow-signups"):
            raise tornado.web.HTTPError(500)

        username = self.get_argument("email", "")

        error = False
        if len(username) == 0:
            error = "empty"
        if not self.application.storage.unique_username(username):
            error = "not_unique"

        if not error:
            try:
                code = activation_code()
                if send_signup_email(username, code):
                    self.application.storage.signup_user(username, code, self.request.remote_ip)
                    self.render(u"../resources/templates/account/signup_instructions.html",
                                options=options,
                                current_user=self.get_current_user())
                    return
                else:
                    error = True
            except Exception, e:
                logging.error("Could not signup user: %s" % username)
                logging.exception(e)
                error = True
        
        self.render(u"../resources/templates/account/signup.html",
                    options=options,
                    current_user=self.get_current_user(),
                    error=error,
                    username=username)


class ActivationHandler(BaseHandler):
    def get(self, code_parameter = None):
        code = None
        if code_parameter:
            code = code_parameter
        
        if self.enabled("allow-activations"):
            self.render(u"../resources/templates/account/activate.html",
                        options=options,
                        current_user=self.get_current_user(),
                        error=None,
                        code=code)
        else:
            raise tornado.web.HTTPError(404)

    def post(self):
        if not self.enabled("allow-activations"):
            raise tornado.web.HTTPError(500)

        code = self.get_argument("code", "")
        password = self.get_argument("password", "")
        verify_password = self.get_argument("verify-password", "")

        error = None
        if len(code) == 0:
            error = "not_valid"
        if not password == verify_password:
            error = "not_matching"

        if not error:
            salt = self.application.storage.username_for_activation_code(code)
            salted_password = hash_password(password, salt)
            if self.application.storage.activate_user(code, salted_password, salt):
                self.redirect(u"/login")
                return

        self.render(u"../resources/templates/account/activate.html",
                    options=options,
                    current_user=self.get_current_user(),
                    error=error,
                    code=code)
