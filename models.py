"""
User model for Flask-Login integration.
"""
from flask_login import UserMixin
import database


class User(UserMixin):
    """
    User class implementing Flask-Login's UserMixin.
    Provides required methods for Flask-Login authentication.
    """

    def __init__(self, user_id, username, email, role, full_name, student_id=None):
        """
        Initialize a User object.

        Args:
            user_id: Database user ID
            username: Username for login
            email: User email address
            role: User role ('student', 'coordinator', or 'employer')
            full_name: User's full name
            student_id: Student ID (only for students)
        """
        self.id = user_id
        self.username = username
        self.email = email
        self.role = role
        self.full_name = full_name
        self.student_id = student_id

    def get_id(self):
        """
        Return the user ID as a string (required by Flask-Login).
        """
        return str(self.id)

    @property
    def is_authenticated(self):
        """
        Return True if the user is authenticated (required by Flask-Login).
        """
        return True

    @property
    def is_active(self):
        """
        Return True if the user account is active (required by Flask-Login).
        """
        return True

    @property
    def is_anonymous(self):
        """
        Return False as this is not an anonymous user (required by Flask-Login).
        """
        return False

    # Helper methods for role checking
    def is_student(self):
        """Check if user is a student."""
        return self.role == 'student'

    def is_coordinator(self):
        """Check if user is a coordinator."""
        return self.role == 'coordinator'

    def is_employer(self):
        """Check if user is an employer."""
        return self.role == 'employer'

    @staticmethod
    def get(user_id):
        """
        Load a user from the database by ID (for Flask-Login user_loader).

        Args:
            user_id: The user ID to load

        Returns:
            User: User object if found, None otherwise
        """
        user_row = database.get_user_by_id(int(user_id))
        if user_row:
            return User(
                user_id=user_row['id'],
                username=user_row['username'],
                email=user_row['email'],
                role=user_row['role'],
                full_name=user_row['full_name'],
                student_id=user_row['student_id']
            )
        return None

    def __repr__(self):
        """String representation of the User object."""
        return f"<User {self.username} ({self.role})>"
