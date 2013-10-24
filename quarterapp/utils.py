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

import datetime
import logging
import sys
import hashlib
import base64
import os
import re
from collections import Counter


def generate_pagination(total, current, max_per_page, max_links, query_filter = None):
    """
    Generate a list of pagination links based on the following input.

    Tries to keep the current page at the center of the returned list

    Args:
        total The total number of items (not per page)
        current The current position / index within that range (0:total)
        max_per_page The maximum number of links per page
        max_pages The maximum number of pagination links to return

    Returns:
        The list of pagination links
    """
    pagination = []
    total_pages = 0
    current_page = 0
    
    try:
        if total == 0:
            total_pages = 0
        elif int(total) < int(max_per_page):
            total_pages = 1
        else:
            total_pages = int(total) / int(max_per_page)
            if int(total) % int(max_per_page) != 0:
                total_pages += 1
        
        if int(current) < int(max_per_page):
            current_page = 0
        else:
            current_page = int(current) / int(max_per_page)

        for i in range(total_pages):
            start = int(i) * int(max_per_page)

            link = ""
            if query_filter:
                link = "/admin/users?start={0}&count={1}&filter={2}".format(start, max_per_page, query_filter)
            else:
                link = "/admin/users?start={0}&count={1}".format(start, max_per_page)

            current_page = int(start) <= int(current) < (int(start) + int(max_per_page))
            
            p = {'index': i, 'link': link, 'current': current_page}
            pagination.append(p)
    except:
        logging.warn("Could not generate the users pagination: %s", sys.exc_info())

    return pagination


def hash_password(password, salt):
    """
    Performs a password hash using the given salt.

    Args:
        password The plain text password
        salt The applications salt

    Returns:
        The hashed password
    """
    sha = hashlib.sha512()
    sha.update(password + salt)
    return base64.urlsafe_b64encode(sha.digest())


def valid_date(date):
    """
    Check if the given string is a valid date format YYYY-MM-DD

    @param date The date in string format
    @return True if the date string is correctly formatted, else False
    """
    return extract_date(date) is not None


def extract_date(date):
    """
    Extract a date object based on the given date string, the string must be formatted
    YYYY-MM-DD else None will be returned.

    @param date The date in string format
    @return The date object with the given date, or None
    """
    try:
        parts = date.split("-")
        if len(parts) != 3:
            return None
        else:
            if len(parts[0]) == 4 and len(parts[1]) == 2 and len(parts[2]) == 2:
                date_obj = datetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
                return date_obj
            else:
                return None
    except Exception, e:
        logging.exception(e)
        return None


def summarize_quarters(quarters, activity_dict):
    # Convert the list of quarters to a list of only activity_id
    quarter_values = map(lambda q: q.activity_id, quarters)
    summary_list = []
    summary_dict = Counter(quarter_values)
    summary_total = 0

    for activity_id in summary_dict:
        if activity_id == -1:
            continue

        activity_color = "#ccc"
        activity_title = "Unknown"

        if long(activity_id) in activity_dict:
            activity_color = activity_dict[long(activity_id)].color.hex()
            activity_title = activity_dict[long(activity_id)].title

        activity_summary = float(summary_dict[activity_id] / 4.0)
        summary_total += activity_summary
        summary_list.append({"id": activity_id, "color": activity_color,
                             "title": activity_title, "sum": "%.2f" % activity_summary})
    return summary_list, "%.2f" % summary_total


def activation_code():
    """
    Generate and return a URL friendly activation code

    @return The activation code
    """
    code = os.urandom(16).encode("base64")
    code = re.sub("[\W\d]", "", code.strip())
    return code