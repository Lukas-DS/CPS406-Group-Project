# Co-op Support Application

A complete Flask-based web application for managing student co-op applications, coordinator reviews, and employer evaluations. Built with Python, Flask, and SQLite.

## Features

### 1. Student Features

- Register and login as a student
- Submit co-op applications with name, student ID, and email
- View application status (pending, accepted, rejected)
- Submit work reports after application is accepted
- View all submitted reports

### 2. Coordinator Features

- Register and login as a coordinator
- View dashboard with application statistics
- Review all student applications
- Approve or reject applications
- View all submitted student reports

### 3. Employer Features

- Register and login as an employer
- View list of students with accepted applications
- Submit detailed evaluations for students (ratings 1-5)
- Rate technical skills, communication, professionalism, and overall performance
- Add comments to evaluations

### 4. Technical Features

- User authentication with password hashing
- Role-based access control (student/coordinator/employer)
- SQLite database with proper relationships
- Client-side and server-side validation
- RESTful API endpoints
- Comprehensive automated test suite (40 tests)

## Technology Stack

- **Backend**: Flask 3.0.0
- **Authentication**: Flask-Login 0.6.3
- **Database**: SQLite3 (native Python)
- **Password Security**: Werkzeug (secure hashing)
- **Testing**: pytest 7.4.3
- **Frontend**: HTML, CSS (Bootstrap CDN), JavaScript

## Project Structure

```
CPS406-Group-Project/
├── app.py                          # Main Flask application
├── database.py                     # Database operations
├── models.py                       # User model for Flask-Login
├── config.py                       # Configuration settings
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── .gitignore                      # Git ignore patterns
├── templates/                      # HTML templates
│   ├── base.html                   # Base template with navigation
│   ├── register.html               # Registration form
│   ├── login.html                  # Login page
│   ├── student_dashboard.html      # Student home page
│   ├── student_apply.html          # Application submission form
│   ├── student_reports.html        # Report submission and viewing
│   ├── coordinator_dashboard.html  # Coordinator dashboard
│   ├── coordinator_applications.html # Application review interface
│   ├── employer_dashboard.html     # Employer home page
│   ├── employer_students.html      # List of students to evaluate
│   └── employer_evaluate.html      # Evaluation submission form
├── static/                         # Static files
│   └── css/
│       └── style.css               # Custom styling
├── tests/                          # Test files
│   ├── __init__.py
│   ├── conftest.py                 # pytest fixtures
│   ├── test_auth.py                # Authentication tests (12 tests)
│   ├── test_student.py             # Student feature tests (9 tests)
│   ├── test_coordinator.py         # Coordinator feature tests (5 tests)
│   ├── test_employer.py            # Employer feature tests (5 tests)
│   └── test_database.py            # Database tests (9 tests)
└── instance/                       # Runtime data
    └── coop_app.db                 # SQLite database (created at runtime)
```

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### 1. Clone or Navigate to Project

```bash
cd CPS406-Group-Project
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python app.py
```

The application will start at: **http://127.0.0.1:5000**

## Running Tests

```bash
# Run all tests with verbose output
pytest -v

# Run specific test file
pytest tests/test_auth.py -v

# Run with coverage report
pytest --cov=. --cov-report=term-missing

# Run specific test
pytest tests/test_auth.py::test_login_valid -v
```

**Test Results**: ✅ All 40 tests passing

## Database Access

The SQLite database is automatically created in `instance/coop_app.db` on first run.

### View Database Contents

```bash
# Using SQLite command line
sqlite3 instance/coop_app.db "SELECT * FROM applications;"

# View all users
sqlite3 instance/coop_app.db "SELECT id, username, role FROM users;"

# View application status distribution
sqlite3 instance/coop_app.db "SELECT status, COUNT(*) FROM applications GROUP BY status;"
```

### Or use DB Browser for SQLite (GUI)

1. Download: https://sqlitebrowser.org/
2. Open: `instance/coop_app.db`
3. Browse tables visually

### Reset Database

```bash
rm instance/coop_app.db
python app.py  # Database will be recreated
```

## Usage Workflows

### Student Workflow

1. Navigate to http://127.0.0.1:5000/register
2. Register as a student (requires 9-digit student ID)
3. Login with your credentials
4. Click "Apply" to submit your co-op application
5. Once approved, submit work reports in the "Reports" section

### Coordinator Workflow

1. Register as a coordinator
2. Login to access coordinator dashboard
3. View all applications in "Applications" section
4. Click "Approve" or "Reject" on pending applications
5. View student reports in the dashboard

### Employer Workflow

1. Register as an employer
2. Login to access employer dashboard
3. Click "Evaluate Students" to see students with accepted applications
4. Complete the evaluation form with ratings and comments
5. Submit the evaluation

## API Endpoints

### Authentication

- `POST /register` - Create new user account
- `POST /login` - Authenticate user
- `GET /logout` - End session

### Student

- `GET /student/dashboard` - View application status
- `GET /student/apply` - Application form
- `POST /api/student/submit-application` - Submit application
- `GET /student/reports` - View/submit reports
- `POST /api/student/submit-report` - Submit report

### Coordinator

- `GET /coordinator/dashboard` - View statistics
- `GET /coordinator/applications` - Review applications
- `POST /api/coordinator/review-application` - Approve/reject

### Employer

- `GET /employer/dashboard` - Employer home
- `GET /employer/students` - List students
- `GET /employer/evaluate/<student_id>` - Evaluation form
- `POST /api/employer/submit-evaluation` - Submit evaluation

## Validation Rules

### Registration

- Username: 3-50 characters, alphanumeric with underscores
- Email: Valid email format
- Password: Minimum 8 characters, must match confirmation
- Student ID: 9 digits (for students only)

### Application

- Full Name: 2-100 characters
- Student ID: Exactly 9 digits, must be unique
- Email: Valid email format

### Reports

- Title: Minimum 3 characters
- Description: Minimum 10 characters
- Hours: Positive integer
- Supervisor Email: Valid email format

### Evaluations

- All ratings: 1-5 scale
- Comments: Optional text

## Database Schema

### Users Table

- `id` (PK): User ID
- `username` (UNIQUE): Login username
- `email` (UNIQUE): User email
- `password_hash`: Hashed password
- `role`: student, coordinator, or employer
- `full_name`: Full name
- `student_id` (UNIQUE): Student ID (nullable)
- `created_at`: Registration timestamp

### Applications Table

- `id` (PK): Application ID
- `user_id` (FK): Student user ID
- `full_name`: Student's full name
- `student_id` (UNIQUE): Student ID
- `email`: Student email
- `submitted_at`: Submission timestamp
- `status`: pending, accepted, or rejected
- `reviewed_by` (FK): Coordinator user ID (nullable)
- `reviewed_at`: Review timestamp (nullable)

### Reports Table

- `id` (PK): Report ID
- `application_id` (FK): Associated application
- `user_id` (FK): Student user ID
- `report_title`: Report title
- `work_description`: Description of work
- `hours_worked`: Hours worked
- `supervisor_name`: Supervisor name
- `supervisor_email`: Supervisor email
- `submitted_at`: Submission timestamp

### Evaluations Table

- `id` (PK): Evaluation ID
- `student_user_id` (FK): Student being evaluated
- `employer_user_id` (FK): Employer submitting
- `application_id` (FK): Associated application
- `technical_skills`: Rating 1-5
- `communication`: Rating 1-5
- `professionalism`: Rating 1-5
- `overall_rating`: Rating 1-5
- `comments`: Optional feedback
- `submitted_at`: Submission timestamp

## Test Coverage

**Total Tests**: 40 ✅ All Passing

- **Authentication Tests** (12): Registration, login, logout, validations, role-based access
- **Student Tests** (9): Application submission, reports, validations
- **Coordinator Tests** (5): Dashboard, application review, access control
- **Employer Tests** (5): Dashboard, student viewing, evaluations
- **Database Tests** (9): User creation, applications, reports, evaluations, constraints

## Development Notes

### Adding New Features

1. Update database schema in `database.py` if needed
2. Add database functions in `database.py`
3. Add routes in `app.py`
4. Create templates in `templates/`
5. Add tests in `tests/`

### Common Development Commands

```bash
# Reset database and start fresh
rm instance/coop_app.db
python app.py

# Run app in debug mode (automatic)
python app.py

# Run specific test with output
pytest tests/test_student.py::test_submit_application_valid -v -s
```

## Security Features

- ✅ Password hashing (PBKDF2-SHA256)
- ✅ Session management with Flask-Login
- ✅ Server-side validation (never trust client)
- ✅ Role-based access control (decorators)
- ✅ SQL injection prevention (parameterized queries)
- ✅ UNIQUE constraints on sensitive data
- ✅ Foreign key constraints for data integrity

## Troubleshooting

### Port Already in Use

```bash
# Change port in app.py
app.run(debug=True, port=5001)
```

### Database Locked

- Close any other instances of the app
- Delete `instance/coop_app.db` and restart

### Import Errors

```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Tests Failing

```bash
# Ensure test database is clean
rm instance/test_coop_app.db
pytest -v
```

## Future Enhancements

Possible features for later sprints:

- Email notifications for application status
- PDF report generation
- Export evaluations to CSV
- Admin dashboard with analytics
- Student portfolio system
- Job matching system

## Demo Users (For Testing)

You can create test users by registering through the UI, or run:

```bash
python
>>> from werkzeug.security import generate_password_hash
>>> import database
>>> database.init_db()
>>> database.create_user('student1', 'student1@example.com',
...                      generate_password_hash('password123'),
...                      'student', 'John Doe', '501234567')
>>> database.create_user('coordinator1', 'coordinator@example.com',
...                      generate_password_hash('password123'),
...                      'coordinator', 'Jane Smith', None)
>>> database.create_user('employer1', 'employer@example.com',
...                      generate_password_hash('password123'),
...                      'employer', 'ABC Company', None)
```

Then login with:

- Student: `student1` / `password123`
- Coordinator: `coordinator1` / `password123`
- Employer: `employer1` / `password123`

## Submission Checklist

Before submitting:

- [ ] All 40 tests passing
- [ ] Database initializes without errors
- [ ] Can register new users (all roles)
- [ ] Can login and logout
- [ ] Student can submit application
- [ ] Coordinator can review and approve/reject
- [ ] Student can submit reports (after acceptance)
- [ ] Employer can submit evaluations
- [ ] Role-based access control working
- [ ] Validation working (client and server)
- [ ] No hardcoded credentials in code

## Support & Documentation

For detailed implementation information, see:

- **Database Design**: `database.py` (schema and functions)
- **Routes & Logic**: `app.py` (main application logic)
- **User Model**: `models.py` (Flask-Login integration)
- **Tests**: `tests/` (usage examples)

## License

This project is for educational purposes as part of the CPS406 Software Design course.

---

**Status**: ✅ Complete and Ready for Demo

**Last Updated**: March 24, 2026

**All Features Implemented**: Student Applications, Coordinator Review, Employer Evaluations, Authentication, Role-Based Access Control, Database Persistence, Comprehensive Test Suite
