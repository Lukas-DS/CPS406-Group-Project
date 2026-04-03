"""
Database operations for the Co-op Support Application.
Handles schema creation, CRUD operations, and queries.
"""
import sqlite3
import os
import config


def init_db():
    """
    Initialize the database and create all tables with proper schema.
    Creates the instance folder if it doesn't exist.
    """
    # Create instance folder if it doesn't exist
    os.makedirs('instance', exist_ok=True)

    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()

    # Enable foreign key constraints
    cursor.execute('PRAGMA foreign_keys = ON')

    # Create users table (for authentication)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('student', 'coordinator', 'employer')),
            full_name TEXT NOT NULL,
            student_id TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create applications table (student co-op applications)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            full_name TEXT NOT NULL,
            student_id TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'accepted', 'rejected')),
            reviewed_by INTEGER,
            reviewed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (reviewed_by) REFERENCES users(id)
        )
    ''')

    # Create reports table (student work reports)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            report_title TEXT NOT NULL,
            work_description TEXT NOT NULL,
            hours_worked INTEGER NOT NULL,
            supervisor_name TEXT NOT NULL,
            supervisor_email TEXT NOT NULL,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (application_id) REFERENCES applications(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Create evaluations table (employer evaluations of students)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_user_id INTEGER NOT NULL,
            employer_user_id INTEGER NOT NULL,
            application_id INTEGER NOT NULL,
            technical_skills INTEGER NOT NULL CHECK(technical_skills BETWEEN 1 AND 5),
            communication INTEGER NOT NULL CHECK(communication BETWEEN 1 AND 5),
            professionalism INTEGER NOT NULL CHECK(professionalism BETWEEN 1 AND 5),
            overall_rating INTEGER NOT NULL CHECK(overall_rating BETWEEN 1 AND 5),
            comments TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_user_id) REFERENCES users(id),
            FOREIGN KEY (employer_user_id) REFERENCES users(id),
            FOREIGN KEY (application_id) REFERENCES applications(id)
        )
    ''')

    # Create report_access table (controls which coordinators/employers can access reports)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS report_access (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            access_type TEXT NOT NULL CHECK(access_type IN ('coordinator', 'employer')),
            granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(report_id, user_id, access_type)
        )
    ''')

    # Create indexes for faster queries
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_student_id ON applications(student_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_role ON users(role)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_application_status ON applications(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_application_user ON applications(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_reports_application ON reports(application_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_evaluations_student ON evaluations(student_user_id)')

    # Indexes for report_access table
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_report_access_report ON report_access(report_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_report_access_user ON report_access(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_report_access_type ON report_access(access_type)')

    conn.commit()
    conn.close()
    print(f"Database initialized successfully at {config.DATABASE_PATH}")


def get_db_connection():
    """
    Create and return a database connection with row factory.
    Allows accessing columns by name using row['column_name'].
    """
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')  # Enable foreign keys
    return conn


# ============ USER OPERATIONS ============

def create_user(username, email, password_hash, role, full_name, student_id=None):
    """
    Create a new user account.

    Args:
        username: Unique username for login
        email: Unique email address
        password_hash: Hashed password (use werkzeug.security.generate_password_hash)
        role: 'student', 'coordinator', or 'employer'
        full_name: User's full name
        student_id: Student ID (required only for students, 9 digits)

    Returns:
        int: The ID of the newly created user

    Raises:
        sqlite3.IntegrityError: If username, email, or student_id already exists
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, role, full_name, student_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, email, password_hash, role, full_name, student_id))

        conn.commit()
        user_id = cursor.lastrowid
        return user_id
    finally:
        conn.close()


def get_user_by_username(username):
    """
    Retrieve a user by username (for login authentication).

    Args:
        username: The username to search for

    Returns:
        sqlite3.Row: User row if found, None otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        return cursor.fetchone()
    finally:
        conn.close()


def get_user_by_email(email):
    """
    Retrieve a user by email.

    Args:
        email: The email to search for

    Returns:
        sqlite3.Row: User row if found, None otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        return cursor.fetchone()
    finally:
        conn.close()


def get_user_by_id(user_id):
    """
    Retrieve a user by ID (for Flask-Login session management).

    Args:
        user_id: The user ID to search for

    Returns:
        sqlite3.Row: User row if found, None otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        return cursor.fetchone()
    finally:
        conn.close()


def get_users_by_role(role):
    """
    Get all users with specified role for dropdown selection.

    Args:
        role: The role to filter by ('student', 'coordinator', 'employer')

    Returns:
        list: List of user rows with the specified role
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            'SELECT id, username, email, full_name, role FROM users WHERE role = ? ORDER BY full_name',
            (role,)
        )
        return cursor.fetchall()
    finally:
        conn.close()


def get_coordinators():
    """
    Get all coordinators for dropdown selection.

    Returns:
        list: List of coordinator user rows
    """
    return get_users_by_role('coordinator')


def get_employers():
    """
    Get all employers for dropdown selection.

    Returns:
        list: List of employer user rows
    """
    return get_users_by_role('employer')


# ============ APPLICATION OPERATIONS ============

def create_application(user_id, full_name, student_id, email):
    """
    Create a new co-op application.

    Args:
        user_id: ID of the student submitting the application
        full_name: Applicant's full name
        student_id: Student ID (must be unique, 9 digits)
        email: Applicant's email

    Returns:
        int: The ID of the newly created application

    Raises:
        sqlite3.IntegrityError: If student_id already exists
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO applications (user_id, full_name, student_id, email)
            VALUES (?, ?, ?, ?)
        ''', (user_id, full_name, student_id, email))

        conn.commit()
        application_id = cursor.lastrowid
        return application_id
    finally:
        conn.close()


def check_duplicate_student_id(student_id):
    """
    Check if a student_id already exists in the applications table.

    Args:
        student_id: The student ID to check

    Returns:
        bool: True if duplicate exists, False otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            'SELECT COUNT(*) as count FROM applications WHERE student_id = ?',
            (student_id,)
        )
        result = cursor.fetchone()
        return result['count'] > 0
    finally:
        conn.close()


def get_application_by_user_id(user_id):
    """
    Get the application for a specific user.

    Args:
        user_id: The user ID

    Returns:
        sqlite3.Row: Application row if found, None otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT * FROM applications WHERE user_id = ?', (user_id,))
        return cursor.fetchone()
    finally:
        conn.close()


def get_all_applications():
    """
    Get all applications (for coordinator dashboard).

    Returns:
        list: List of all application rows
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT * FROM applications ORDER BY submitted_at DESC')
        return cursor.fetchall()
    finally:
        conn.close()


def get_applications_by_status(status):
    """
    Get applications filtered by status.

    Args:
        status: 'pending', 'accepted', or 'rejected'

    Returns:
        list: List of applications with the specified status
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            'SELECT * FROM applications WHERE status = ? ORDER BY submitted_at DESC',
            (status,)
        )
        return cursor.fetchall()
    finally:
        conn.close()


def update_application_status(application_id, status, coordinator_id):
    """
    Update the status of an application (approve or reject).

    Args:
        application_id: ID of the application to update
        status: New status ('accepted' or 'rejected')
        coordinator_id: ID of the coordinator making the decision

    Returns:
        bool: True if update was successful, False otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE applications
            SET status = ?, reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, coordinator_id, application_id))

        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# ============ REPORT OPERATIONS ============

def create_report(application_id, user_id, report_title, work_description,
                 hours_worked, supervisor_name, supervisor_email):
    """
    Create a new work report.

    Args:
        application_id: ID of the associated application
        user_id: ID of the student submitting the report
        report_title: Title of the report
        work_description: Description of work performed
        hours_worked: Number of hours worked
        supervisor_name: Name of supervisor
        supervisor_email: Email of supervisor

    Returns:
        int: The ID of the newly created report
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO reports (application_id, user_id, report_title, work_description,
                               hours_worked, supervisor_name, supervisor_email)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (application_id, user_id, report_title, work_description,
              hours_worked, supervisor_name, supervisor_email))

        conn.commit()
        report_id = cursor.lastrowid
        return report_id
    finally:
        conn.close()


def get_reports_by_user(user_id):
    """
    Get all reports submitted by a specific user.

    Args:
        user_id: The user ID

    Returns:
        list: List of report rows
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            'SELECT * FROM reports WHERE user_id = ? ORDER BY submitted_at DESC',
            (user_id,)
        )
        return cursor.fetchall()
    finally:
        conn.close()


def get_all_reports():
    """
    Get all reports (for coordinator to view).
    NOTE: This function is deprecated in favor of access-controlled report viewing.

    Returns:
        list: List of all report rows
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT * FROM reports ORDER BY submitted_at DESC')
        return cursor.fetchall()
    finally:
        conn.close()


def create_report_with_access(application_id, user_id, report_title, work_description,
                            hours_worked, supervisor_name, supervisor_email,
                            coordinator_ids, employer_ids):
    """
    Create a new work report and grant access to specified coordinators/employers in one transaction.

    Args:
        application_id: ID of the associated application
        user_id: ID of the student submitting the report
        report_title: Title of the report
        work_description: Description of work performed
        hours_worked: Number of hours worked
        supervisor_name: Name of supervisor
        supervisor_email: Email of supervisor
        coordinator_ids: List of coordinator user IDs to grant access to
        employer_ids: List of employer user IDs to grant access to

    Returns:
        int: The ID of the newly created report

    Raises:
        sqlite3.Error: If transaction fails
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Begin transaction
        cursor.execute('BEGIN TRANSACTION')

        # Create the report
        cursor.execute('''
            INSERT INTO reports (application_id, user_id, report_title, work_description,
                               hours_worked, supervisor_name, supervisor_email)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (application_id, user_id, report_title, work_description,
              hours_worked, supervisor_name, supervisor_email))

        report_id = cursor.lastrowid

        # Grant access to coordinators
        for coordinator_id in coordinator_ids:
            cursor.execute('''
                INSERT INTO report_access (report_id, user_id, access_type)
                VALUES (?, ?, ?)
            ''', (report_id, coordinator_id, 'coordinator'))

        # Grant access to employers
        for employer_id in employer_ids:
            cursor.execute('''
                INSERT INTO report_access (report_id, user_id, access_type)
                VALUES (?, ?, ?)
            ''', (report_id, employer_id, 'employer'))

        # Commit transaction
        conn.commit()
        return report_id
    except Exception as e:
        # Rollback on error
        conn.rollback()
        raise e
    finally:
        conn.close()


def grant_report_access(report_id, user_id, access_type):
    """
    Grant access to specific user for a report.

    Args:
        report_id: ID of the report
        user_id: ID of the user to grant access to
        access_type: 'coordinator' or 'employer'

    Returns:
        bool: True if access was granted, False if already existed
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT OR IGNORE INTO report_access (report_id, user_id, access_type)
            VALUES (?, ?, ?)
        ''', (report_id, user_id, access_type))

        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_reports_accessible_to_user(user_id, access_type):
    """
    Get all reports that a coordinator/employer has access to view.

    Args:
        user_id: ID of the coordinator/employer
        access_type: 'coordinator' or 'employer'

    Returns:
        list: List of report rows that the user can access
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT DISTINCT r.*, u.full_name as student_name, u.username as student_username
            FROM reports r
            INNER JOIN report_access ra ON r.id = ra.report_id
            INNER JOIN users u ON r.user_id = u.id
            WHERE ra.user_id = ? AND ra.access_type = ?
            ORDER BY r.submitted_at DESC
        ''', (user_id, access_type))
        return cursor.fetchall()
    finally:
        conn.close()


def get_report_with_access_check(report_id, user_id, access_type):
    """
    Get report details if user has access, otherwise return None.

    Args:
        report_id: ID of the report
        user_id: ID of the requesting user
        access_type: 'coordinator' or 'employer'

    Returns:
        sqlite3.Row: Report row if user has access, None otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT r.*, u.full_name as student_name, u.username as student_username
            FROM reports r
            INNER JOIN report_access ra ON r.id = ra.report_id
            INNER JOIN users u ON r.user_id = u.id
            WHERE r.id = ? AND ra.user_id = ? AND ra.access_type = ?
        ''', (report_id, user_id, access_type))
        return cursor.fetchone()
    finally:
        conn.close()


# ============ EVALUATION OPERATIONS ============

def create_evaluation(student_user_id, employer_user_id, application_id,
                     technical_skills, communication, professionalism,
                     overall_rating, comments):
    """
    Create a new student evaluation.

    Args:
        student_user_id: ID of the student being evaluated
        employer_user_id: ID of the employer submitting the evaluation
        application_id: ID of the associated application
        technical_skills: Rating 1-5
        communication: Rating 1-5
        professionalism: Rating 1-5
        overall_rating: Rating 1-5
        comments: Optional text comments

    Returns:
        int: The ID of the newly created evaluation
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO evaluations (student_user_id, employer_user_id, application_id,
                                   technical_skills, communication, professionalism,
                                   overall_rating, comments)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (student_user_id, employer_user_id, application_id, technical_skills,
              communication, professionalism, overall_rating, comments))

        conn.commit()
        evaluation_id = cursor.lastrowid
        return evaluation_id
    finally:
        conn.close()


def get_evaluations_for_student(student_user_id):
    """
    Get all evaluations for a specific student.

    Args:
        student_user_id: The student user ID

    Returns:
        list: List of evaluation rows
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            'SELECT * FROM evaluations WHERE student_user_id = ? ORDER BY submitted_at DESC',
            (student_user_id,)
        )
        return cursor.fetchall()
    finally:
        conn.close()


def get_all_evaluations():
    """
    Get all evaluations.

    Returns:
        list: List of all evaluation rows
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT * FROM evaluations ORDER BY submitted_at DESC')
        return cursor.fetchall()
    finally:
        conn.close()


def get_students_with_accepted_applications():
    """
    Get all students who have accepted applications (for employer to evaluate).

    Returns:
        list: List of user rows (students only) with accepted applications
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT DISTINCT u.* FROM users u
            INNER JOIN applications a ON u.id = a.user_id
            WHERE a.status = 'accepted'
            ORDER BY u.full_name
        ''')
        return cursor.fetchall()
    finally:
        conn.close()


if __name__ == '__main__':
    # Initialize database when run directly
    init_db()
    print("Database tables created successfully!")

"""
Database operations for the Co-op Support Application.
Handles schema creation, CRUD operations, and queries.
"""
import sqlite3
import os
import config


def init_db():
    """
    Initialize the database and create all tables with proper schema.
    Creates the instance folder if it doesn't exist.
    """
    # Create instance folder if it doesn't exist
    os.makedirs('instance', exist_ok=True)

    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()

    # Enable foreign key constraints
    cursor.execute('PRAGMA foreign_keys = ON')

    # Create users table (for authentication)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('student', 'coordinator', 'employer')),
            full_name TEXT NOT NULL,
            student_id TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create applications table (student co-op applications)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            full_name TEXT NOT NULL,
            student_id TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'accepted', 'rejected')),
            reviewed_by INTEGER,
            reviewed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (reviewed_by) REFERENCES users(id)
        )
    ''')

    # Create reports table (student work reports)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            report_title TEXT NOT NULL,
            work_description TEXT NOT NULL,
            hours_worked INTEGER NOT NULL,
            supervisor_name TEXT NOT NULL,
            supervisor_email TEXT NOT NULL,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (application_id) REFERENCES applications(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Create evaluations table (employer evaluations of students)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_user_id INTEGER NOT NULL,
            employer_user_id INTEGER NOT NULL,
            application_id INTEGER NOT NULL,
            technical_skills INTEGER NOT NULL CHECK(technical_skills BETWEEN 1 AND 5),
            communication INTEGER NOT NULL CHECK(communication BETWEEN 1 AND 5),
            professionalism INTEGER NOT NULL CHECK(professionalism BETWEEN 1 AND 5),
            overall_rating INTEGER NOT NULL CHECK(overall_rating BETWEEN 1 AND 5),
            comments TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_user_id) REFERENCES users(id),
            FOREIGN KEY (employer_user_id) REFERENCES users(id),
            FOREIGN KEY (application_id) REFERENCES applications(id)
        )
    ''')

    # Create report_access table (controls which coordinators/employers can access reports)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS report_access (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            access_type TEXT NOT NULL CHECK(access_type IN ('coordinator', 'employer')),
            granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(report_id, user_id, access_type)
        )
    ''')

    # Create indexes for faster queries
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_student_id ON applications(student_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_role ON users(role)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_application_status ON applications(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_application_user ON applications(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_reports_application ON reports(application_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_evaluations_student ON evaluations(student_user_id)')

    # Indexes for report_access table
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_report_access_report ON report_access(report_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_report_access_user ON report_access(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_report_access_type ON report_access(access_type)')

    conn.commit()
    conn.close()
    print(f"Database initialized successfully at {config.DATABASE_PATH}")


def get_db_connection():
    """
    Create and return a database connection with row factory.
    Allows accessing columns by name using row['column_name'].
    """
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')  # Enable foreign keys
    return conn


# ============ USER OPERATIONS ============

def create_user(username, email, password_hash, role, full_name, student_id=None):
    """
    Create a new user account.

    Args:
        username: Unique username for login
        email: Unique email address
        password_hash: Hashed password (use werkzeug.security.generate_password_hash)
        role: 'student', 'coordinator', or 'employer'
        full_name: User's full name
        student_id: Student ID (required only for students, 9 digits)

    Returns:
        int: The ID of the newly created user

    Raises:
        sqlite3.IntegrityError: If username, email, or student_id already exists
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, role, full_name, student_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, email, password_hash, role, full_name, student_id))
        conn.commit()
        return cursor.lastrowid

    except sqlite3.IntegrityError as e:
        error_msg = str(e)
        if "username" in error_msg:
            raise ValueError("Username already exists.")
        elif "email" in error_msg:
            raise ValueError("Email already exists.")
        elif "student_id" in error_msg:
            raise ValueError("A user with this Student ID already exists.")
        else:
            raise ValueError("Registration failed due to database error.")

    finally:
        conn.close()


def get_user_by_username(username):
    """
    Retrieve a user by username (for login authentication).

    Args:
        username: The username to search for

    Returns:
        sqlite3.Row: User row if found, None otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        return cursor.fetchone()
    finally:
        conn.close()


def get_user_by_email(email):
    """
    Retrieve a user by email.

    Args:
        email: The email to search for

    Returns:
        sqlite3.Row: User row if found, None otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        return cursor.fetchone()
    finally:
        conn.close()


def get_user_by_id(user_id):
    """
    Retrieve a user by ID (for Flask-Login session management).

    Args:
        user_id: The user ID to search for

    Returns:
        sqlite3.Row: User row if found, None otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        return cursor.fetchone()
    finally:
        conn.close()


def get_users_by_role(role):
    """
    Get all users with specified role for dropdown selection.

    Args:
        role: The role to filter by ('student', 'coordinator', 'employer')

    Returns:
        list: List of user rows with the specified role
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            'SELECT id, username, email, full_name, role FROM users WHERE role = ? ORDER BY full_name',
            (role,)
        )
        return cursor.fetchall()
    finally:
        conn.close()


def get_coordinators():
    """
    Get all coordinators for dropdown selection.

    Returns:
        list: List of coordinator user rows
    """
    return get_users_by_role('coordinator')


def get_employers():
    """
    Get all employers for dropdown selection.

    Returns:
        list: List of employer user rows
    """
    return get_users_by_role('employer')


# ============ APPLICATION OPERATIONS ============

def create_application(user_id, full_name, student_id, email):
    """
    Create a new co-op application.

    Args:
        user_id: ID of the student submitting the application
        full_name: Applicant's full name
        student_id: Student ID (must be unique, 9 digits)
        email: Applicant's email

    Returns:
        int: The ID of the newly created application

    Raises:
        sqlite3.IntegrityError: If student_id already exists
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO applications (user_id, full_name, student_id, email)
            VALUES (?, ?, ?, ?)
        ''', (user_id, full_name, student_id, email))

        conn.commit()
        application_id = cursor.lastrowid
        return application_id
    finally:
        conn.close()


def check_duplicate_student_id(student_id):
    """
    Check if a student_id already exists in the applications table.

    Args:
        student_id: The student ID to check

    Returns:
        bool: True if duplicate exists, False otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            'SELECT COUNT(*) as count FROM applications WHERE student_id = ?',
            (student_id,)
        )
        result = cursor.fetchone()
        return result['count'] > 0
    finally:
        conn.close()


def get_application_by_user_id(user_id):
    """
    Get the application for a specific user.

    Args:
        user_id: The user ID

    Returns:
        sqlite3.Row: Application row if found, None otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT * FROM applications WHERE user_id = ?', (user_id,))
        return cursor.fetchone()
    finally:
        conn.close()


def get_all_applications():
    """
    Get all applications (for coordinator dashboard).

    Returns:
        list: List of all application rows
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT * FROM applications ORDER BY submitted_at DESC')
        return cursor.fetchall()
    finally:
        conn.close()


def get_applications_by_status(status):
    """
    Get applications filtered by status.

    Args:
        status: 'pending', 'accepted', or 'rejected'

    Returns:
        list: List of applications with the specified status
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            'SELECT * FROM applications WHERE status = ? ORDER BY submitted_at DESC',
            (status,)
        )
        return cursor.fetchall()
    finally:
        conn.close()


def update_application_status(application_id, status, coordinator_id):
    """
    Update the status of an application (approve or reject).

    Args:
        application_id: ID of the application to update
        status: New status ('accepted' or 'rejected')
        coordinator_id: ID of the coordinator making the decision

    Returns:
        bool: True if update was successful, False otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE applications
            SET status = ?, reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, coordinator_id, application_id))

        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# ============ REPORT OPERATIONS ============

def create_report(application_id, user_id, report_title, work_description,
                 hours_worked, supervisor_name, supervisor_email):
    """
    Create a new work report.

    Args:
        application_id: ID of the associated application
        user_id: ID of the student submitting the report
        report_title: Title of the report
        work_description: Description of work performed
        hours_worked: Number of hours worked
        supervisor_name: Name of supervisor
        supervisor_email: Email of supervisor

    Returns:
        int: The ID of the newly created report
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO reports (application_id, user_id, report_title, work_description,
                               hours_worked, supervisor_name, supervisor_email)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (application_id, user_id, report_title, work_description,
              hours_worked, supervisor_name, supervisor_email))

        conn.commit()
        report_id = cursor.lastrowid
        return report_id
    finally:
        conn.close()


def get_reports_by_user(user_id):
    """
    Get all reports submitted by a specific user.

    Args:
        user_id: The user ID

    Returns:
        list: List of report rows
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            'SELECT * FROM reports WHERE user_id = ? ORDER BY submitted_at DESC',
            (user_id,)
        )
        return cursor.fetchall()
    finally:
        conn.close()


def get_all_reports():
    """
    Get all reports (for coordinator to view).
    NOTE: This function is deprecated in favor of access-controlled report viewing.

    Returns:
        list: List of all report rows
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT * FROM reports ORDER BY submitted_at DESC')
        return cursor.fetchall()
    finally:
        conn.close()


def create_report_with_access(application_id, user_id, report_title, work_description,
                            hours_worked, supervisor_name, supervisor_email,
                            coordinator_ids, employer_ids):
    """
    Create a new work report and grant access to specified coordinators/employers in one transaction.

    Args:
        application_id: ID of the associated application
        user_id: ID of the student submitting the report
        report_title: Title of the report
        work_description: Description of work performed
        hours_worked: Number of hours worked
        supervisor_name: Name of supervisor
        supervisor_email: Email of supervisor
        coordinator_ids: List of coordinator user IDs to grant access to
        employer_ids: List of employer user IDs to grant access to

    Returns:
        int: The ID of the newly created report

    Raises:
        sqlite3.Error: If transaction fails
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Begin transaction
        cursor.execute('BEGIN TRANSACTION')

        # Create the report
        cursor.execute('''
            INSERT INTO reports (application_id, user_id, report_title, work_description,
                               hours_worked, supervisor_name, supervisor_email)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (application_id, user_id, report_title, work_description,
              hours_worked, supervisor_name, supervisor_email))

        report_id = cursor.lastrowid

        # Grant access to coordinators
        for coordinator_id in coordinator_ids:
            cursor.execute('''
                INSERT INTO report_access (report_id, user_id, access_type)
                VALUES (?, ?, ?)
            ''', (report_id, coordinator_id, 'coordinator'))

        # Grant access to employers
        for employer_id in employer_ids:
            cursor.execute('''
                INSERT INTO report_access (report_id, user_id, access_type)
                VALUES (?, ?, ?)
            ''', (report_id, employer_id, 'employer'))

        # Commit transaction
        conn.commit()
        return report_id
    except Exception as e:
        # Rollback on error
        conn.rollback()
        raise e
    finally:
        conn.close()


def grant_report_access(report_id, user_id, access_type):
    """
    Grant access to specific user for a report.

    Args:
        report_id: ID of the report
        user_id: ID of the user to grant access to
        access_type: 'coordinator' or 'employer'

    Returns:
        bool: True if access was granted, False if already existed
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT OR IGNORE INTO report_access (report_id, user_id, access_type)
            VALUES (?, ?, ?)
        ''', (report_id, user_id, access_type))

        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_reports_accessible_to_user(user_id, access_type):
    """
    Get all reports that a coordinator/employer has access to view.

    Args:
        user_id: ID of the coordinator/employer
        access_type: 'coordinator' or 'employer'

    Returns:
        list: List of report rows that the user can access
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT DISTINCT r.*, u.full_name as student_name, u.username as student_username
            FROM reports r
            INNER JOIN report_access ra ON r.id = ra.report_id
            INNER JOIN users u ON r.user_id = u.id
            WHERE ra.user_id = ? AND ra.access_type = ?
            ORDER BY r.submitted_at DESC
        ''', (user_id, access_type))
        return cursor.fetchall()
    finally:
        conn.close()


def get_report_with_access_check(report_id, user_id, access_type):
    """
    Get report details if user has access, otherwise return None.

    Args:
        report_id: ID of the report
        user_id: ID of the requesting user
        access_type: 'coordinator' or 'employer'

    Returns:
        sqlite3.Row: Report row if user has access, None otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT r.*, u.full_name as student_name, u.username as student_username
            FROM reports r
            INNER JOIN report_access ra ON r.id = ra.report_id
            INNER JOIN users u ON r.user_id = u.id
            WHERE r.id = ? AND ra.user_id = ? AND ra.access_type = ?
        ''', (report_id, user_id, access_type))
        return cursor.fetchone()
    finally:
        conn.close()


# ============ EVALUATION OPERATIONS ============

def create_evaluation(student_user_id, employer_user_id, application_id,
                     technical_skills, communication, professionalism,
                     overall_rating, comments):
    """
    Create a new student evaluation.

    Args:
        student_user_id: ID of the student being evaluated
        employer_user_id: ID of the employer submitting the evaluation
        application_id: ID of the associated application
        technical_skills: Rating 1-5
        communication: Rating 1-5
        professionalism: Rating 1-5
        overall_rating: Rating 1-5
        comments: Optional text comments

    Returns:
        int: The ID of the newly created evaluation
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO evaluations (student_user_id, employer_user_id, application_id,
                                   technical_skills, communication, professionalism,
                                   overall_rating, comments)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (student_user_id, employer_user_id, application_id, technical_skills,
              communication, professionalism, overall_rating, comments))

        conn.commit()
        evaluation_id = cursor.lastrowid
        return evaluation_id
    finally:
        conn.close()


def get_evaluations_for_student(student_user_id):
    """
    Get all evaluations for a specific student.

    Args:
        student_user_id: The student user ID

    Returns:
        list: List of evaluation rows
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            'SELECT * FROM evaluations WHERE student_user_id = ? ORDER BY submitted_at DESC',
            (student_user_id,)
        )
        return cursor.fetchall()
    finally:
        conn.close()


def get_all_evaluations():
    """
    Get all evaluations.

    Returns:
        list: List of all evaluation rows
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT * FROM evaluations ORDER BY submitted_at DESC')
        return cursor.fetchall()
    finally:
        conn.close()


def get_students_with_accepted_applications():
    """
    Get all students who have accepted applications (for employer to evaluate).

    Returns:
        list: List of user rows (students only) with accepted applications
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT DISTINCT u.* FROM users u
            INNER JOIN applications a ON u.id = a.user_id
            WHERE a.status = 'accepted'
            ORDER BY u.full_name
        ''')
        return cursor.fetchall()
    finally:
        conn.close()

if __name__ == '__main__':
    # Initialize database when run directly
    init_db()
    print("Database tables created successfully!")
