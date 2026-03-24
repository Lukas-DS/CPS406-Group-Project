"""
Tests for student features (applications, reports).
"""
import pytest
import json
from tests.conftest import login
import database


def test_student_dashboard_access(client, student_user):
    """Test student can access their dashboard."""
    login(client, 'student1', 'password123')
    response = client.get('/student/dashboard')
    assert response.status_code == 200
    assert b'Student Dashboard' in response.data


def test_submit_application_valid(client, student_user):
    """Test successful application submission."""
    login(client, 'student1', 'password123')

    response = client.post('/api/student/submit-application',
                          json={
                              'full_name': 'John Doe',
                              'student_id': '501234567',
                              'email': 'student1@example.com'
                          })

    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'successfully' in data['message'].lower()

    # Verify in database
    app = database.get_application_by_user_id(student_user['id'])
    assert app is not None
    assert app['student_id'] == '501234567'
    assert app['status'] == 'pending'


def test_submit_application_duplicate(client, student_user):
    """Test duplicate application prevention."""
    login(client, 'student1', 'password123')

    # First submission
    client.post('/api/student/submit-application',
               json={
                   'full_name': 'John Doe',
                   'student_id': '501234567',
                   'email': 'student1@example.com'
               })

    # Second submission (should fail because student ID already exists)
    response = client.post('/api/student/submit-application',
                          json={
                              'full_name': 'John Doe',
                              'student_id': '501234567',
                              'email': 'student1@example.com'
                          })

    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'already exists' in data['error'].lower()


def test_submit_application_invalid_email(client, student_user):
    """Test application submission with invalid email."""
    login(client, 'student1', 'password123')

    response = client.post('/api/student/submit-application',
                          json={
                              'full_name': 'John Doe',
                              'student_id': '501234567',
                              'email': 'invalid-email'
                          })

    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'email' in data['error'].lower()


def test_submit_application_invalid_student_id(client, student_user):
    """Test application submission with invalid student ID."""
    login(client, 'student1', 'password123')

    response = client.post('/api/student/submit-application',
                          json={
                              'full_name': 'John Doe',
                              'student_id': '12345',  # Too short
                              'email': 'student1@example.com'
                          })

    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['success'] is False
    assert '9 digits' in data['error'].lower()


def test_submit_report_valid(client, student_user):
    """Test successful report submission."""
    login(client, 'student1', 'password123')

    # First, create and accept an application
    database.create_application(
        student_user['id'], 'John Doe', '501234567', 'student1@example.com'
    )
    app = database.get_application_by_user_id(student_user['id'])
    database.update_application_status(app['id'], 'accepted', 1)

    # Now submit report
    response = client.post('/api/student/submit-report',
                          json={
                              'report_title': 'Week 1 Report',
                              'work_description': 'Completed initial training and setup tasks',
                              'hours_worked': 40,
                              'supervisor_name': 'Jane Manager',
                              'supervisor_email': 'jane@company.com'
                          })

    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['success'] is True

    # Verify in database
    reports = database.get_reports_by_user(student_user['id'])
    assert len(reports) == 1
    assert reports[0]['report_title'] == 'Week 1 Report'


def test_submit_report_without_accepted_application(client, student_user):
    """Test report submission without accepted application."""
    login(client, 'student1', 'password123')

    response = client.post('/api/student/submit-report',
                          json={
                              'report_title': 'Week 1 Report',
                              'work_description': 'Completed tasks',
                              'hours_worked': 40,
                              'supervisor_name': 'Jane Manager',
                              'supervisor_email': 'jane@company.com'
                          })

    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['success'] is False


def test_submit_report_with_pending_application(client, student_user):
    """Test report submission with pending (not accepted) application."""
    login(client, 'student1', 'password123')

    # Create pending application
    database.create_application(
        student_user['id'], 'John Doe', '501234567', 'student1@example.com'
    )

    # Try to submit report (should fail)
    response = client.post('/api/student/submit-report',
                          json={
                              'report_title': 'Week 1 Report',
                              'work_description': 'Completed tasks',
                              'hours_worked': 40,
                              'supervisor_name': 'Jane Manager',
                              'supervisor_email': 'jane@company.com'
                          })

    assert response.status_code == 403
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'accepted' in data['error'].lower()


def test_submit_report_invalid_data(client, student_user):
    """Test report submission with invalid data."""
    login(client, 'student1', 'password123')

    # Create accepted application
    database.create_application(
        student_user['id'], 'John Doe', '501234567', 'student1@example.com'
    )
    app = database.get_application_by_user_id(student_user['id'])
    database.update_application_status(app['id'], 'accepted', 1)

    # Submit with invalid hours
    response = client.post('/api/student/submit-report',
                          json={
                              'report_title': 'Week 1 Report',
                              'work_description': 'Completed tasks',
                              'hours_worked': -5,  # Invalid
                              'supervisor_name': 'Jane Manager',
                              'supervisor_email': 'jane@company.com'
                          })

    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['success'] is False
