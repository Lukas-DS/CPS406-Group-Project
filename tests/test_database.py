"""
Tests for database operations.
"""
import pytest
from werkzeug.security import generate_password_hash, check_password_hash
import database


def test_database_initialization(app):
    """Test database tables are created correctly."""
    with app.app_context():
        database.init_db()

    # Verify database file exists
    import os
    assert os.path.exists('instance/test_coop_app.db')


def test_create_user(app, clean_db):
    """Test user creation."""
    password_hash = generate_password_hash('password123')
    user_id = database.create_user(
        username='testuser',
        email='test@example.com',
        password_hash=password_hash,
        role='student',
        full_name='Test User',
        student_id='509876543'
    )

    assert user_id > 0

    # Retrieve and verify
    user = database.get_user_by_id(user_id)
    assert user['username'] == 'testuser'
    assert user['email'] == 'test@example.com'
    assert user['role'] == 'student'
    assert user['student_id'] == '509876543'
    assert check_password_hash(user['password_hash'], 'password123')


def test_duplicate_username_fails(app, clean_db):
    """Test that duplicate usernames are prevented."""
    password_hash = generate_password_hash('password123')

    database.create_user(
        username='testuser',
        email='test1@example.com',
        password_hash=password_hash,
        role='student',
        full_name='Test User 1',
        student_id='501111111'
    )

    # Try to create another user with same username
    with pytest.raises(Exception):
        database.create_user(
            username='testuser',  # Duplicate
            email='test2@example.com',
            password_hash=password_hash,
            role='student',
            full_name='Test User 2',
            student_id='502222222'
        )


def test_create_application(app, clean_db):
    """Test application creation."""
    # First create a user
    password_hash = generate_password_hash('password123')
    user_id = database.create_user(
        username='student1',
        email='student@example.com',
        password_hash=password_hash,
        role='student',
        full_name='Student Name',
        student_id='501234567'
    )

    # Create application
    app_id = database.create_application(
        user_id=user_id,
        full_name='Student Name',
        student_id='501234567',
        email='student@example.com'
    )

    assert app_id > 0

    # Retrieve and verify
    application = database.get_application_by_user_id(user_id)
    assert application['full_name'] == 'Student Name'
    assert application['student_id'] == '501234567'
    assert application['status'] == 'pending'


def test_duplicate_student_id_in_applications(app, clean_db):
    """Test that duplicate student IDs in applications are prevented."""
    password_hash = generate_password_hash('password123')

    # Create two users
    user_id1 = database.create_user(
        username='student1',
        email='student1@example.com',
        password_hash=password_hash,
        role='student',
        full_name='Student 1',
        student_id='501111111'
    )

    user_id2 = database.create_user(
        username='student2',
        email='student2@example.com',
        password_hash=password_hash,
        role='student',
        full_name='Student 2',
        student_id='502222222'
    )

    # Create first application
    database.create_application(user_id1, 'Student 1', '501234567', 'student1@example.com')

    # Try to create second application with same student_id (should fail)
    with pytest.raises(Exception):
        database.create_application(user_id2, 'Student 2', '501234567', 'student2@example.com')


def test_update_application_status(app, clean_db):
    """Test updating application status."""
    password_hash = generate_password_hash('password123')

    # Create student and coordinator
    student_id = database.create_user(
        username='student1',
        email='student1@example.com',
        password_hash=password_hash,
        role='student',
        full_name='Student Name',
        student_id='501234567'
    )

    coord_id = database.create_user(
        username='coordinator1',
        email='coord@example.com',
        password_hash=password_hash,
        role='coordinator',
        full_name='Coordinator Name',
        student_id=None
    )

    # Create application
    app_id = database.create_application(student_id, 'Student Name', '501234567', 'student1@example.com')

    # Update status
    success = database.update_application_status(app_id, 'accepted', coord_id)
    assert success is True

    # Verify
    app = database.get_application_by_user_id(student_id)
    assert app['status'] == 'accepted'
    assert app['reviewed_by'] == coord_id
    assert app['reviewed_at'] is not None


def test_create_report(app, clean_db):
    """Test report creation."""
    password_hash = generate_password_hash('password123')

    user_id = database.create_user(
        username='student1',
        email='student1@example.com',
        password_hash=password_hash,
        role='student',
        full_name='Student Name',
        student_id='501234567'
    )

    app_id = database.create_application(user_id, 'Student Name', '501234567', 'student1@example.com')

    report_id = database.create_report(
        application_id=app_id,
        user_id=user_id,
        report_title='Week 1 Report',
        work_description='Completed training',
        hours_worked=40,
        supervisor_name='Jane Manager',
        supervisor_email='jane@company.com'
    )

    assert report_id > 0

    reports = database.get_reports_by_user(user_id)
    assert len(reports) == 1
    assert reports[0]['report_title'] == 'Week 1 Report'
    assert reports[0]['hours_worked'] == 40


def test_create_evaluation(app, clean_db):
    """Test evaluation creation."""
    password_hash = generate_password_hash('password123')

    student_id = database.create_user(
        username='student1',
        email='student1@example.com',
        password_hash=password_hash,
        role='student',
        full_name='Student Name',
        student_id='501234567'
    )

    employer_id = database.create_user(
        username='employer1',
        email='employer@example.com',
        password_hash=password_hash,
        role='employer',
        full_name='Company Name',
        student_id=None
    )

    app_id = database.create_application(student_id, 'Student Name', '501234567', 'student1@example.com')

    eval_id = database.create_evaluation(
        student_user_id=student_id,
        employer_user_id=employer_id,
        application_id=app_id,
        technical_skills=4,
        communication=5,
        professionalism=4,
        overall_rating=4,
        comments='Excellent work!'
    )

    assert eval_id > 0

    evals = database.get_evaluations_for_student(student_id)
    assert len(evals) == 1
    assert evals[0]['overall_rating'] == 4
    assert evals[0]['comments'] == 'Excellent work!'


def test_foreign_key_constraints(app, clean_db):
    """Test that foreign key constraints are enforced."""
    # Try to create application with non-existent user_id
    with pytest.raises(Exception):
        database.create_application(
            user_id=9999,  # Doesn't exist
            full_name='Test',
            student_id='501234567',
            email='test@example.com'
        )
