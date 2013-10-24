#!/usr/bin/env python
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

import os
import logging
import tornado.ioloop
import tornado.web
import pkg_resources

from tornado.options import options, define
from settings import QuarterSettings
from handlers import Http404Handler
from handlers.app import *
from handlers.admin import *
from handlers.api import *
from handlers.account import *

HANDLERS_END_POINT = "quarterapp.handlers"
STORAGE_END_POINT = "quarterapp.storages"
VIEWS_END_POINT = "quarterapp.views"

DATABASE_FILE_NAME = "quarterapp.db"


def configure():
    define("base_url", help="Application base URL (including port but not schema")
    define("port", help="Port to listen on", type=int)
    define("cookie_secret", help="Random long hexvalue to secure cookies")
    define("storage", help="Choice of storage (default is SQLite)")
    define("compressed_resources", type=bool, help="Use compressed JavaScript and CSS")
    define("mail_host", help="SMTP host name")
    define("mail_port", type=int, help="SMTP port number")
    define("mail_user", help="SMTP Authentication username")
    define("mail_password", help="SMTP Authentication password")
    define("mail_sender", help="Email sender address")
    
    try:
        tornado.options.parse_command_line()
        tornado.options.parse_config_file("quarterapp.conf")
    except IOError:
        logging.warning("Configuration file not found (quarterapp.conf)!")
        exit(1)


def find_handlers():
    routes = []
    for plugin_end_point in pkg_resources.iter_entry_points(HANDLERS_END_POINT):
        logging.info("Loading route %s", plugin_end_point.name)
        routes.append(plugin_end_point.load()())  # Load class and create an instance
    return routes


def find_storages():
    storages = []
    for plugin_end_point in pkg_resources.iter_entry_points(STORAGE_END_POINT):
        logging.info("Loading storage %s", plugin_end_point.name)
        storages.append(plugin_end_point.load()())  # Load class and create an instance
    return storages


def setup_handlers(application):
    for handler in find_handlers():
        application.add_handlers(r".*", [
            (handler.path, handler.handler)])


def setup_storage(application):
    if not options.storage:
        logging.info("Using built in SQLite storage")
        from storage.default import DefaultStorage
        application.storage = DefaultStorage(DATABASE_FILE_NAME)
    else:
        for storage in find_storages():
            logging.info("Looking at %s", storage.name)
            application.storage = storage.plugin


def setup_settings(application):
    application.quarter_settings = QuarterSettings(application.storage)


def quarterapp_main():
    application = tornado.web.Application(
        [
            # Account views
            (r"/login", LoginViewHandler),
            (r"/logout", LogoutViewHandler),
            (r"/password", ChangePasswordHandler),
            (r"/delete-account", DeleteAccountHandler),
            (r"/forgot", ForgotPasswordHandler),
            (r"/reset", ResetPasswordHandler),
            (r"/signup", SignupHandler),
            (r"/activate", ActivationHandler),
            (r"/activate/([^\/]+)", ActivationHandler),

            # Application views
            (r"/application/activities", ActivityViewHandler),
            (r"/application/timesheet", TimesheetViewHandler),
            (r"/application/timesheet/([^\/]+)", TimesheetViewHandler),
            (r"/application/report", ReportViewHandler),
            (r"/application/profile", ProfileViewHandler),

            # Admin views
            (r"/admin", AdminDefaultHandler),
            (r"/admin/users", AdminUsersHandler),
            (r"/admin/user/new", AdminNewUserHandler),
            (r"/admin/user/([^\/]+)", AdminEditUserHandler),
            (r"/admin/user/delete/([^\/]+)", AdminDeleteUserHandler),
            (r"/admin/metrics", AdminMetricsHandler),
            (r"/admin/setting/([^\/]+)", AdminSettingsHandler),

            # HTTP API
            (r"/api/categories/all", CategoriesApiHandler),
            (r"/api/category", CategoryApiHandler),
            (r"/api/category/([^\/]+)", CategoryApiHandler),
            (r"/api/activities/([^\/]+)", ActivitiesApiHandler),
            (r"/api/activity", ActivityApiHandler),
            (r"/api/activity/([^\/]+)", ActivityApiHandler),
            (r"/api/categories-and-activities/", CategoryAndActivitiesHandler),
            (r"/api/sheet/([^\/]+)", SheetApiHandler),
            (r"/api/comment/([^\/]+)", CommentHandler),

            (r".*", Http404Handler)
        ],
        login_url="/login",
        static_path=os.path.join(os.path.dirname(__file__), "resources/static"),
        template_path=None, # Files will be relative to calling file
        cookie_secret=options.cookie_secret,
        gzip=True,
        debug=True)

    setup_storage(application)
    setup_handlers(application)
    setup_settings(application)

    logging.info("Starting quarterapp")
    main_loop = tornado.ioloop.IOLoop.instance()

    try:
        application.listen(options.port)
        main_loop.start()
    except KeyboardInterrupt:
        logging.info("Quitting quarterapp")
    except Exception, e:
        logging.error("Could not start quarterapp:")
        logging.exception(e)
        exit()


def main():
    configure()
    quarterapp_main()
