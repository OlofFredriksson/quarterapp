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
import os
import tempfile

from quarterapp.domain import *
from quarterapp.storage import Storage
from quarterapp.storage.default import DefaultStorage

class TestStorage(unittest.TestCase):
    """
    Test the default storage (SQLite)
    """

    @classmethod
    def setUpClass(cls):
        cls.storage = DefaultStorage(":memory:")
        
    @classmethod
    def tearDownClass(cls):
        cls.storage.close()

    def setUp(self):
        self.user_dale = User("dale@example.com")
        self.user_roger = User("roger@example.com")
        self.default_category = Category("Default")
        self.second_category = Category("Default")

    def tearDown(self):
        self.storage.execute("DELETE FROM timeranges;")
        self.storage.execute("DELETE FROM activities;")
        self.storage.execute("DELETE FROM categories;")
        self.storage.execute("DELETE FROM users;")


    ## User

    def test_can_add_user(self):
        user = User("joe@example.com")

        self.assertTrue(self.storage.save_user(user))
        self.assertEqual(user.username, "joe@example.com")
        self.assertIsNotNone(user.id)

    def test_can_add_multiple_users(self):
        user_joe = User("joe@example.com")
        user_jane = User("jane@example.com")

        self.storage.save_user(user_joe)
        self.storage.save_user(user_jane)

        self.assertIsNotNone(user_joe.id)
        self.assertIsNotNone(user_jane.id)

    def test_username_must_be_unique(self):
        user_joe = User("joe@example.com")
        user_joey = User("joe@example.com")

        self.assertTrue(self.storage.save_user(user_joe))
        self.assertFalse(self.storage.save_user(user_joey))

        self.assertIsNotNone(user_joe.id)
        self.assertEqual(-1, user_joey.id)

    def test_no_users(self):
        self.assertEqual(0, self.storage.user_count())

    def test_counting_many_users(self):
        user_joe = User("joe@example.com")
        user_jane = User("jane@example.com")

        self.storage.save_user(user_joe)
        self.storage.save_user(user_jane)

        self.assertEqual(2, self.storage.user_count())

    def test_can_update_user(self):
        user_joe = User("joe@example.com")
        
        self.storage.save_user(user_joe)
        self.assertEqual("", user_joe.password)

        user_joe.password = "s3cret"
        self.storage.save_user(user_joe)
        self.assertEqual("s3cret", user_joe.password)
        
    def test_can_change_username(self):
        user_joe = User("joe@example.com")
        
        self.storage.save_user(user_joe)
        old_id = user_joe.id

        user_joe.username = "joey@example.com"
        self.storage.save_user(user_joe)

        self.assertEqual(old_id, user_joe.id)
        self.assertEqual("joey@example.com", user_joe.username)
        self.assertEqual(1, self.storage.user_count())

    #def test_cannot_change_to_taken_username(self):
    #    user_joe = User("joe@example.com")
    #    user_jane = User("jane@example.com")
    #
    #    self.storage.save_user(user_joe)
    #    self.storage.save_user(user_jane)
    #
    #    user_joe.username = "jane@example.com"
    #    self.assertFalse(self.storage.save_user(user_joe))
        
    #def test_cannot_update_invalid_user(self):
    #    user_joe = User("joe@example.com")
    #    
    #    self.storage.save_user(user_joe)
    #    self.assertEqual("", user_joe.password)
    #
    #    user_joe.id = 123
    #    user_joe.password = "s3cret"
    #    self.assertFalse(self.storage.save_user(user_joe))

    def test_can_retrieve_user(self):
        user_joe = User("joe@example.com")
        user_jane = User("jane@example.com")

        self.storage.save_user(user_joe)
        self.storage.save_user(user_jane)

        user_joe_2 = self.storage.get_user(user_joe.id)
        self.assertEqual(user_joe.username, user_joe_2.username)
    
    def test_cannot_retrieve_invalid_user(self):
        invalid_user = self.storage.get_user(666)
        self.assertIsNone(invalid_user)
    
    def test_can_retrieve_user_by_username(self):
        user_joe = User("joe@example.com")  
        user_jane = User("jane@example.com")

        self.storage.save_user(user_joe)
        self.storage.save_user(user_jane)

        user_joe_2 = self.storage.get_user(user_joe.id)
        user_joe_3 = self.storage.get_user_by_username("joe@example.com")
        self.assertEqual(user_joe.username, user_joe_2.username)
        self.assertEqual(user_joe_2.username, user_joe_3.username)
    
    def test_can_delete_user(self):
        user_joe = User("joe@example.com")
        user_jane = User("jane@example.com")
        user_bob = User("bob@example.com")

        self.storage.save_user(user_joe)
        self.storage.save_user(user_jane)
        self.storage.save_user(user_bob)
        self.assertEqual(3, self.storage.user_count())

        self.storage.delete_user(user_jane)
        self.assertEqual(2, self.storage.user_count())

        invalid_jane = self.storage.get_user_by_username("jane@example.com")
        self.assertIsNone(invalid_jane)

    def test_can_get_users(self):
        user_joe = User("joe@example.com")
        user_jane = User("jane@example.com")
        user_bob = User("bob@example.com")
        user_alice = User("alice@example.com")
        user_robert = User("robert@example.com")

        self.storage.save_user(user_joe)
        self.storage.save_user(user_jane)
        self.storage.save_user(user_bob)
        self.storage.save_user(user_alice)
        self.storage.save_user(user_robert)

        users = self.storage.get_users(0)
        self.assertEqual(5, len(users))

        users = self.storage.get_users(0, 0)
        self.assertEqual(0, len(users))

        users = self.storage.get_users(0, 2)
        self.assertEqual(2, len(users))

        users = self.storage.get_users(5)
        self.assertEqual(0, len(users))

    def test_can_get_filtered_user_count(self):
        user_joe = User("joe@example.com")
        user_jane = User("jane@example.com")
        user_bob = User("bob@example.net")
        user_alice = User("alice@example.net")
        user_robert = User("robert@example.net")

        self.storage.save_user(user_joe)
        self.storage.save_user(user_jane)
        self.storage.save_user(user_bob)
        self.storage.save_user(user_alice)
        self.storage.save_user(user_robert)

        self.assertEqual(5, self.storage.get_filtered_user_count("@"))
        self.assertEqual(3, self.storage.get_filtered_user_count(".net"))
        self.assertEqual(5, self.storage.get_filtered_user_count("example."))

    def test_can_get_filtered_users(self):
        user_joe = User("joe@example.com")
        user_jane = User("jane@example.com")
        user_bob = User("bob@example.net")
        user_alice = User("alice@example.net")
        user_robert = User("robert@example.net")

        self.storage.save_user(user_joe)
        self.storage.save_user(user_jane)
        self.storage.save_user(user_bob)
        self.storage.save_user(user_alice)
        self.storage.save_user(user_robert)

        self.assertEqual("alice@example.net", self.storage.get_filtered_users("alice")[0].username)
        