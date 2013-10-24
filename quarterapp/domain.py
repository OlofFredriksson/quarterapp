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
#

import re
import logging
from datetime import date, timedelta, datetime
from collections import Counter
from utils import *


class BaseError(Exception):
    """
    Base exception for quarterapp, all other exceptions should derive
    from this.
    """
    def __init__(self, message):
        self.message = message


class InvalidColorError(BaseError):
    pass


class RangeTooBigError(BaseError):
    pass


class InvalidRangeStartError(BaseError):
    pass


class InvalidRangeLengthError(BaseError):
    pass


class NotLoggedInError(BaseError):
    pass


class Color(object):
    """
    Represents a CSS color but only supports HEX format
    """
    # Pre-compile regular expression
    color_hex_match_re = re.compile(r"^(#)([0-9a-fA-F]{3})([0-9a-fA-F]{3})?$")

    """
    Represents a CSS color but only supports HEX format
    """
    def __init__(self, hex):
        """
        Creates a color object, will raise InvalidColorError if the
        given hex value is not correct.

        @param hex The hex value of this color
        @return A Color object
        """
        if not Color.color_hex_match_re.match(hex):
            raise InvalidColorError("Not a valid HEX color code")
        self.hex_value = hex

    def hex(self):
        """
        Get the hex value for this color, will always be 4 or 7 chars (#fff or #cdcdcd)

        @return The colors HEX value
        """
        return self.hex_value

    def luminance_color(self, lum):
        """
        Create a new Color object with another luminance value. Use positive for lighter and
        negative to generate a darker color.

        @param lum Percentage luminance to alter. 
        @return A new Color object
        """
        color_code = self.hex_value.replace("#", "")
        lum = lum or 0;
        
        if len(color_code) == 3:
            color_code = color_code[0]+color_code[0]+color_code[1]+color_code[1]+color_code[2]+color_code[2]

        color = "#"
        for i in range(3):
            c = int(color_code[i * 2 : (i * 2) + 2], 16)
            c = int(round( min( max(0, c + (c * lum)), 255)))
            c = hex(c)[2:]
            color += str("00" + c)[len(c):]

        return Color(color)

    def __str__(self):
        return self.hex_value


class UserType(object):
    """
    Represents the different type of users QuarteraApp has, a user can
    only be one type at a time.
    """
    # Administrator can access all areas
    Administrator = 1
    # Beta users (this should be removed once not needed)
    Beta = 2
    # Normal users can use the web application
    Normal = 3
    # Premium users can use the web application and the HTTP API (ios / android apps)
    Premium = 4

    @classmethod
    def from_string(cls, user_type):
        ut = UserType.Normal
        if user_type == "admin":
            ut = UserType.Administrator
        return ut


class UserState(object):
    """
    Represents the different state a user might have
    """
    # User is not yet active and cannot use application
    Inactive = 0
    # User is enabled (can login, use application)
    Active = 1
    # User is disabled and cannot use application
    Disabled = 3

    @classmethod
    def from_string(cls, state):
        us = UserState.Inactive
        if state == "active":
            us = UserState.Inactive
        elif state == "disabled":
            us = UserState.Disabled
        return us


class User(object):
    """
    Represents a user (regardless of authentication) of QuarteraApp
    """
    
    def __init__(self, username, id = -1, password = "", type = UserType.Normal, state = UserState.Inactive, last_login = "Unknown"):
        self.id = id
        self.username = username
        self.password = password
        self.last_login = last_login
        self.type = type
        self.state = state
        self.enabled = True

    def active(self):
        return self.state == UserState.Active

    def inactive(self):
        return self.state == UserState.Inactive

    def disabled(self):
        return self.state == UserState.Disabled

    def disable(self):
        self.state = UserState.Disabled

    def activate(self):
        self.state = UserState.Active

    def is_admin(self):
        return self.type == UserType.Administrator

    def __str__(self):
        return "ID: %s Username: %s Type: %s State: %s" % (self.id, self.username, self.type, self.state)


class Activity(object):
    """
    An activity is used to mark the time (quarters) during a day. In the
    simplest form it contains an id, title and a color code. It does however
    contain a meta-data field that can be used for anything. The core application
    does not read the meta-data, plugins might use it though.
    """
    # Activity is enabled, this it can be used in a timesheet
    Enabled = 1
    # Activity is disabled, it cannot be used in new timesheets, but accessible for reports
    Disabled = 0

    def __init__(self, id=-1, color=Color("#fff"), title="Untitled", state=Enabled, meta="", category_id=-1):
        self.id = id
        self.color = color
        self.title = title
        self.state = state
        self.meta = meta
        self.category_id = category_id
        self.usage = 0

    def disable(self):
        """
        Set the activity as disabled
        """
        self.state = Activity.Disabled

    def disabled(self):
        """
        Returns True if this activity is disabled
        
        @return True if this activity is disabled, else False
        """
        return self.state == Activity.Disabled

    def enable(self):
        """
        Set the activity as enabled
        """
        self.state = Activity.Enabled

    def enabled(self):
        """
        Returns True if this activity is enabled
        
        @return True if this activity is enabled, else False
        """
        return self.state == Activity.Enabled

    def meta_data(self):
        """
        Get the activities meta-data. This can be anything, quarterapp itself
        does not use it, but plugins might use it to store extra information about
        activities.
        """
        return self.meta


class ActivityDict(dict):
    """
    Creats a dictionary containing Activity objects using the id as key
    """
    def __init__(self, activity_list):
        for activity in activity_list:
            self[activity.id] = activity


class Category(object):
    """
    Each activity belongs to exactly one category, and a category always has
    at least one activity.

    An id of -1 indicates that this Category has not yet been stored to database.
    """
    def __init__(self, title = "", id = -1, empty = False):
        self.title = title
        self.id = id
        self.empty = empty

    def __str__(self):
        return self.title

    def is_empty(self):
        return self.empty


class TimeRange(object):
    """
    Represents a range of time given in quarters, that is  a range of quarters
    that are marked using the same activity.

    The range always use quarters as unit and its length cannot excee 96. 

    1.5 hours of the same activiyt from 13:00 to 14:30 would be the range

    start: 52
    stop: 6
    """

    def __init__(self, id = -1, start = 0, length = 0, activity_id = -1):
        """"
        Create a time range. The range must not exceed 96 quarters, e.g. if the
        range starts at 90, the length cannot be longer than 5

        Args:
            start: The quarter to start with (0-95)
            length: The total number of quarters (1-96)

        Returns:
            An instance of TimeRange
        
        Raises:
            RangeTooBigError: If the total length exceeds 96 quarters
            InvalidRangeLengthError: If the length is less than 0
            InvalidRangeStartError: If the start position is less than 0 or greater than 95
        """
        if start + length > 96:
            raise RangeTooBigError("Time range cannot start at %d and contain %d quarters" % (start, length))
        if start < 0 or start > 95:
            raise InvalidRangeStartError("Time range must be between 0 and 95")
        if length < 0:
            raise InvalidRangeLengthError("Time range must be greater than 0")

        self.id = id
        self.start = start
        self.length = length
        self.activity_id = activity_id

    def adjust(self, other_range):
        """
        Adjust this range after the other range. Shrink the size of this range if overlapping
        """
        if self.start < other_range.start and (self.start + self.length) > other_range.start:
            logging.info("Adjusting timeranges:\n\t%s\n\t%s" % (self, other_range))
            logging.info("Adjusting time range starting at %d from length %d to %d" % (self.start, self.length, (other_range.start - self.start)))
            self.length = other_range.start - self.start
            logging.info("Result: %s" % (self,))

    def merge(self, other_range):
        """
        Merge the two ranges together, resulting in that the other range will have a
        length of zero once this method returns
        """
        logging.info("Merging time ranges:\n\t%s\n\t%s" % (self, other_range))
        self.length = self.length + other_range.length
        other_range.length = 0
        logging.info("Resulting time range: %s" % (self,))

    def ends(self):
        return self.start + self.length

    def __str__(self):
        return "id = %d start=%d length=%d activity=%d" % (self.id, self.start, self.length, self.activity_id)


class ActivitySummary(object):
    """Used to the summarized amount of time spent on a activity"""
    def __init__(self, id=id, amount=0.0):
        self.id = id
        self.amount = amount

    def __str__(self):
        return "activity_id=%d amount=%d" % (self.id, self.amount)


class TimeSheet(object):
    """
    Represents a day (24 hours) and contains any Quarters reported for that day.

    It can contain many or none quarters, but its total quarter count can never
    exceed 96 quarters.
    """

    def __init__(self, date = None):
        """
        Construct a TimeSheet
        """
        self.date = date
        self.weekday = date.weekday() # 0 based
        self.quarters = []
        self.summary = [] # Summarized list of activities

    def summarize(self):
        """
        Summarize the quarters and create activities for the sums
        """
        quarter_values = map(lambda q: q.activity_id, self.quarters)
        summary = Counter(quarter_values)
        self.summary = []
        for aid in summary:
            if aid == "-1":
                continue
            self.summary.append(ActivitySummary(aid, float(summary[aid] / 4.0)))
        self.summary.sort(key = lambda x: int(x.id))

    def total(self):
        """
        Get the total number of hours worth of activities for this day
        """
        accumelator = 0
        for act in self.summary:
            accumelator += act.amount

        return accumelator

    def clear(self):
        """
        Clear this time sheet and remove any quarters registered.
        """
        self.quarters = []

    def time(self, activity_id):
        for act in self.summary:
            if act.id == activity_id:
                return act.amount
        return 0

    def get_weekday(self):
        return self.date.weekday()

    def date_as_string(self):
        """
        Get this days date as a YYYY-MM-DD formatted string
        """
        return self.date.strftime("%Y-%m-%d")

    def __str__(self):
        return "date = %s total = %d quarters = %s" % (self.date, self.total(), self.quarters)


class Quarter(object):
    """
    Represents a single quarter
    """

    def __init__(self, id = -1, offset = 0, activity_id = -1, comment_id = -1):
        """
        Args:
            id: The quarter id
            offset: The quarter offset on a given day (0-95)
            activity_id: The activity used for this quarter
            comment_id: Id for any comment this quarter might have
        """
        self.id = id
        self.offset = int(offset)
        self.activity_id = int(activity_id)
        self.comment_id = comment_id
        self.color = "#fff"
        self.border_color = "#ccc"

    def __str__(self):
        return "id=%d offset=%s comment_id=%s color=%s" % (self.id, self.offset, self.comment_id, self.color)


class Comment(object):
    def __init__(self, id = -1, comment = ""):
        self.id = id
        self.comment = comment

    def __str__(self):
        return "id = %d comment = '%s'" % (self.id, self.comment)


class Week(object):
    """
    A week always contains 7 time sheets, no more no less.
    """

    def __init__(self, year, week):
        self.year = year
        self.week = week
        self.sheets = []
        self._setup_empty_sheets()

    def _setup_empty_sheets(self):
        first_day = Week._week_start_date(self.year, self.week)
        for i in range(7):
            delta = timedelta(days=i)
            self.sheets.append(TimeSheet(date=first_day + delta))

    @staticmethod
    def _week_start_date(year, week):
        # From SO http://stackoverflow.com/a/1287862
        d = date(year, 1, 1)    
        delta_days = d.isoweekday() - 1
        delta_weeks = week
        if year == d.isocalendar()[0]:
            delta_weeks -= 1
        delta = timedelta(days=-delta_days, weeks=delta_weeks)
        return d + delta

    def total(self):
        """
        Get the total number of hours spent on any activity for this week

        Returns:
            The total number of hours this week
        """
        accumelator = 0
        for sheet in self.sheets:
            accumelator += sheet.total()
        return accumelator

    def update_sheet(self, sheet):
        """
        Updates the sheet with the given sheet
        """
        # TODO Check that sheet is within range
        self.sheets[sheet.weekday] = sheet

    def week_of_year(self):
        """
        Get the week of year for this week
        """
        return self.week

    def get_weeks_activities(self):
        """
        Get a sorted unique list of all the weeks activities where the
        activities amount is summed up
        """
        all_activities = []
        for sheet in self.sheets:
            all_activities += sheet.summary

        unique_activities = _merge_activity_summaries(all_activities)
        unique_activities.sort(key=lambda x: int(x.id))
        return unique_activities

    # Iteration support
    def __iter__(self):
        return self.sheets.__iter__()

    def next(self):
        return self.sheets.next()

    def __str__(self):
        desc = "Week: %d\n" % self.week
        desc += "Sheets: \n"
        for sheet in self.sheets:
            desc += "\t%s\n" % sheet.date
            for act in sheet.summary:
                desc += "\t\t %s: %s\n" % (act.id, act.amount)
        return desc


class Report(object):
    def __init__(self):
        self.weeks = []
        self.total_activities = []

    def add_week(self, week):
        """
        Add a new week to this report and update the total summary.

        Args:
            week: The Week object to add
        """
        self.weeks.append(week)
        week_activities = week.get_weeks_activities()
        activities = self.total_activities + week_activities
        self.total_activities = _merge_activity_summaries(activities)
        self.total_activities.sort(key=lambda x: int(x.id))

    def total_hours(self):
        """Calculate the total number of hours"""
        acc = 0
        for a in self.total_activities:
            acc += a.amount
        return acc


def _merge_activity_summaries(activities):
    """
    Filter any duplicate activities and merge the amount of time spent.

    Args:
        A list of ActivitySummary objects

    Returns:
        A list of unique ActivitySummary objects
    """
    unique_activities = []
    for aa in activities:
        matches = list((ua for ua in unique_activities if ua.id == aa.id))
        if len(matches) > 0:
            # Item already exist in list of unique activities
            # Mutable data, yay!
            updated_activity = ActivitySummary(aa.id, aa.amount + matches[0].amount)

            unique_activities.remove(matches[0])
            unique_activities.append(updated_activity)
        else:
            unique_activities.append(aa)
    return unique_activities
