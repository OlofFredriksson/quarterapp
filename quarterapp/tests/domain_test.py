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

import unittest

from nose.tools import raises
from quarterapp.domain import *

class TestUser(unittest.TestCase):
    def test_user_is_inactive_by_default(self):
        joe = User(1, "joe@example.com")
        self.assertTrue(joe.inactive())
        self.assertFalse(joe.active())
        self.assertFalse(joe.disabled())

    def test_user_can_be_made_active(self):
        joe = User(1, "joe@example.com")
        self.assertTrue(joe.inactive())
        self.assertFalse(joe.active())

        joe.activate()

        self.assertTrue(joe.active())

class TestColor(unittest.TestCase):
    def test_create_color(self):
        color= Color("#fff")
        self.assertEqual("#fff", color.hex())

    @raises(InvalidColorError)
    def test_cannot_create_invalid_color(self):
        color= Color("banan")

    @raises(InvalidColorError)
    def test_cannot_create_empty_color(self):
        color= Color("")

    @raises(TypeError)
    def test_cannot_create_none_color(self):
        color= Color(None)
    
    def test_luminance_color(self):
        c1 = Color("#fff").luminance_color(0)
        c2 = Color("#fcaf3e").luminance_color(-0.25)
        c3 = Color("#fcaf3e").luminance_color(0.25)
        c4 = Color("#3465a4").luminance_color(0.66)
        self.assertEqual("#ffffff", c1.hex())
        self.assertEqual("#bd832f", c2.hex())
        self.assertEqual("#ffdb4e", c3.hex())
        self.assertEqual("#56a8ff", c4.hex())

class TestActivity(unittest.TestCase):
    def test_empty_activity(self):
        activity = Activity(1, category_id = 1)
        self.assertIsNotNone(activity)

    def test_activity_color(self):
        activity = Activity(1, color = Color("#cdcdcd"), category_id = 1)
        self.assertEquals("#cdcdcd", activity.color.hex())

    def test_change_activity_color(self):
        activity = Activity(1, color = Color("#cdcdcd"), category_id = 1)
        self.assertEquals("#cdcdcd", activity.color.hex())
        activity.color = Color("#123123")
        self.assertEquals("#123123", activity.color.hex())

    def test_activity_has_default_title(self):
        activity = Activity(1, category_id = 1)
        self.assertIsNotNone(activity.title)

    def test_can_change_activity_title(self):
        activity = Activity(1, title = "Comet", category_id = 1)
        self.assertEquals("Comet", activity.title)

        activity.title = "House"
        self.assertEquals("House", activity.title)

    def test_no_meta_data_by_default(self):
        activity = Activity(1, title="Comet", category_id = 1)
        self.assertEquals("", activity.meta_data())

class TestCategory(unittest.TestCase):
    
    def test_category_needs_nothing(self):
        category = Category()

    def test_category_can_have_title(self):
        category = Category("Title")
        self.assertIsNotNone(category)

    def test_category_can_have_id(self):
        category = Category("title", id = 5)
        self.assertEqual(5, category.id)

class TestTimeSheet(unittest.TestCase):
    def test_can_create_sheet(self):
        time_sheet = TimeSheet()
        
        self.assertIsNotNone(time_sheet)

    