import sqlite3
import os
import hashlib
from datetime import datetime
from contextlib import contextmanager

DATABASE_PATH = "case_management.db"

def get_password_hash(password):
    """Generate password hash"""
    return hashlib.sha256(password.encode()).hexdigest()

@contextmanager
def get_db_connection():
    """Database connection context manager"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    """Initialize database with tables and default data"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Cases table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT UNIQUE NOT NULL,
                lan TEXT NOT NULL,
                case_type TEXT NOT NULL,
                product TEXT NOT NULL,
                region TEXT NOT NULL,
                referred_by TEXT NOT NULL,
                case_description TEXT NOT NULL,
                case_date DATE NOT NULL,
                status TEXT DEFAULT 'Draft',
                created_by TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_by TEXT,
                reviewed_at TIMESTAMP,
                approved_by TEXT,
                approved_at TIMESTAMP,
                legal_reviewed_by TEXT,
                legal_reviewed_at TIMESTAMP,
                closed_by TEXT,
                closed_at TIMESTAMP,
                closure_reason TEXT,
                FOREIGN KEY (created_by) REFERENCES users (username)
            )
        ''')
        
        # Documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                uploaded_by TEXT NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (case_id) REFERENCES cases (case_id),
                FOREIGN KEY (uploaded_by) REFERENCES users (username)
            )
        ''')
        
        # Audit logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT,
                action TEXT NOT NULL,
                details TEXT,
                performed_by TEXT NOT NULL,
                performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (case_id) REFERENCES cases (case_id),
                FOREIGN KEY (performed_by) REFERENCES users (username)
            )
        ''')
        
        # Case comments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS case_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT NOT NULL,
                comment TEXT NOT NULL,
                comment_type TEXT DEFAULT 'General',
                created_by TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (case_id) REFERENCES cases (case_id),
                FOREIGN KEY (created_by) REFERENCES users (username)
            )
        ''')
        
        conn.commit()
        
        # Insert default users if they don't exist
        default_users = [
            ("admin", "admin123", "Admin", "admin@abcl.com"),
            ("initiator", "init123", "Initiator", "initiator@abcl.com"),
            ("reviewer", "review123", "Reviewer", "reviewer@abcl.com"),
            ("approver", "approve123", "Approver", "approver@abcl.com"),
            ("legal", "legal123", "Legal Reviewer", "legal@abcl.com"),
            ("closure", "closure123", "Action Closure Authority", "closure@abcl.com")
        ]
        
        for username, password, role, email in default_users:
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
            if cursor.fetchone()[0] == 0:
                password_hash = get_password_hash(password)
                cursor.execute(
                    "INSERT INTO users (username, password_hash, role, email) VALUES (?, ?, ?, ?)",
                    (username, password_hash, role, email)
                )
        
        conn.commit()

def log_audit(case_id, action, details, performed_by):
    """Log audit trail"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO audit_logs (case_id, action, details, performed_by) VALUES (?, ?, ?, ?)",
            (case_id, action, details, performed_by)
        )
        conn.commit()
