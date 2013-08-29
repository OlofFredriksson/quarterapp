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
import sys
import sqlite3
import logging

from exceptions import NotImplementedError
from ..domain import User, Color, TimeSheet, Quarter, Comment, UserState, UserType
from storage import *

initializing_sql = """
    PRAGMA foreign_keys = ON;

    CREATE TABLE `users` (
        `id` INTEGER PRIMARY KEY AUTOINCREMENT,
        `username` VARCHAR(256) NOT NULL DEFAULT '',
        `password` VARCHAR(90) NOT NULL DEFAULT '',
        `salt` VARCHAR(256) NOT NULL DEFAULT '',
        `type` TINYINT NOT NULL DEFAULT '0',
        `state`  TINYINT NOT NULL DEFAULT '0',
        `last_login` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        `reset_code` VARCHAR(64),
        UNIQUE(`username`)
        );

    CREATE TABLE `signups` (
        `id` INTEGER PRIMARY KEY AUTOINCREMENT,
        `username` VARCHAR(256) NOT NULL DEFAULT '',
        `activation_code` VARCHAR(64) NOT NULL DEFAULT '',
        `ip` VARCHAR(39) NOT NULL DEFAULT '',
        `signup_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(`username`)
        );

    CREATE TABLE `settings` (
        `id` INTEGER PRIMARY KEY AUTOINCREMENT,
        `name` TEXT NOT NULL,
        `value` TEXT NOT NULL,
        UNIQUE(`name`)
        );

    CREATE TABLE `categories` (
        `id` INTEGER PRIMARY KEY AUTOINCREMENT,
        `user` INTEGER NOT NULL,
        `title` TEXT NOT NULL DEFAULT '',
        FOREIGN KEY(user) REFERENCES users(id) ON DELETE CASCADE
        );

    CREATE TABLE `activities` (
        `id` INTEGER PRIMARY KEY AUTOINCREMENT,
        `category` INTEGER NOT NULL,
        `user` INTEGER NOT NULL,
        `title` TEXT NOT NULL DEFAULT '',
        `color` VARCHAR(32) NOT NULL DEFAULT '',
        `state` TINYINT(1) NOT NULL DEFAULT '0',
        `meta` TEXT NOT NULL DEFAULT '',
        FOREIGN KEY(user) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(category) REFERENCES categories(id) ON DELETE CASCADE
        );

    CREATE TABLE `quarters` (
        `id` INTEGER PRIMARY KEY AUTOINCREMENT,
        `user` INTEGER NOT NULL,
        `date` DATE NOT NULL,
        `offset` INTEGER NOT NULL,
        `activity` INTEGER NOT NULL,
        `comment` INTEGER NOT NULL DEFAULT '0',
        FOREIGN KEY(user) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(activity) REFERENCES activities(id) ON DELETE CASCADE
        );

    CREATE TABLE `comments` (
        `id` INTEGER PRIMARY KEY AUTOINCREMENT,
        `user` INTEGER NOT NULL,
        `comment` TEXT NOT NULL,
        FOREIGN KEY(user) REFERENCES users(id) ON DELETE CASCADE
        );

    /* Insert default settings */
    INSERT INTO settings (`name`, `value`) VALUES("allow-signups", "1");
    INSERT INTO settings (`name`, `value`) VALUES("allow-activations", "1");

    /*
        Insert default administrator account
        Username: one@example.com
        Password: 123qweASD
    */
    INSERT INTO users (`username`, `password`, `salt`, `type`, `state`) VALUES("one@example.com", "MYlkZO_QWaMjtCTJd76FJg--87ixaKBIoq7iKxjrOlLf358FqGuny4jbVUn5PeGmQoci4MOc_e5sBuLL2QN4UA==", "one@example.com", 1, 1);
"""

class Data(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

class DefaultStorage(Storage):
    """
    The default storage for quarterapp is a SQLite database.
    """

    def __init__(self, file_name):
        """
        Construct the default storage and initialize the SQLite database

        @param file_name The path and file name for the database file
        """
        
        # If the database file does not exist, create tables as well
        existing_db = os.path.isfile(file_name)
        self.conn = sqlite3.connect(file_name)
        
        if not existing_db:
            self.execute_sql(initializing_sql)

    def execute_sql(self, sql):
        """
        Executes a string containing SQL with multiple statements.

        @param sql The SQL to execute as string
        """
        for stmt in sql.split(';'):
            try:
                cur = self.conn.cursor()
                cur.execute(stmt)
                self.conn.commit()
            except:
                self.conn.rollback()
                logging.error("Could not execute SQL statement %s", stmt)
                raise

    def execute(self, query, *params):
        """
        Executes a SQL query and return the row id for the affected row.

        @param query The SQL to execute
        @param params Any parameters needed to execute the query
        @return The row id for the affected row
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            return cursor.lastrowid
        except:
            logging.error("Could not execute SQL: %s", sys.exc_info())
            self.conn.rollback()
        return -1

    def query(self, query, *params):
        """
        Execute a SQL query and return an array of dict's representing each row
        and where dict keys are the column names.

        @param query The SQL to execute
        @param params Any parameters needed to execute the query
        @return An array with the result set
        """
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        cols = [c[0] for c in cursor.description]
        return [Data(zip(cols, row)) for row in cursor.fetchall()]

    def query_rowcount(self, sql, *params):
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        return cursor.rowcount

    def close(self):
        """
        Close connection to database
        """
        self.conn.close()

    ## Implementation of storage contract

    def get_all_settings(self):
        return self.query("SELECT * FROM settings;")

    def get_setting(self, name):
        result = sel.query("SELECT value FROM settings WHERE name=?;", name)
        if len(result) > 0:
            return getattr(result[0], "value")
        return None

    def put_setting(self, name, value):
        return self.execute("UPDATE settings SET value=? WHERE name=? ;", value, name) == 1

    def unique_username(self, username):
        users = self.query("SELECT username FROM users WHERE username=?;", username)
        return len(users) < 1

    def save_user(self, user):
        try:
            if user.id == -1:
                user.id = self.execute("INSERT INTO users (username, password, salt, type, state) VALUES (?,?,?,?,?);", 
                    user.username, user.password, user.username, str(user.type), str(user.state))
                return user.id != -1
            else:
                self.execute("UPDATE users SET password=?, type=?, state=? WHERE id=?;", user.password, str(user.type), str(user.state), user.id)
        except:
            logging.error("Could not save user")
            return False
        return True

    def get_user(self, id):
        users = self.query("SELECT * FROM users WHERE id=?", id)
        if len(users) == 1:
            return User(users[0].username, users[0].id, users[0].password, users[0].type, users[0].state, users[0].last_login)
        return None

    def get_user_by_username(self, username):
        users = self.query("SELECT * FROM users WHERE username=?;", username)
        if len(users) == 1:
            return User(users[0].username, users[0].id, users[0].password, users[0].type, users[0].state, users[0].last_login)
        return None

    def delete_user(self, user):
        removed_id = self.execute("DELETE FROM comments WHERE user=?;", user.id)
        removed_id = self.execute("DELETE FROM quarters WHERE user=?;", user.id)
        removed_id = self.execute("DELETE FROM activities WHERE user=?;", user.id)
        removed_id = self.execute("DELETE FROM categories WHERE user=?;", user.id)
        removed_id = self.execute("DELETE FROM users WHERE id=?;", user.id)
        return removed_id == user.id

    def user_count(self):
        users = self.query("SELECT COUNT(*) FROM users;")
        if len(users) > 0:
            return getattr(users[0], "COUNT(*)")
        else:
            return 0

    def get_users(self, start = 0, count = 50):
        users = []
        result = self.query("SELECT * FROM users ORDER BY id LIMIT ?, ?;", start, count)
        for row in result:
            users.append(User(row.username, row.id, row.password, row.type, row.state, row.last_login))
        return users

    def get_filtered_user_count(self, query_filter):
        filter = "%{0}%".format(query_filter)
        users = self.query("SELECT COUNT(*) FROM users WHERE username LIKE ?;", filter)
        if len(users) > 0:
            return getattr(users[0], "COUNT(*)")
        else:
            return 0

    def get_filtered_users(self, query_filter, start = 0, count = 50):
        users = []
        filter = "%{0}%".format(query_filter)
        result = self.query("SELECT * FROM users WHERE username LIKE ? ORDER BY id LIMIT ?, ?;", filter, start, count)
        for row in result:
            users.append(User(row.username, row.id, row.password, row.type, row.state))
        return users

    def authenticate_user(self, user_id):
        users = self.query("SELECT state FROM users WHERE id=?", user_id)
        if len(users) == 1:
            return users[0].state == UserState.Active
        return False
        
    def authenticate_admin(self, user_id):
        users = self.query("SELECT state, type FROM users WHERE id=?", user_id)
        if len(users) == 1:
            return users[0].state == UserState.Active and users[0].type == UserType.Administrator
        return False

    def username_for_reset_code(self, code):
        users = self.query("SELECT username FROM users WHERE reset_code=?;", code)

        if len(users) > 0:
            return users[0].username
        return None

    def set_user_reset_code(self, username, reset_code):
        try:
            self.execute("UPDATE users SET reset_code=? WHERE username=?;", reset_code, username)
            return True
        except:
            return False

    def reset_password(self, reset_code, new_password):
        try:
            users = self.query("SELECT username FROM users WHERE reset_code=?;", reset_code)
            if len(users) == 1:
                self.execute("UPDATE users SET password=? WHERE reset_code=?;", new_password, reset_code)
                self.execute("UPDATE users SET reset_code='' WHERE reset_code=?;", reset_code)
                return True
            else:
                return False
        except:
            return False

    def signup_user(self, email, code, ip):
        result = self.query_rowcount("UPDATE signups SET activation_code=? WHERE username=?;", code, email)
        if result == 0:
            result = self.execute("INSERT INTO signups (username, activation_code, ip) VALUES(?, ?, ?);", email, code, ip)
        return result

    def username_for_activation_code(self, code):
        signups = self.query("SELECT username FROM signups WHERE activation_code=?;", code)
        if len(signups) > 0:
            return signups[0].username
        return None

    def activate_user(self, code, password, salt):
        try:
            signups = self.query("SELECT username, activation_code FROM signups WHERE activation_code=?;", code)
            if signups[0].activation_code == code:
                logging.info("Activating user")
                self.execute("DELETE FROM signups WHERE activation_code=?;", code)
                self.execute("INSERT INTO users (username, password, salt, type, state) VALUES(?, ?, ?, ?, ?);",
                    signups[0].username, password, salt, UserType.Normal, UserState.Active)
                return True
        except Exception, e:
            logging.error("Could not activate user")
            logging.exception(e)
            return False


    ## Categories

    def save_category(self, category, user):
        try:
            if category.id == -1:
                category.id = self.execute("INSERT INTO categories (title, user) VALUES (?, ?);", category.title, user.id)
            else:
                self.execute("UPDATE categories SET title=? WHERE id=? AND user=?;", category.title, category.id, user.id)
        except:
            logging.error("Could not save category")
            return False
        return True

    def get_category(self, id, user):
        categories = self.query("SELECT * FROM categories WHERE id=? AND user=?;", id, user.id)
        if len(categories) == 1:
            return Category(categories[0].title, id = categories[0].id, empty = self.is_category_empty(user, id))
        return None

    def delete_category(self, category, user):
        self.execute("DELETE FROM categories WHERE id=? AND user=?;", category.id, user.id)
        return True
        
    def category_count(self, user):
        categories = self.query("SELECT COUNT(*) FROM categories WHERE user=?;", user.id)
        if len(categories) > 0:
            return getattr(categories[0], "COUNT(*)")
        else:
            return 0

    def get_categories(self, user):
        categories = []
        result = self.query("SELECT * FROM categories WHERE user=?;", user.id)
        for row in result:
            categories.append(Category(row.title, id = row.id, empty = self.is_category_empty(user, row.id)))
        return categories

    def get_categories_and_activities(self, user):
        categories = self.get_categories(user)
        for cat in categories:
            activities = self.get_activities_for_category(cat, user)
            setattr(cat, 'activities', activities)
        return categories

    def get_categories_and_activities_with_usage(self, user):
        categories = self.get_categories(user)
        for cat in categories:
            activities = self.get_activities_for_category(cat, user)
            setattr(cat, 'activities', activities)
            for act in activities:
                act.usage = self._quarter_count(act.id, user)

        return categories

    def is_category_empty(self, user, category_id):
        activities = self.query("SELECT COUNT(*) FROM activities WHERE category=?;", category_id)
        if len(activities) >0:
            return getattr(activities[0], "COUNT(*)") == 0
        else:
            return True


    ## Activities

    def save_activity(self, activity, category, user):
        try:
            if activity.id == -1:
                activity.id = self.execute("INSERT INTO activities (color, title, state, meta, category, user) VALUES (?, ?, ?, ?, ?, ?);",
                    activity.color.hex(), activity.title, str(activity.state), activity.meta, category.id, user.id)
            else:
                rowid = self.execute("UPDATE activities SET color=?, title=?, state=?, meta=?, category=? WHERE id=? AND user=?;", 
                    activity.color.hex(), activity.title, str(activity.state), activity.meta, category.id, activity.id, user.id)
        except:
            logging.error("Could not save activity: %s", sys.exc_info())
            return False
        return True

    def get_activity(self, id, user):
        activities = self.query("SELECT * FROM activities WHERE id=? AND user=?;", id, user.id)
        if len(activities) == 1:
            return Activity(id = activities[0].id, color = Color(activities[0].color), title = activities[0].title,
                state =activities[0].state, meta = activities[0].meta, category_id = activities[0].category)
        return None

    def activity_count(self, user):
        activities = self.query("SELECT COUNT(*) FROM activities WHERE user=?;", user.id)
        if len(activities) > 0:
            return getattr(activities[0], "COUNT(*)")
        else:
            return 0

    def activity_count_for_category(self, category, user):
        activities = self.query("SELECT COUNT(*) FROM activities WHERE user=? AND category=?;", user.id, category.id)
        if len(activities) > 0:
            return getattr(activities[0], "COUNT(*)")
        else:
            return 0

    def delete_activity(self, activity, user):
        self.execute("DELETE FROM activities WHERE id=? AND user=?;", activity.id, user.id)
        return True

    def get_activities(self, user):
        activities = []
        result = self.query("SELECT * FROM activities WHERE user=?;", user.id)
        for row in result:
            activities.append(Activity(id = row.id, color = Color(row.color),
                title = row.title, state = row.state, meta = row.meta, category_id = row.category))
        return activities

    def get_activities_for_category(self, category, user):
        activities = []
        result = self.query("SELECT * FROM activities WHERE category=? AND user=?;", category.id, user.id)
        for row in result:
            activities.append(Activity(id = row.id, color = Color(row.color),
                title = row.title, state = row.state, meta = row.meta, category_id = row.category))
        return activities


    ## Time sheet

    def _quarter_count(self, activity_id, user):
        quarters = self.query("SELECT COUNT(*) FROM quarters WHERE activity=? AND user=?;", activity_id, user.id)
        if len(quarters) > 0:
            return getattr(quarters[0], "COUNT(*)")
        else:
            return 0

    def _add_quarter(self, date, quarter, user):
        try:
            if quarter.id == -1:
                quarter.id = self.execute("INSERT INTO quarters (offset, activity, date, user) VALUES (?, ?, ?, ?);",
                    quarter.offset, quarter.activity_id, date, user.id)
            else:
                self.execute("UPDATE quarters SET activity=? WHERE id=? AND user=?;",
                    quarter.activity_id, quarter.id, user.id)
        except Exception, e:
            logging.error("Could not save quarter")
            logging.exception(e)
            return False
        return True

    def _get_quarter(self, date, offset, user):
        quarter = None
        result = self.query("SELECT * FROM quarters WHERE date=? AND offset=? AND user=?;", date, offset, user.id)
        if len(result) > 0:
            row = result[0]
            quarter = Quarter(id = row.id, offset = row.offset, activity_id = row.activity, comment_id = row.comment)
        return quarter

    def _get_quarter_from_id(self, id, user):
        quarter = None
        result = self.query("SELECT * FROM quarters WHERE id=? AND user=?;", id, user.id)
        if len(result) == 1:
            row = result[0]
            quarter = Quarter(id = row.id, offset = row.offset, activity_id = row.activity, comment_id = row.comment)
        return quarter

    def _delete_quarter_by_offset(self, date, offset, user):
        self.execute("DELETE FROM quarters WHERE date=? AND offset=? AND user=?;", date, offset, user.id)

    def get_timesheet(self, date, user):
        sheet = TimeSheet(date = date)
        result = self.query("SELECT * FROM quarters WHERE date=? AND user=?;", date, user.id)
        for row in result:
            sheet.quarters.append(Quarter(id = row.id, offset = row.offset, activity_id = row.activity, comment_id = row.comment))
        sheet.summarize()
        return sheet

    def add_quarters_to_sheet(self, date, quarters, user):
        for quarter in quarters:
            existing_quarter = self._get_quarter(date, quarter.offset, user)
            
            if existing_quarter == None and quarter.activity_id != -1:
                self._add_quarter(date, quarter, user)
            elif quarter.activity_id == -1:
                self._delete_quarter_by_offset(date, quarter.offset, user)
            elif existing_quarter.activity_id != quarter.activity_id:
                self._delete_quarter_by_offset(date, quarter.offset, user)
                self._add_quarter(date, quarter, user)
            elif existing_quarter.offset != quarter.offset:
                self._add_quarter(date, quarter, user)


    # Comments

    def get_comment_for_quarter(self, quarter_id, user):
        try:
            quarter = self._get_quarter_from_id(quarter_id, user)
            comments = self.query("SELECT * FROM comments WHERE id=? AND user=?;", quarter.comment_id, user.id)
            if len(comments) == 1:
                return Comment(id = comments[0].id, comment = comments[0].comment)
        except Exception, e:
            logging.error("Could not retrieve comment")
            logging.exception(e)
        return None

    def save_comment(self, quarter_id, comment, user):
        try:
            quarter = self._get_quarter_from_id(quarter_id, user)
            if quarter.comment_id == 0:
                comment.id = self.execute("INSERT INTO comments (comment, user) VALUES (?, ?);", comment.comment, user.id)
                self.execute("UPDATE quarters SET comment=? WHERE id=? AND user=?;", comment.id, quarter_id, user.id)
            else:
                self.execute("UPDATE comments SET comment=? WHERE id=? AND user=?;", comment.comment, quarter.comment_id, user.id)
        except Exception, e:
            logging.error("Could not save comment")
            logging.exception(e)
            return False
        return True

    def delete_comment(self, quarter_id, user):
        quarter = self._get_quarter_from_id(quarter_id, user)
        self.execute("DELETE FROM comments WHERE id=? AND user=?;", quarter.comment_id, user.id)

