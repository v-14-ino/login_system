from database.db import get_db_connection

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Safely add 2FA columns if they don't exist
    try:
        import sqlite3
        cursor.execute("ALTER TABLE Users ADD COLUMN twofa_enabled INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE Users ADD COLUMN twofa_secret TEXT")
    except sqlite3.OperationalError:
        pass # Columns already exist

    # Safely add Phase 8 Security Suite columns
    try:
        cursor.execute("ALTER TABLE Users ADD COLUMN failed_attempts INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE Users ADD COLUMN lock_until TIMESTAMP")
        cursor.execute("ALTER TABLE Users ADD COLUMN trusted_fingerprint TEXT")
    except sqlite3.OperationalError:
        pass # Columns already exist

    # Create Login Logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            ip_address TEXT,
            browser TEXT,
            operating_system TEXT,
            login_status TEXT,
            login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
