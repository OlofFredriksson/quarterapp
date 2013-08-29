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

from quarterapp.domain import BaseError, Category, Activity

class UsernameNotUnique(BaseError):
    pass

class Storage(object):
    """
    Empty implementation of the Storage contract
    """

    ## Settings

    def get_all_settings(self):
        """
        Get all settings from the database
        
        Returns:
            A list of toupes (key / value)
        """
        pass

    def get_setting(self, name):
        """
        Get a specific setting

        Args:
            name: The setting's name

        Returns:
            The setting's value or None if not found
        """
        pass

    def put_setting(self, name, value):
        """
        Set a specific setting to the given value

        Args:
            name: The setting's name
            value: The setting's value

        Returns:
            True on success, else False
        """
        pass

    ## User
    
    def unique_username(self, username):
        """
        Check if the given username is unique

        Args:
            username The username to check

        Returns:
            True if unique else False
        """
        pass

    def save_user(self, user):
        """
        Saves a user object. If this user is a new user it will be added to storage,
        if existing the current user details will be updated with new values.

        The given user object will be updated with a id on first save.

        Note: Do not store password in plain text, hash and salt

        Args:
            user: The user object to save

        Returns:
            True on a successful save, else False
        """
        pass

    def get_user(self, id):
        """
        Gets a fully constructed User object

        Args:
            id: The user id

        Returns:
            A fully constructed User object, or None if no user was found.

        TODO: What about the password?
        """
        pass

    def get_user_by_username(self, username):
        """
        Gets a fully constructed User object

        Args:
            username: The user's username

        Returns:
            A fully constructed User object, or None if no user was found.
        """
        pass

    def delete_user(self, user):
        """
        Delete the given user.

        Calling this method will remove any other data related to this user account
        (e.g. activities and timesheets).

        Args:
            user: The user to delete (of type quarterapp.domain.User)

        Returns:
            True on success else False
        """
        pass

    def user_count(self):
        """
        Get the total numer of users in the application

        Returns:
            The number of users
        """
        pass

    def get_users(self, start = 0, count = 50):
        """
        Get a list of user rows starting at the given position. If the start index
        is out of bounds an empty list will be returned. If there are as many users
        as the given 'count' the list will be filled with as many as there is.

        Args:
            start: The start index
            count: The max number of users to retrieve

        Returns:
            A list of User objects
        """
        pass

    def get_filtered_user_count(self, query_filter):
        """
        Get the total number of users, regardless of their state of type,
        filtered on the username.

        Args:
            query_filter: The filter to match username against

        Returns:
            The number of users matching the query
        """
        pass
    
    def get_filtered_users(self, query_filter, start = 0, count = 50):
        """
        Get a filtered list of user rows starting at the given position. If the start index is out of bounds
        an empty list will be returned. If there are as many users as the given 'count' the list will
        be filled with as many as there is.

        Args:
            query_filter: The filter to match username against
            start: The start index
            count: The max number of users to retrieve

        Returns:
            A list of User objects matching the query
        """
        pass

    def authenticate_user(self, user_id):
        """
        Authenticate that the user is an active and valid user

        Args:
            user_id: The user id
        Returns:
            True if the user is authenticated, else False
        """
        pass

    def authenticate_admin(self, user_id):
        """
        Authenticate that the user is an active and valid administrator

        Args:
            user_id: The user id
        Returns:
            True if the user is authenticated, else False
        """
        pass

    def username_for_reset_code(self, code):
        """
        Get the registered username for the given password reset code

        Args:
            code - The reset code

        Returns:
            The username
        """
        pass

    def set_user_reset_code(self, username, reset_code):
        """
        Set the reset code for a given user.

        Args:
            username - The user to update
            reset_code - The reset code to store

        Returns:
            True on success, else False
        """
        pass

    def reset_password(self, reset_code, new_password):
        """
        Resets a user password for the user account with the given reset_code.

        Args:
            reset_code - The unique reset code
            new_password - The password to set (will not be hashed)

        Returns:
            True on success, else False
        """
        pass

    def signup_user(self, email, code, ip):
        """
        Add the given signup details

        Args:
            email - The new users email
            code - The activation code
            ip - The IP address that requested the sign up

        Returns:
            True on success, else False 
        """
        pass

    def username_for_activation_code(self, code):
        """
        Get the suggested username for the given activation code

        Args:
            code - The activation code

        Returns:
            The username
        """
        pass

    def activate_user(self, code, password, salt):
        """
        Creates a new user if the given email is found in the signup table and the code matches the assigned
        activation code.

        A standard user is created.

        Args:
            db - The database connection to use
            code - The activation code
            password - The users encrypted password
            salt - The user's specific password salt

        Returns:
            True if the user was activated, else False
        """
        pass


    ## Categories
    
    def save_category(self, category, user):
        """
        Saves an activity category. If this is a new category a it will be added to
        the storage, if existing the current will be updated with new values. 

        This method will only save the category, no child activities will be updated!

        The Category passed as argument will be updated with id on first save.
        
        Args:
            category: The category to save
            user: The current user

        Returns:
            True on a successful save, else False
        """
        pass

    def get_category(self, id, user):
        """
        Get the Category object by id. 

        This will only retrieve the category, not any child activities!

        Args:
            id: The category id
            user: The current user

        Returns:
            Either a fully constructed quarterapp.domain.Category instance or None
        """
        pass

    def delete_category(self, category, user):
        """
        Delete the activity category with the given id.

        This will only delete the category, not any child activities!

        Args:
            category: The category to delete
            user: The current user

        Returns:
            True on success, else False
        """
        pass

    def category_count(self, user):
        """
        Get the number of categories for the given user.

        Args:
            user: The current user

        Returns:
            Number of categories
        """
        pass

    def get_categories(self, user):
        """
        Get all the categories for the given user.

        Args:
            user: The current user

        Returns:
            A list of Categories
        """
        pass

    def get_categories_and_activities(self, user):
        """
        Get all the categories and their activities for the given user.

        Args:
            user: The current user

        Returns:
            A list of Categories including a list of activities
        """
        pass

    def get_categories_and_activities_with_usage(self, user):
        """
        Same as get_categories_and_activities, but activities will contain quarter usage.
        
        Only use this when really necessary.
        """

    ## Activities

    def save_activity(self, activity, category, user):
        """
        Saves a single activity. If this is a new activity it will be added to
        the storage, if existing the current will be updated with new values.

        Args:
            activity: The Activity to save
            category: The Category this Activity belongs to 
            user: The current User

        Returns:
            True on success, else False
        """
        pass

    def get_activity(self, id, user):
        """
        Get a previously stored Activity.

        Args:
            id: The ID of the activity to retrieve
            user: The current User

        Returns:
            An instance of Activity or None if not found
        """
        pass

    def activity_count(self, user):
        """
        Get the total number of activities for the current User.

        Args:
            user: The current User

        Returns:
            The total number of activities
        """
        pass

    def activity_count_for_category(self, category, user):
        """
        Get the number of Activities for the given category and user.

        Args:
            category: The category to filter on
            user: The current User

        Returns:
            The total number of activities
        """
        pass

    def delete_activity(self, activity, user):
        """
        Deletes the given Activity.

        Note this will not delete any category!

        Args:
            activity: The activity to delete
            user: The current User
        
        Returns:
            True on success, else False
        """
        pass

    def get_activities(self, user):
        """
        Get all activities for a user.

        Args:
            user: The current User

        Returns:
            A list of activities        
        """
        pass
        
    def get_activities_for_category(self, category, user):
        """
        Get all activities for a given category.

        Args:
            category: The category to retrieve the activities for
            user: The current User

        Returns:
            A list of activities
        """
        pass


    # Time sheet

    def get_timesheet(self, date, user):
        """
        Get a TimeSheet object for the given date. This method will always return a valid
        object, if no quarters are registered an empty TimeSheet will be returned.

        Args:
            date: The time sheets date, must be in the format YYYY-MM-DD (or a datetime object)
            user: The current user

        Returns:
            A TimeSheet object
        """
        pass

    def add_quarters_to_sheet(self, date, quarters, user):
        """
        Adds the given list of quarter objects to the sheet with the given date. Any
        existing quarters with different id will be replaced.

        Args:
            date: The time sheets date, must be in the format YYYY-MM-DD (or a datetime object)
            quarters: A list of quarters to add
            user: The current user
        """
        pass


    # Comments

    def get_comment_for_quarter(self, quarter_id, user):
        """
        Get the the optional comment for a given quarter

        Args:
            quarter_id: The id for the quarter
            user: The current user

        Returns:
            An instance of Comment or None
        """
        pass

    def save_comment(self, quarter_id, comment, user):
        """
        Store the the given comment for a quarter

        Args:
            quarter_id: The quarter id to assign the comment to
            comment: The Comment object to store
            user: The current user
        """
        pass

    def delete_comment(self, quarter_id, user):
        """
        Delete a comment for a quarter

        Args:
            quarter_id: The id for the quarter
            user: The current user
        """
        pass