"""
Shared pytest fixtures for the Co-op Support Application tests.
"""
import pytest
import os
from werkzeug.security import generate_password_hash

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app as flask_app
import database


@pytest.fixture
def app():
    """Create and configure a test Flask application."""
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    flask_app.config['SECRET_KEY'] = 'test-secret-key'

    # Use a test database
    original_db_path = database.config.DATABASE_PATH
    database.config.DATABASE_PATH = 'instance/test_coop_app.db'

    # Initialize test database
    with flask_app.app_context():
        database.init_db()

    yield flask_app

    # Cleanup: remove test database
    database.config.DATABASE_PATH = original_db_path
    if os.path.exists('instance/test_coop_app.db'):
        os.remove('instance/test_coop_app.db')


@pytest.fixture
def client(app):
    """Create a test client for making requests."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def clean_db(app):
    """Reset database before each test."""
    with app.app_context():
        database.init_db()
    yield


@pytest.fixture
def student_user(app, clean_db):
    """Create a test student user."""
    password_hash = generate_password_hash('password123')
    user_id = database.create_user(
        username='student1',
        email='student1@example.com',
        password_hash=password_hash,
        role='student',
        full_name='John Doe',
        student_id='501234567'
    )
    return {
        'id': user_id,
        'username': 'student1',
        'password': 'password123',
        'email': 'student1@example.com',
        'student_id': '501234567',
        'full_name': 'John Doe'
    }


@pytest.fixture
def coordinator_user(app, clean_db):
    """Create a test coordinator user."""
    password_hash = generate_password_hash('password123')
    user_id = database.create_user(
        username='coordinator1',
        email='coordinator@example.com',
        password_hash=password_hash,
        role='coordinator',
        full_name='Jane Smith',
        student_id=None
    )
    return {
        'id': user_id,
        'username': 'coordinator1',
        'password': 'password123',
        'email': 'coordinator@example.com',
        'full_name': 'Jane Smith'
    }


@pytest.fixture
def employer_user(app, clean_db):
    """Create a test employer user."""
    password_hash = generate_password_hash('password123')
    user_id = database.create_user(
        username='employer1',
        email='employer@example.com',
        password_hash=password_hash,
        role='employer',
        full_name='ABC Company',
        student_id=None
    )
    return {
        'id': user_id,
        'username': 'employer1',
        'password': 'password123',
        'email': 'employer@example.com',
        'full_name': 'ABC Company'
    }


def login(client, username, password):
    """Helper function to log in a user."""
    return client.post('/login', data={
        'username': username,
        'password': password
    }, follow_redirects=True)


def logout(client):
    """Helper function to log out."""
    return client.get('/logout', follow_redirects=True)
