"""
Tests for employer features (student evaluation).
"""
import pytest
import json
from tests.conftest import login
import database


def test_employer_dashboard_access(client, employer_user):
    """Test employer can access their dashboard."""
    login(client, 'employer1', 'password123')
    response = client.get('/employer/dashboard')
    assert response.status_code == 200
    assert b'Employer Dashboard' in response.data


def test_employer_view_students(client, employer_user, student_user):
    """Test employer can view list of students."""
    login(client, 'employer1', 'password123')

    # Create and accept application for student
    app_id = database.create_application(
        student_user['id'], 'John Doe', '501234567', 'student1@example.com'
    )
    database.update_application_status(app_id, 'accepted', 1)

    response = client.get('/employer/students')
    assert response.status_code == 200
    assert b'John Doe' in response.data or b'501234567' in response.data


def test_submit_evaluation_valid(client, employer_user, student_user):
    """Test successful evaluation submission."""
    login(client, 'employer1', 'password123')

    # Create and accept application
    app_id = database.create_application(
        student_user['id'], 'John Doe', '501234567', 'student1@example.com'
    )
    database.update_application_status(app_id, 'accepted', 1)

    # Submit evaluation
    response = client.post('/api/employer/submit-evaluation',
                          json={
                              'student_user_id': student_user['id'],
                              'application_id': app_id,
                              'technical_skills': 4,
                              'communication': 5,
                              'professionalism': 4,
                              'overall_rating': 4,
                              'comments': 'Great work!'
                          })

    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['success'] is True

    # Verify in database
    evals = database.get_evaluations_for_student(student_user['id'])
    assert len(evals) == 1
    assert evals[0]['overall_rating'] == 4


def test_submit_evaluation_invalid_ratings(client, employer_user, student_user):
    """Test evaluation submission with invalid ratings."""
    login(client, 'employer1', 'password123')

    # Create and accept application
    app_id = database.create_application(
        student_user['id'], 'John Doe', '501234567', 'student1@example.com'
    )
    database.update_application_status(app_id, 'accepted', 1)

    # Submit with invalid rating
    response = client.post('/api/employer/submit-evaluation',
                          json={
                              'student_user_id': student_user['id'],
                              'application_id': app_id,
                              'technical_skills': 6,  # Invalid (>5)
                              'communication': 5,
                              'professionalism': 4,
                              'overall_rating': 4,
                              'comments': 'Great work!'
                          })

    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['success'] is False


def test_student_cannot_access_employer_routes(client, student_user):
    """Test student cannot access employer routes."""
    login(client, 'student1', 'password123')

    response = client.get('/employer/dashboard', follow_redirects=True)
    assert response.status_code == 200
    # Should be redirected or see error
    assert b'permission' in response.data.lower() or b'Student Dashboard' in response.data
