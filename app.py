"""
Main Flask application for the Co-op Support Application.
Handles all routes, authentication, and business logic.
"""
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import re

import config
import database
from models import User

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(config)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

# Initialize database on startup
with app.app_context():
    database.init_db()


@login_manager.user_loader
def load_user(user_id):
    """Load user from database for Flask-Login."""
    return User.get(user_id)


# ============ CUSTOM DECORATORS ============

def role_required(role):
    """
    Decorator to check if user has required role.
    Usage: @role_required('coordinator')
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role != role:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ============ VALIDATION FUNCTIONS ============

def validate_registration(username, email, password, password_confirm, role, student_id=None):
    """
    Validate registration form data.

    Returns:
        tuple: (is_valid, error_message)
    """
    # Username validation
    if len(username) < 3 or len(username) > 50:
        return False, "Username must be 3-50 characters"

    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"

    # Email validation
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        return False, "Invalid email format"

    # Password validation
    if len(password) < 8:
        return False, "Password must be at least 8 characters"

    if password != password_confirm:
        return False, "Passwords do not match"

    # Student ID validation (only for students)
    if role == 'student':
        if not student_id:
            return False, "Student ID is required for students"
        if not re.match(r'^\d{9}$', student_id):
            return False, "Student ID must be exactly 9 digits"

    # Check for duplicate username/email
    if database.get_user_by_username(username):
        return False, "Username already exists"

    if database.get_user_by_email(email):
        return False, "Email already registered"

    return True, None


def validate_application(full_name, student_id, email):
    """
    Validate application submission data.

    Returns:
        tuple: (is_valid, error_message)
    """
    if not full_name or len(full_name.strip()) < 2:
        return False, "Full name must be at least 2 characters"

    if len(full_name.strip()) > 100:
        return False, "Full name must not exceed 100 characters"

    if not re.match(r'^\d{9}$', student_id):
        return False, "Student ID must be exactly 9 digits"

    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        return False, "Invalid email format"

    # Check for duplicate student_id
    if database.check_duplicate_student_id(student_id):
        return False, "An application with this Student ID already exists"

    return True, None


def validate_report(report_title, work_description, hours_worked, supervisor_name, supervisor_email):
    """
    Validate report submission data.

    Returns:
        tuple: (is_valid, error_message)
    """
    if not report_title or len(report_title.strip()) < 3:
        return False, "Report title must be at least 3 characters"

    if not work_description or len(work_description.strip()) < 10:
        return False, "Work description must be at least 10 characters"

    try:
        hours = int(hours_worked)
        if hours <= 0:
            return False, "Hours worked must be a positive number"
    except (ValueError, TypeError):
        return False, "Hours worked must be a valid number"

    if not supervisor_name or len(supervisor_name.strip()) < 2:
        return False, "Supervisor name is required"

    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', supervisor_email):
        return False, "Invalid supervisor email format"

    return True, None


def validate_evaluation(technical_skills, communication, professionalism, overall_rating):
    """
    Validate evaluation ratings.

    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        ratings = [
            int(technical_skills),
            int(communication),
            int(professionalism),
            int(overall_rating)
        ]

        for rating in ratings:
            if rating < 1 or rating > 5:
                return False, "All ratings must be between 1 and 5"

        return True, None
    except (ValueError, TypeError):
        return False, "All ratings must be valid numbers"


# ============ PUBLIC ROUTES ============

@app.route('/')
def index():
    """Landing page - redirects based on login status."""
    if current_user.is_authenticated:
        # Redirect to appropriate dashboard based on role
        if current_user.is_student():
            return redirect(url_for('student_dashboard'))
        elif current_user.is_coordinator():
            return redirect(url_for('coordinator_dashboard'))
        elif current_user.is_employer():
            return redirect(url_for('employer_dashboard'))

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        full_name = request.form.get('full_name', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        role = request.form.get('role', 'student')
        student_id = request.form.get('student_id', '').strip() if role == 'student' else None

        # Validate input
        is_valid, error_msg = validate_registration(
            username, email, password, password_confirm, role, student_id
        )

        if not is_valid:
            flash(error_msg, 'danger')
            return render_template('register.html')

        # Hash password and create user
        password_hash = generate_password_hash(password)

        try:
            user_id = database.create_user(
                username, email, password_hash, role, full_name, student_id
            )
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'An error occurred during registration: {str(e)}', 'danger')
            return render_template('register.html')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        user_row = database.get_user_by_username(username)

        if user_row and check_password_hash(user_row['password_hash'], password):
            # Create User object and log in
            user = User(
                user_id=user_row['id'],
                username=user_row['username'],
                email=user_row['email'],
                role=user_row['role'],
                full_name=user_row['full_name'],
                student_id=user_row['student_id']
            )
            login_user(user, remember=remember)
            flash(f'Welcome back, {user.full_name}!', 'success')

            # Redirect to appropriate dashboard
            if user.is_student():
                return redirect(url_for('student_dashboard'))
            elif user.is_coordinator():
                return redirect(url_for('coordinator_dashboard'))
            elif user.is_employer():
                return redirect(url_for('employer_dashboard'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """User logout."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ============ STUDENT ROUTES ============

@app.route('/student/dashboard')
@role_required('student')
def student_dashboard():
    """Student dashboard."""
    # Get student's application if exists
    application = database.get_application_by_user_id(current_user.id)
    return render_template('student_dashboard.html', application=application)


@app.route('/student/apply')
@role_required('student')
def student_apply():
    """Student application form."""
    # Check if student already has an application
    application = database.get_application_by_user_id(current_user.id)
    if application:
        flash('You have already submitted an application.', 'warning')
        return redirect(url_for('student_dashboard'))

    return render_template('student_apply.html')


@app.route('/api/student/submit-application', methods=['POST'])
@role_required('student')
def submit_application():
    """Handle application submission (API endpoint)."""
    data = request.get_json()

    full_name = data.get('full_name', '').strip()
    student_id = data.get('student_id', '').strip()
    email = data.get('email', '').strip()

    # Validate
    is_valid, error_msg = validate_application(full_name, student_id, email)
    if not is_valid:
        return jsonify({'success': False, 'error': error_msg}), 400

    # Check if student already has an application
    existing_app = database.get_application_by_user_id(current_user.id)
    if existing_app:
        return jsonify({'success': False, 'error': 'You have already submitted an application'}), 409

    try:
        app_id = database.create_application(current_user.id, full_name, student_id, email)
        return jsonify({
            'success': True,
            'message': 'Application submitted successfully!',
            'application_id': app_id
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/student/reports')
@role_required('student')
def student_reports():
    """Student reports page."""
    # Get student's application
    application = database.get_application_by_user_id(current_user.id)

    # Get student's reports
    reports = database.get_reports_by_user(current_user.id)

    return render_template('student_reports.html', application=application, reports=reports)


@app.route('/api/student/submit-report', methods=['POST'])
@role_required('student')
def submit_report():
    """Handle report submission with access control (API endpoint)."""
    data = request.get_json()

    # Check if student has an accepted application
    application = database.get_application_by_user_id(current_user.id)
    if not application:
        return jsonify({'success': False, 'error': 'You must submit an application first'}), 400

    if application['status'] != 'accepted':
        return jsonify({'success': False, 'error': 'Your application must be accepted before submitting reports'}), 403

    # Extract form data
    report_title = data.get('report_title', '').strip()
    work_description = data.get('work_description', '').strip()
    hours_worked = data.get('hours_worked', 0)
    supervisor_name = data.get('supervisor_name', '').strip()
    supervisor_email = data.get('supervisor_email', '').strip()

    # Extract access control data
    coordinator_ids = data.get('coordinator_ids', [])
    employer_id = data.get('employer_id')

    # Validate basic report fields
    is_valid, error_msg = validate_report(
        report_title, work_description, hours_worked, supervisor_name, supervisor_email
    )
    if not is_valid:
        return jsonify({'success': False, 'error': error_msg}), 400

    # Validate access control selections
    try:
        # Ensure coordinator_ids is a list
        if not isinstance(coordinator_ids, list):
            coordinator_ids = [coordinator_ids] if coordinator_ids else []

        # Convert to integers and remove any empty values
        coordinator_ids = [int(id) for id in coordinator_ids if id and str(id).strip()]
        employer_ids = [int(employer_id)] if employer_id and str(employer_id).strip() else []

<<<<<<< HEAD
        # Require at least one coordinator OR employer
        if not coordinator_ids and not employer_ids:
            return jsonify({
                'success': False,
                'error': 'Please select at least one coordinator or employer who can access this report'
            }), 400

=======
>>>>>>> 0cbc115 (Sprint 2 updates)
        # Validate that selected coordinators exist and have correct role
        for coord_id in coordinator_ids:
            user = database.get_user_by_id(coord_id)
            if not user:
                return jsonify({'success': False, 'error': f'Coordinator with ID {coord_id} not found'}), 400
            if user['role'] != 'coordinator':
                return jsonify({'success': False, 'error': f'User {user["full_name"]} is not a coordinator'}), 400

        # Validate that selected employers exist and have correct role
        for emp_id in employer_ids:
            user = database.get_user_by_id(emp_id)
            if not user:
                return jsonify({'success': False, 'error': f'Employer with ID {emp_id} not found'}), 400
            if user['role'] != 'employer':
                return jsonify({'success': False, 'error': f'User {user["full_name"]} is not an employer'}), 400

        # Create report with access control
        report_id = database.create_report_with_access(
            application['id'], current_user.id, report_title, work_description,
            int(hours_worked), supervisor_name, supervisor_email,
            coordinator_ids, employer_ids
        )

        return jsonify({
            'success': True,
            'message': 'Report submitted successfully with access control!',
            'report_id': report_id
        }), 201

    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid coordinator or employer ID format'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============ USER SELECTION API ENDPOINTS ============

@app.route('/api/users/coordinators', methods=['GET'])
@login_required
def get_coordinators_api():
    """
    Get all coordinators for dropdown selection.
    Returns list of coordinators for report access control.
    """
    try:
        coordinators = database.get_coordinators()
        # Convert to list of dictionaries for JSON response
        coordinator_list = []
        for coord in coordinators:
            coordinator_list.append({
                'id': coord['id'],
                'username': coord['username'],
                'full_name': coord['full_name'],
                'email': coord['email']
            })

        return jsonify({
            'success': True,
            'coordinators': coordinator_list
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve coordinators: {str(e)}'
        }), 500


@app.route('/api/users/employers', methods=['GET'])
@login_required
def get_employers_api():
    """
    Get all employers for dropdown selection.
    Returns list of employers for report access control.
    """
    try:
        employers = database.get_employers()
        # Convert to list of dictionaries for JSON response
        employer_list = []
        for emp in employers:
            employer_list.append({
                'id': emp['id'],
                'username': emp['username'],
                'full_name': emp['full_name'],
                'email': emp['email']
            })

        return jsonify({
            'success': True,
            'employers': employer_list
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve employers: {str(e)}'
        }), 500


# ============ COORDINATOR ROUTES ============

@app.route('/coordinator/dashboard')
@role_required('coordinator')
def coordinator_dashboard():
    """Coordinator dashboard."""
    # Get statistics
    all_apps = database.get_all_applications()
    pending_count = len([a for a in all_apps if a['status'] == 'pending'])
    accepted_count = len([a for a in all_apps if a['status'] == 'accepted'])
    rejected_count = len([a for a in all_apps if a['status'] == 'rejected'])

    return render_template('coordinator_dashboard.html',
                         total_applications=len(all_apps),
                         pending_count=pending_count,
                         accepted_count=accepted_count,
                         rejected_count=rejected_count)


@app.route('/coordinator/applications')
@role_required('coordinator')
def coordinator_applications():
    """View and review all applications."""
    # Get all applications
    applications = database.get_all_applications()
    return render_template('coordinator_applications.html', applications=applications)


@app.route('/api/coordinator/review-application', methods=['POST'])
@role_required('coordinator')
def review_application():
    """Approve or reject an application (API endpoint)."""
    data = request.get_json()

    application_id = data.get('application_id')
    status = data.get('status')

    if status not in ['accepted', 'rejected']:
        return jsonify({'success': False, 'error': 'Invalid status'}), 400

    try:
        success = database.update_application_status(application_id, status, current_user.id)
        if success:
            return jsonify({
                'success': True,
                'message': f'Application {status} successfully!'
            }), 200
        else:
            return jsonify({'success': False, 'error': 'Application not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/coordinator/reports')
@role_required('coordinator')
def coordinator_reports():
    """Coordinator report viewing page."""
    try:
        # Get reports accessible to this coordinator
        reports = database.get_reports_accessible_to_user(current_user.id, 'coordinator')
        return render_template('coordinator_reports.html', reports=reports)
    except Exception as e:
        flash(f'Error loading reports: {str(e)}', 'danger')
        return redirect(url_for('coordinator_dashboard'))


@app.route('/api/coordinator/reports', methods=['GET'])
@role_required('coordinator')
def get_coordinator_reports_api():
    """Get reports accessible to current coordinator (API endpoint)."""
    try:
        reports = database.get_reports_accessible_to_user(current_user.id, 'coordinator')
        # Convert to list of dictionaries for JSON response
        report_list = []
        for report in reports:
            report_list.append({
                'id': report['id'],
                'report_title': report['report_title'],
                'student_name': report['student_name'],
                'hours_worked': report['hours_worked'],
                'submitted_at': report['submitted_at'],
                'work_description': report['work_description'][:100] + '...' if len(report['work_description']) > 100 else report['work_description']
            })

        return jsonify({
            'success': True,
            'reports': report_list
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve reports: {str(e)}'
        }), 500


# ============ EMPLOYER ROUTES ============

@app.route('/employer/dashboard')
@role_required('employer')
def employer_dashboard():
    """Employer dashboard."""
    return render_template('employer_dashboard.html')


@app.route('/employer/students')
@role_required('employer')
def employer_students():
    """View list of students to evaluate."""
    students = database.get_students_with_accepted_applications()
    return render_template('employer_students.html', students=students)


@app.route('/employer/evaluate/<int:student_id>')
@role_required('employer')
def employer_evaluate(student_id):
    """Evaluation form for a specific student."""
    student = database.get_user_by_id(student_id)
    if not student or student['role'] != 'student':
        flash('Student not found.', 'danger')
        return redirect(url_for('employer_students'))

    # Get student's application
    application = database.get_application_by_user_id(student_id)
    if not application or application['status'] != 'accepted':
        flash('Student does not have an accepted application.', 'warning')
        return redirect(url_for('employer_students'))

    return render_template('employer_evaluate.html', student=student, application=application)


@app.route('/api/employer/submit-evaluation', methods=['POST'])
@role_required('employer')
def submit_evaluation():
    """Handle evaluation submission (API endpoint)."""
    data = request.get_json()

    student_user_id = data.get('student_user_id')
    application_id = data.get('application_id')
    technical_skills = data.get('technical_skills')
    communication = data.get('communication')
    professionalism = data.get('professionalism')
    overall_rating = data.get('overall_rating')
    comments = data.get('comments', '').strip()

    # Validate ratings
    is_valid, error_msg = validate_evaluation(
        technical_skills, communication, professionalism, overall_rating
    )
    if not is_valid:
        return jsonify({'success': False, 'error': error_msg}), 400

    try:
        eval_id = database.create_evaluation(
            int(student_user_id), current_user.id, int(application_id),
            int(technical_skills), int(communication), int(professionalism),
            int(overall_rating), comments
        )
        return jsonify({
            'success': True,
            'message': 'Evaluation submitted successfully!',
            'evaluation_id': eval_id
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/employer/reports')
@role_required('employer')
def employer_reports():
    """Employer report viewing page."""
    try:
        # Get reports accessible to this employer
        reports = database.get_reports_accessible_to_user(current_user.id, 'employer')
        return render_template('employer_reports.html', reports=reports)
    except Exception as e:
        flash(f'Error loading reports: {str(e)}', 'danger')
        return redirect(url_for('employer_dashboard'))


@app.route('/api/employer/reports', methods=['GET'])
@role_required('employer')
def get_employer_reports_api():
    """Get reports accessible to current employer (API endpoint)."""
    try:
        reports = database.get_reports_accessible_to_user(current_user.id, 'employer')
        # Convert to list of dictionaries for JSON response
        report_list = []
        for report in reports:
            report_list.append({
                'id': report['id'],
                'report_title': report['report_title'],
                'student_name': report['student_name'],
                'hours_worked': report['hours_worked'],
                'submitted_at': report['submitted_at'],
                'work_description': report['work_description'][:100] + '...' if len(report['work_description']) > 100 else report['work_description']
            })

        return jsonify({
            'success': True,
            'reports': report_list
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve reports: {str(e)}'
        }), 500


@app.route('/reports/<int:report_id>')
@login_required
def view_report(report_id):
    """View specific report with access control."""
    try:
        # Determine user access type
        if current_user.role == 'coordinator':
            access_type = 'coordinator'
        elif current_user.role == 'employer':
            access_type = 'employer'
        elif current_user.role == 'student':
            # Students can view their own reports
            report = database.get_reports_by_user(current_user.id)
            student_report = next((r for r in report if r['id'] == report_id), None)
            if student_report:
                return render_template('report_details.html', report=student_report, is_own_report=True)
            else:
                flash('Report not found or you do not have access.', 'danger')
                return redirect(url_for('student_reports'))
        else:
            flash('You do not have permission to view reports.', 'danger')
            return redirect(url_for('index'))

        # Check access for coordinators and employers
        report = database.get_report_with_access_check(report_id, current_user.id, access_type)
        if not report:
            flash('Report not found or you do not have access.', 'danger')
            if current_user.role == 'coordinator':
                return redirect(url_for('coordinator_reports'))
            else:
                return redirect(url_for('employer_reports'))

        return render_template('report_details.html', report=report, is_own_report=False)
    except Exception as e:
        flash(f'Error loading report: {str(e)}', 'danger')
        return redirect(url_for('index'))


# ============ ERROR HANDLERS ============

@app.errorhandler(401)
def unauthorized(e):
    """Handle unauthorized access."""
    flash('Please log in to access this page.', 'warning')
    return redirect(url_for('login'))


@app.errorhandler(403)
def forbidden(e):
    """Handle forbidden access."""
    flash('You do not have permission to access this page.', 'danger')
    return redirect(url_for('index'))


@app.errorhandler(404)
def not_found(e):
    """Handle page not found."""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle internal server error."""
    return render_template('500.html'), 500


# ============ RUN APPLICATION ============

if __name__ == '__main__':
    app.run(debug=config.DEBUG)
