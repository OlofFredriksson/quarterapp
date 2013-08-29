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
import logging
import tornado.web

from tornado.escape import utf8
from tornado.options import options
from base import BaseHandler, AuthenticatedHandler, authenticated_user
from ..utils import *
from ..domain import BaseError, NotLoggedInError, Category, Activity, Color, ActivityDict, TimeSheet, Quarter, Comment

class QuarterEncoder(json.JSONEncoder):
    """
    JSON encoder for quarterapp specific objects
    """
    def default(self, obj):
        if isinstance(obj, ApiError):
            return { "code" : obj.code, "message" : obj.message }
        if isinstance(obj, Category):
            if hasattr(obj, "activities"):
                return { "id" : obj.id, "title" : obj.title, "activities" : obj.activities}
            else:    
                return { "id" : obj.id, "title" : obj.title }
        if isinstance(obj, Activity):
            return { "id" : obj.id, "category" : obj.category_id, "title" : obj.title,
                     "color" : obj.color.hex(), "enabled" : obj.enabled() }
        if isinstance(obj, TimeSheet):
            return { "date" : obj.date_as_string(), "quarters" : obj.quarters  }
        if isinstance(obj, Quarter):
            return { "id" : obj.id, "offset" : obj.offset, "activity" : obj.activity_id }
        if isinstance(obj, Comment):
            return { "id" : obj.id, "comment" : obj.comment }

class JsonApiHandler(BaseHandler):
    def _send(self, structure):
        structure = QuarterEncoder().encode(structure).replace("'", "\"")
        structure = utf8(structure)
        self._write_buffer.append(structure)
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.finish()

    def send_json(self, structure):
        """
        Sends the given object structure as JSON as response to the client.
        After calling this method, the output stream is closed and no further
        can occure.
        """
        self.set_status(200)
        self._send(structure)

    def send_json_error(self, structure):
        """
        Sends the given object structure as JSON as response to the client using
        the HTTP Bad Request error code.
        After calling this method, the output stream is closed and no further
        can occure.
        """
        self.set_status(400)
        self._send(structure)

    def send_success(self):
        """
        Sends a generic success JSON message to client.
        """
        self.write({
            "error" : 0,
            "message" :"Ok"})
        self.finish()

    def parameter(self, argument, error):
        argument = self.get_argument(argument, None)
        if not argument or len(argument) == 0:
            raise error
        return argument

class ApiError(BaseError):
    """
    Represents a API error that is returned to the user from the HTTP API.
    """
    def __init__(self, code, message):
        self.code = code
        self.message = message

ERROR_GENERAL               = ApiError(100, "An unknown error occured")
ERROR_NOT_IMPLEMENTED       = ApiError(101, "Not implemented")
ERROR_NOT_AUTHENTICATED     = ApiError(400, "Not logged in")
ERROR_NO_CATEGORY_TITLE     = ApiError(500, "Missing value for title")
ERROR_NO_CATEGORY_ID        = ApiError(501, "Missing value for category id")
ERROR_NO_ACTIVITY_COLOR     = ApiError(600, "Missing value for activity color")
ERROR_NO_ACTIVITY_ENABLED   = ApiError(601, "Missing value for activity enabled")
ERROR_NO_ACTIVITY_ID        = ApiError(602, "Missing value for activity id")
ERROR_NO_QUARTERS           = ApiError(700, "No quarters given")
ERROR_NOT_96_QUARTERS       = ApiError(701, "Expected 96 quarters")
ERROR_INVALID_SHEET_DATE    = ApiError(702, "Expected date in YYYY-MM-DD format")
ERROR_NO_INDEXES            = ApiError(703, "Missing value for indexes")
ERROR_NO_COMMENT            = ApiError(800, "Missing value for comment")

class CategoriesApiHandler(JsonApiHandler, AuthenticatedHandler):
    """
    HTTP API for getting the list of categories
    """

    @authenticated_user
    def get(self):
        try:
            user = self.user()
            categories = self.application.storage.get_categories(user)

            if not categories:
                categories = []

            self.send_json( { "categories" : categories } )

        except NotLoggedInError:
            self.send_json_error(ERROR_NOT_AUTHENTICATED)
        except  ApiError, error:
            self.send_json_error(error)

class CategoryApiHandler(JsonApiHandler, AuthenticatedHandler):
    """
    HTTP API for CRUD operations of Category
    """
    
    @authenticated_user
    def post(self):
        try:
            user = self.user()
            title = self.parameter("title", ERROR_NO_CATEGORY_TITLE)
            category = Category(title)

            if self.application.storage.save_category(category, user):
                self.send_json(category)
            else:
                self.send_json_error(ERROR_GENERAL)
        except NotLoggedInError:
            self.send_json_error(ERROR_NOT_AUTHENTICATED)
        except  ApiError, error:
            self.send_json_error(error)

    @authenticated_user
    def get(self, category_id):
        try:
            user = self.user()
            
            category = self.application.storage.get_category(category_id, user)
            if category:
                self.send_json(category)
            else:
                self.send_json_error(ERROR_GENERAL)
        except NotLoggedInError:
            self.send_json_error(ERROR_NOT_AUTHENTICATED)
        except  ApiError, error:
            self.send_json_error(error)

    @authenticated_user
    def put(self, category_id):
        try:
            user = self.user()
            title = self.parameter("title", ERROR_NO_CATEGORY_TITLE)
            category = Category(id = int(category_id), title = title)

            if self.application.storage.save_category(category, user):
                self.send_json(category)
            else:
                self.send_json_error(ERROR_GENERAL)
        except NotLoggedInError:
            self.send_json_error(ERROR_NOT_AUTHENTICATED)
        except  ApiError, error:
            self.send_json_error(error)

    @authenticated_user
    def delete(self, category_id):
        try:
            user = self.user()
            if self.application.storage.get_category(category_id, user).is_empty():
                if self.application.storage.delete_category(Category(id=category_id), user):
                    self.send_success()
                else:
                    self.send_json_error(ERROR_GENERAL)
            else:
                self.send_json_error(ERROR_GENERAL)
        except NotLoggedInError:
            self.send_json_error(ERROR_NOT_AUTHENTICATED)
        except  ApiError, error:
            self.send_json_error(error)

class ActivitiesApiHandler(JsonApiHandler, AuthenticatedHandler):
    """
    HTTP API for getting the list of activities
    """

    @authenticated_user
    def get(self, category_id):
        try:
            user = self.user()
            activities = []

            if category_id == "all":
                activities = self.application.storage.get_activities(user)
            else:
                category = Category(id = category_id)
                activities = self.application.storage.get_activities_for_category(category, user)

            self.send_json( { "activities" : activities } )

        except NotLoggedInError:
            self.send_json_error(ERROR_NOT_AUTHENTICATED)
        except  ApiError, error:
            self.send_json_error(error)
        
class CategoryAndActivitiesHandler(JsonApiHandler, AuthenticatedHandler):
    """
    HTTP API for getting the list of categories populated each with their list
    of activities.
    """

    @authenticated_user
    def get(self):
        try:
            user = self.user()
            categories = self.application.storage.get_categories_and_activities(user)
            self.send_json( { "categories" : categories } )

        except NotLoggedInError:
            self.send_json_error(ERROR_NOT_AUTHENTICATED)
        except  ApiError, error:
            self.send_json_error(error)

class ActivityApiHandler(JsonApiHandler, AuthenticatedHandler):
    """
    HTTP API for CRUD operations of Activity
    """
    
    @authenticated_user
    def post(self):
        try:
            user = self.user()
            category_id = self.parameter("category", ERROR_NO_CATEGORY_ID)
            title = self.parameter("title", ERROR_NO_CATEGORY_TITLE)
            color = self.parameter("color", ERROR_NO_ACTIVITY_COLOR)
            enabled = self.parameter("enabled", ERROR_NO_ACTIVITY_ENABLED)

            if enabled == "false":
                state = Activity.Disabled
            else:
                state = Activity.Enabled

            category = Category(id = category_id)
            activity = Activity(title = title, category_id = int(category_id), color = Color(color), state = state)

            if self.application.storage.save_activity(activity, category, user):
                self.send_json(activity)
            else:
                self.send_json_error(ERROR_GENERAL)
        except NotLoggedInError:
            self.send_json_error(ERROR_NOT_AUTHENTICATED)
        except  ApiError, error:
            self.send_json_error(error)

    @authenticated_user
    def get(self, activity_id):
        try:
            user = self.user()
            
            activity = self.application.storage.get_activity(activity_id, user)
            
            if activity:
                self.send_json(activity)
            else:
                self.send_json_error(ERROR_GENERAL)
        except NotLoggedInError:
            self.send_json_error(ERROR_NOT_AUTHENTICATED)
        except  ApiError, error:
            self.send_json_error(error)

    @authenticated_user
    def put(self, activity_id):
        try:
            user = self.user()
            category_id = self.parameter("category", ERROR_NO_CATEGORY_ID)
            title = self.parameter("title", ERROR_NO_CATEGORY_TITLE)
            color = self.parameter("color", ERROR_NO_ACTIVITY_COLOR)
            enabled = self.parameter("enabled", ERROR_NO_ACTIVITY_ENABLED)

            if enabled == "false":
                state = Activity.Disabled
            else:
                state = Activity.Enabled

            category = Category(id = category_id)
            activity = Activity(id = activity_id, title = title, category_id = int(category_id), color = Color(color), state = state)

            if self.application.storage.save_activity(activity, category, user):
                self.send_json(activity)
            else:
                self.send_json_error(ERROR_GENERAL)
        except NotLoggedInError:
            self.send_json_error(ERROR_NOT_AUTHENTICATED)
        except  ApiError, error:
            self.send_json_error(error)

    @authenticated_user
    def delete(self, activity_id):
        try:
            user = self.user()
            
            if self.application.storage.delete_activity(Activity(id=activity_id), user):
                self.send_success()
            else:
                self.send_json_error(ERROR_GENERAL)
        except NotLoggedInError:
            self.send_json_error(ERROR_NOT_AUTHENTICATED)
        except  ApiError, error:
            self.send_json_error(error)

class SheetApiHandler(JsonApiHandler, AuthenticatedHandler):
    @authenticated_user
    def get(self, date):
        try:
            user = self.user()
            sheet = self.application.storage.get_timesheet(extract_date(date), user)
            self.send_json(sheet)
        except NotLoggedInError:
            self.send_json_error(ERROR_NOT_AUTHENTICATED)
        except  ApiError, error:
            self.send_json_error(error)

    @authenticated_user
    def put(self, date):
        try:
            user = self.user()
            indexes = self.parameter("indexes", ERROR_NO_INDEXES)
            activity_id = self.parameter("activity", ERROR_NO_ACTIVITY_ID)

            quarters = []
            indexes_array = indexes.split(',')
            for index in indexes_array:
                quarters.append(Quarter(offset = index, activity_id = int(activity_id)))

            self.application.storage.add_quarters_to_sheet(extract_date(date), quarters, user)
            
            time_sheet = self.application.storage.get_timesheet(extract_date(date), user)
            activity_dict = ActivityDict(self.application.storage.get_activities(user))
            summary, total = summarize_quarters(time_sheet.quarters, activity_dict)
            self.send_json({ "summary" : summary, "total" : total })

        except NotLoggedInError:
            self.send_json_error(ERROR_NOT_AUTHENTICATED)
        except ApiError, error:
            self.send_json_error(error)

class CommentHandler(JsonApiHandler, AuthenticatedHandler):
    @authenticated_user
    def get(self, quarter_id):
        try:
            user = self.user()
            comment = self.application.storage.get_comment_for_quarter(quarter_id, user)
            self.send_json(comment)
        except NotLoggedInError:
            self.send_json_error(ERROR_NOT_AUTHENTICATED)
        except ApiError, error:
            self.send_json_error(error)

    @authenticated_user
    def put(self, quarter_id):
        try:
            user = self.user()
            message = self.parameter("comment", ERROR_NO_COMMENT)
            comment = Comment(comment = message)
            self.application.storage.save_comment(quarter_id, comment, user)
        except NotLoggedInError:
            self.send_json_error(ERROR_NOT_AUTHENTICATED)
        except ApiError, error:
            self.send_json_error(error)

    @authenticated_user
    def delete(self, quarter_id):
        try:
            user = self.user()
            self.application.storage.delete_comment(quarter_id, user)
        except NotLoggedInError:
            self.send_json_error(ERROR_NOT_AUTHENTICATED)
        except ApiError, error:
            self.send_json_error(error)