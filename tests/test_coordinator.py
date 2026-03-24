"""
Tests for coordinator features (dashboard, application review).
"""
import pytest
import json
from tests.conftest import login
import database


def test_coordinator_dashboard_access(client, coordinator_user):
    """Test coordinator can access their dashboard."""
    login(client, 'coordinator1', 'password123')
    response = client.get('/coordinator/dashboard')
    assert response.status_code == 200
    assert b'Coordinator Dashboard' in response.data


def test_coordinator_view_applications(client, coordinator_user, student_user):
    """Test coordinator can view all applications."""
    login(client, 'coordinator1', 'password123')

    # Create some test applications
    database.create_application(
        student_user['id'], 'John Doe', '501234567', 'student1@example.com'
    )

    response = client.get('/coordinator/applications')
    assert response.status_code == 200
    assert b'Review Applications' in response.data
    assert b'501234567' in response.data


def test_approve_application(client, coordinator_user, student_user):
    """Test coordinator can approve an application."""
    login(client, 'coordinator1', 'password123')

    # Create application
    app_id = database.create_application(
        student_user['id'], 'John Doe', '501234567', 'student1@example.com'
    )

    # Approve it
    response = client.post('/api/coordinator/review-application',
                          json={
                              'application_id': app_id,
                              'status': 'accepted'
                          })

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True

    # Verify in database
    app = database.get_application_by_user_id(student_user['id'])
    assert app['status'] == 'accepted'
    assert app['reviewed_by'] == coordinator_user['id']


def test_reject_application(client, coordinator_user, student_user):
    """Test coordinator can reject an application."""
    login(client, 'coordinator1', 'password123')

    # Create application
    app_id = database.create_application(
        student_user['id'], 'John Doe', '501234567', 'student1@example.com'
    )

    # Reject it
    response = client.post('/api/coordinator/review-application',
                          json={
                              'application_id': app_id,
                              'status': 'rejected'
                          })

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True

    # Verify in database
    app = database.get_application_by_user_id(student_user['id'])
    assert app['status'] == 'rejected'


def test_student_cannot_access_coordinator_routes(client, student_user):
    """Test student cannot access coordinator routes."""
    login(client, 'student1', 'password123')

    response = client.get('/coordinator/dashboard', follow_redirects=True)
    assert response.status_code == 200
    # Should be redirected or see error
    assert b'permission' in response.data.lower() or b'Student Dashboard' in response.data
