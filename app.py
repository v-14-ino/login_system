import datetime
from datetime import timedelta
import pyotp
import qrcode
import io
import base64
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
from database.db import get_db_connection
from database.init_db import init_db
from utils.validators import validate_username, validate_email, validate_password

app = Flask(__name__)
app.secret_key = 'super-secret-key-phase2'
app.permanent_session_lifetime = datetime.timedelta(minutes=30)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_REFRESH_EACH_REQUEST'] = True
# TODO: Enable SESSION_COOKIE_SECURE = True when deploying over HTTPS in production

bcrypt = Bcrypt(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not username or not email or not password or not confirm_password:
            flash('All fields are required.', 'error')
            return redirect(url_for('register'))

        if not validate_username(username):
            flash('Username contains invalid characters.', 'error')
            return redirect(url_for('register'))

        if not validate_email(email):
            flash('Invalid email format.', 'error')
            return redirect(url_for('register'))

        is_valid_pwd, pwd_msg = validate_password(password)
        if not is_valid_pwd:
            flash(pwd_msg, 'error')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if username exists (parameterized query)
            user = cursor.execute('SELECT id FROM Users WHERE username = ?', (username,)).fetchone()
            if user:
                flash('Username already exists.', 'error')
                conn.close()
                return redirect(url_for('register'))

            # Check if email exists (parameterized query)
            user = cursor.execute('SELECT id FROM Users WHERE email = ?', (email,)).fetchone()
            if user:
                flash('Email already exists.', 'error')
                conn.close()
                return redirect(url_for('register'))

            # Hash the password using bcrypt and decode to utf-8 string for storage
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

            # Insert user (password stored as bcrypt hash, parameterized query)
            cursor.execute(
                'INSERT INTO Users (username, email, password) VALUES (?, ?, ?)',
                (username, email, hashed_password)
            )
            conn.commit()
            conn.close()

            flash('Registration successful.', 'success')
            return redirect(url_for('register'))
        except Exception as e:
            # Handle DB errors gracefully without exposing internals
            flash('An unexpected error occurred. Please try again.', 'error')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        fingerprint = request.form.get('fingerprint', '')

        if not email or not password:
            flash('All fields are required.', 'error')
            return redirect(url_for('login'))
            
        if not validate_email(email):
            flash('Invalid email format.', 'error')
            return redirect(url_for('login'))

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            user = cursor.execute('SELECT * FROM Users WHERE email = ?', (email,)).fetchone()
            
            if user:
                # Check account lockout
                if user['lock_until']:
                    lock_time_str = str(user['lock_until'])
                    if '.' in lock_time_str:
                        lock_time = datetime.datetime.strptime(lock_time_str, '%Y-%m-%d %H:%M:%S.%f')
                    else:
                        lock_time = datetime.datetime.strptime(lock_time_str, '%Y-%m-%d %H:%M:%S')
                        
                    if lock_time > datetime.datetime.now():
                        flash('Account temporarily locked due to multiple failed login attempts.', 'error')
                        conn.close()
                        return redirect(url_for('login'))

                if bcrypt.check_password_hash(user['password'], password):
                    # Reset lockout
                    cursor.execute('UPDATE Users SET failed_attempts = 0, lock_until = NULL WHERE id = ?', (user['id'],))
                    
                    # Device Fingerprinting
                    trusted_fingerprint = user['trusted_fingerprint']
                    if not trusted_fingerprint:
                        cursor.execute('UPDATE Users SET trusted_fingerprint = ? WHERE id = ?', (fingerprint, user['id']))
                        session['new_device'] = False
                    elif trusted_fingerprint != fingerprint:
                        session['new_device'] = True
                    else:
                        session['new_device'] = False
                        
                    conn.commit()
                    log_login_attempt(user['id'], user['username'], 'Success')

                    if user['twofa_enabled'] == 1:
                        session['2fa_user_id'] = user['id']
                        session['2fa_username'] = user['username']
                        session['2fa_email'] = user['email']
                        conn.close()
                        return redirect(url_for('verify_2fa'))
                    else:
                        session.permanent = True
                        session['user_id'] = user['id']
                        session['username'] = user['username']
                        session['email'] = user['email']
                        session['logged_in'] = True
                        flash('Login successful.', 'success')
                        conn.close()
                        return redirect(url_for('dashboard'))
                else:
                    # Login failed
                    failed_attempts = (user['failed_attempts'] or 0) + 1
                    if failed_attempts >= 5:
                        lock_until = datetime.datetime.now() + timedelta(minutes=15)
                        cursor.execute('UPDATE Users SET failed_attempts = ?, lock_until = ? WHERE id = ?', (failed_attempts, lock_until, user['id']))
                    else:
                        cursor.execute('UPDATE Users SET failed_attempts = ? WHERE id = ?', (failed_attempts, user['id']))
                    conn.commit()
                    log_login_attempt(user['id'], user['username'], 'Failed')
            else:
                log_login_attempt(None, email, 'Failed')

            conn.close()
            flash('Invalid email or password.', 'error')
            return redirect(url_for('login'))
        except Exception as e:
            import traceback
            traceback.print_exc()
            flash(f'Error during login: {str(e)}', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa():
    if '2fa_user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        code = request.form.get('totp_code', '').strip()
        user_id = session['2fa_user_id']
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            user = cursor.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()
            conn.close()

            if user and user['twofa_secret']:
                totp = pyotp.TOTP(user['twofa_secret'])
                if totp.verify(code):
                    session.permanent = True
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['email'] = user['email']
                    session['logged_in'] = True
                    
                    session.pop('2fa_user_id', None)
                    session.pop('2fa_username', None)
                    session.pop('2fa_email', None)

                    flash('Verification successful.', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Invalid verification code.', 'error')
            else:
                flash('Authentication failed.', 'error')
        except Exception as e:
            flash('An unexpected error occurred. Please try again.', 'error')

    return render_template('verify_2fa.html')

@app.route('/setup-2fa', methods=['GET', 'POST'])
def setup_2fa():
    if not session.get('logged_in'):
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        code = request.form.get('totp_code', '').strip()
        secret = session.get('setup_2fa_secret')
        
        if not secret:
            flash('QR setup failed. Please try again.', 'error')
            return redirect(url_for('setup_2fa'))

        totp = pyotp.TOTP(secret)
        if totp.verify(code):
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('UPDATE Users SET twofa_enabled = 1, twofa_secret = ? WHERE id = ?', (secret, session['user_id']))
                conn.commit()
                conn.close()
                session.pop('setup_2fa_secret', None)
                flash('Two-Factor Authentication enabled.', 'success')
                return redirect(url_for('dashboard'))
            except Exception as e:
                flash('An unexpected error occurred. Please try again.', 'error')
        else:
            flash('Invalid verification code.', 'error')
            
    secret = pyotp.random_base32()
    session['setup_2fa_secret'] = secret
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(name=session['email'], issuer_name="Secure Login System")
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    qr_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    return render_template('setup_2fa.html', qr_b64=qr_b64)

def log_login_attempt(user_id, username, status):
    ip_address = request.remote_addr or 'Unknown'
    browser = getattr(request.user_agent, 'browser', None) or 'Unknown'
    os = getattr(request.user_agent, 'platform', None) or 'Unknown'
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO login_logs (user_id, username, ip_address, browser, operating_system, login_status) VALUES (?, ?, ?, ?, ?, ?)',
            (user_id, username, ip_address, browser, os, status)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        app.logger.error(f'Error logging login attempt: {e}')

@app.route('/disable-2fa', methods=['POST'])
def disable_2fa():
    if not session.get('logged_in'):
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE Users SET twofa_enabled = 0, twofa_secret = NULL WHERE id = ?', (session['user_id'],))
        conn.commit()
        conn.close()
        flash('Two-Factor Authentication disabled.', 'success')
    except Exception as e:
        app.logger.error(f'Error disabling 2FA: {e}')
        flash('An unexpected error occurred. Please try again.', 'error')
        
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        flash('Please login first.', 'error')
        return redirect(url_for('login'))
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        user = cursor.execute('SELECT * FROM Users WHERE id = ?', (session['user_id'],)).fetchone()
        
        # Get login logs
        logs = cursor.execute('SELECT * FROM login_logs WHERE user_id = ? ORDER BY login_time DESC LIMIT 10', (session['user_id'],)).fetchall()
        conn.close()
        
        twofa_enabled = user['twofa_enabled'] if user else 0
        
        # Calculate Security Score
        score = 0
        score += 20 # Password Hashing
        score += 15 # Session Active
        score += 20 # SQLi protected
        score += 10 # Security Headers
        if twofa_enabled:
            score += 20
        if not session.get('new_device', False):
            score += 15
            
        session_info = {
            'ip': request.remote_addr,
            'browser': request.user_agent.browser or 'Unknown',
            'os': request.user_agent.platform or 'Unknown',
            'new_device': session.get('new_device', False)
        }
        
    except Exception as e:
        twofa_enabled = 0
        score = 0
        logs = []
        session_info = {}

    return render_template('dashboard.html', twofa_enabled=twofa_enabled, score=score, logs=logs, session_info=session_info)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Initialize the database and create tables if they don't exist
    init_db()
    app.run(debug=True)
