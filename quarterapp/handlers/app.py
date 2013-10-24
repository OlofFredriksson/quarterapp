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

import tornado.web, datetime
from ..utils import *
from tornado.options import options
from base import BaseHandler, AuthenticatedHandler, NoCacheHandler, authenticated_user, User, authenticated_admin
from ..domain import Color, ActivityDict, Category, Quarter, Week, Report


class ActivityViewHandler(AuthenticatedHandler, NoCacheHandler):
    """
    The handler responsible for render the activity view (where also
    categories are managed).
    """
    @authenticated_user
    def get(self):
        user = self.get_current_user()
        categories = self.application.storage.get_categories_and_activities_with_usage(user)
        
        self.render(u"../resources/templates/app/activities.html",
                    options=options,
                    current_user=self.get_current_user(),
                    categories=categories)


class TimesheetViewHandler(AuthenticatedHandler, NoCacheHandler):
    """
    Responsible for render a timesheet, the summary and the list of
    available activities.
    """

    @staticmethod
    def _default_sheet():
        quarters = []
        for i in range(0, 96):
            quarters.append(Quarter())
        return quarters

    def _get_list_of_quarters(self, date, activity_dict, user):
        quarters = TimesheetViewHandler._default_sheet()
        time_sheet = self.application.storage.get_timesheet(date, user)
        for quarter in time_sheet.quarters:
            quarter.color = Color(activity_dict[int(quarter.activity_id)].color.hex())
            quarter.border_color = Color(activity_dict[int(quarter.activity_id)].color.luminance_color(-0.2).hex())
            quarters[quarter.offset] = quarter

        return quarters

    @authenticated_user
    def get(self, sheet_date=None):
        user = self.get_current_user()

        date_obj = None
        today = datetime.date.today()

        if sheet_date:
            if valid_date(sheet_date):
                date_obj = extract_date(sheet_date)
        else:
            date_obj = today
            sheet_date = today 

        yesterday = date_obj - datetime.timedelta(days=1)
        tomorrow = date_obj + datetime.timedelta(days=1)
        weekday = date_obj.strftime("%A")

        categories_and_activities = self.application.storage.get_categories_and_activities(user)
        activities = self.application.storage.get_activities(user)
        activity_dict = ActivityDict(activities)
        quarters = self._get_list_of_quarters(date_obj, activity_dict, user)

        summary, summary_total = summarize_quarters(quarters, activity_dict)

        self.render(u"../resources/templates/app/timesheet.html",
                    options=options,
                    current_user=self.get_current_user(),
                    date=date_obj,
                    weekday=weekday,
                    today=today,
                    yesterday=yesterday,
                    tomorrow=tomorrow,
                    summary=summary,
                    summary_total=summary_total,
                    categories_and_activities=categories_and_activities,
                    quarters=quarters)


class ReportViewHandler(BaseHandler, NoCacheHandler):
    """
    Responsible for showing the different reports
    """
    def _generate_report(self, from_date, to_date, user):
        logging.info("Generating report between dates %s and %s" % (from_date, to_date))

        report = Report()
        from_week = from_date.isocalendar()[1]
        to_week = to_date.isocalendar()[1]
        for i in range(from_week, to_week + 1):
            year = from_date.year

            if to_week < from_week: # Report from dec -> jan
                year = to_date.year

            week = Week(year, i)
            for day_time_sheet in week:
                real_time_sheet = self.application.storage.get_timesheet(day_time_sheet.date, user)
                week.update_sheet(real_time_sheet)
            report.weeks.append(week)
        return report

    @authenticated_user
    def get(self):
        user = self.get_current_user()
        from_date = self.get_argument("from-date", "")
        to_date = self.get_argument("to-date", "")
        report = None
        error = None

        activities = self.application.storage.get_activities(user)
        activity_dict = ActivityDict(activities)

        if from_date or to_date:
            if valid_date(from_date) and valid_date(to_date):
                report = self._generate_report(extract_date(from_date), extract_date(to_date), user)
            else:
                error = True
                
        self.render(u"../resources/templates/app/reports.html",
                    options=options,
                    current_user=self.get_current_user(),
                    from_date=from_date,
                    to_date=to_date,
                    activities=activity_dict,
                    error=error,
                    report=report)


class ProfileViewHandler(BaseHandler):
    """
    Responsible for showing the user profile options
    """

    @authenticated_user
    def get(self):
        self.render(u"../resources/templates/app/profile.html",
                    options=options,
                    current_user=self.get_current_user(),
                    delete_account_error=None)
