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

from quarterapp.utils import *

class TestUnit(unittest.TestCase):

    def test_valid_date(self):
        self.assertTrue(valid_date("2013-01-29"))
        self.assertTrue(valid_date("1999-12-29"))
        self.assertTrue(valid_date("2013-11-01"))
        self.assertTrue(valid_date("2012-02-29"))

        self.assertFalse(valid_date("2013-29-11"))
        self.assertFalse(valid_date("2013-9-1"))
        self.assertFalse(valid_date("2013-02-29"))
        self.assertFalse(valid_date("13-1-29"))
        self.assertFalse(valid_date("29/01/2013"))
        self.assertFalse(valid_date("01/29/2013"))

    def test_extract_date(self):
        self.assertEqual(None, extract_date(123))
        self.assertEqual(datetime.date(2013, 2, 2), extract_date("2013-02-02"))

