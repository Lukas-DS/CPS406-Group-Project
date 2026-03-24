"""
Tests for authentication functionality (registration, login, logout).
"""
import pytest
from tests.conftest import login, logout
import database


def test_register_student_valid(client, clean_db):
    """Test valid student registration."""
    response = client.post('/register', data={
        'username': 'newstudent',
        'email': 'newstudent@example.com',
        'full_name': 'New Student',
        'role': 'student',
        'student_id': '502345678',
        'password': 'password123',
        'password_confirm': 'password123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Registration successful' in response.data

    # Verify user was created in database
    user = database.get_user_by_username('newstudent')
    assert user is not None
    assert user['email'] == 'newstudent@example.com'
    assert user['role'] == 'student'


def test_register_coordinator_valid(client, clean_db):
    """Test valid coordinator registration."""
    response = client.post('/register', data={
        'username': 'newcoord',
        'email': 'coordinator@example.com',
        'full_name': 'New Coordinator',
        'role': 'coordinator',
        'password': 'password123',
        'password_confirm': 'password123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Registration successful' in response.data

    user = database.get_user_by_username('newcoord')
    assert user is not None
    assert user['role'] == 'coordinator'
    assert user['student_id'] is None


def test_register_duplicate_username(client, student_user):
    """Test registration with duplicate username."""
    response = client.post('/register', data={
        'username': 'student1',  # Already exists
        'email': 'different@example.com',
        'full_name': 'Different Name',
        'role': 'student',
        'student_id': '509999999',
        'password': 'password123',
        'password_confirm': 'password123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'already exists' in response.data


def test_register_duplicate_email(client, student_user):
    """Test registration with duplicate email."""
    response = client.post('/register', data={
        'username': 'differentuser',
        'email': 'student1@example.com',  # Already exists
        'full_name': 'Different Name',
        'role': 'student',
        'student_id': '509999999',
        'password': 'password123',
        'password_confirm': 'password123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'already registered' in response.data


def test_register_password_mismatch(client, clean_db):
    """Test registration with non-matching passwords."""
    response = client.post('/register', data={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'full_name': 'New User',
        'role': 'student',
        'student_id': '509999999',
        'password': 'password123',
        'password_confirm': 'differentpassword'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'do not match' in response.data


def test_register_invalid_student_id(client, clean_db):
    """Test registration with invalid student ID format."""
    response = client.post('/register', data={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'full_name': 'New User',
        'role': 'student',
        'student_id': '12345',  # Too short
        'password': 'password123',
        'password_confirm': 'password123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'9 digits' in response.data


def test_login_valid(client, student_user):
    """Test successful login."""
    response = login(client, 'student1', 'password123')
    assert response.status_code == 200
    assert b'Welcome back' in response.data


def test_login_invalid_username(client, clean_db):
    """Test login with non-existent username."""
    response = client.post('/login', data={
        'username': 'nonexistent',
        'password': 'password123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Invalid username or password' in response.data


def test_login_invalid_password(client, student_user):
    """Test login with incorrect password."""
    response = client.post('/login', data={
        'username': 'student1',
        'password': 'wrongpassword'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Invalid username or password' in response.data


def test_logout(client, student_user):
    """Test logout functionality."""
    login(client, 'student1', 'password123')
    response = logout(client)

    assert response.status_code == 200
    assert b'logged out' in response.data


def test_access_protected_route_without_login(client):
    """Test accessing protected route without authentication."""
    response = client.get('/student/dashboard', follow_redirects=True)
    assert response.status_code == 200
    assert b'log in' in response.data.lower()


def test_role_based_access_control(client, student_user):
    """Test that student cannot access coordinator routes."""
    login(client, 'student1', 'password123')
    response = client.get('/coordinator/dashboard', follow_redirects=True)

    # Should be redirected or see permission message
    assert response.status_code == 200
    assert b'permission' in response.data.lower() or b'Log in' in response.data
