# Secure Login System - Phase 1

## Project Overview
This project is the final assignment for the Thiranex Cybersecurity Internship. The **Secure Login System** aims to demonstrate the development of a fully secure authentication application, incorporating industry-standard defensive measures against common web vulnerabilities.

## Objectives
- Develop a robust backend with Python and Flask.
- Implement an SQLite database connection.
- Design a modern, responsive, and visually appealing user interface with raw CSS.
- Lay the structural foundation for upcoming authentication and security features.

## Security Features Implemented
- bcrypt password hashing
- passwords never stored in plain text
- duplicate account prevention
- basic input validation

## Authentication
- bcrypt password verification
- secure credential checking
- generic login error messages to reduce information disclosure

## Session Management
- Flask sessions
- Protected routes
- Secure cookies
- Logout
- Automatic session handling

## Security Protections
- Input validation
- Parameterized SQL queries
- SQL Injection protection
- Secure error handling
- Email normalization
- Username validation

## Two-Factor Authentication
- TOTP authentication
- QR code setup
- Authenticator app support
- Additional login security

## Enterprise Security Features
- **Login Audit Logging**: Tracks successful and failed authentication attempts with IP, browser, and OS metadata.
- **Account Lockout**: Automatically locks an account for 15 minutes after 5 consecutive failed login attempts to prevent brute-force attacks.
- **Device Fingerprinting**: Generates a privacy-respecting client-side SHA-256 hash of device characteristics to detect and alert on anomalous logins.
- **Security Headers**: Enforces strict `Content-Security-Policy`, `X-Frame-Options`, `Strict-Transport-Security`, and more via response middleware.
- **Security Score**: A dynamic 0-100 metric calculating overall account health based on 2FA status, trusted devices, and active security mechanisms.
- **Security Alerts**: Real-time notifications on the dashboard regarding new devices or missing security protections.

## Folder Structure
```text
Secure-Login-System/
│
├── app.py
├── requirements.txt
├── README.md
├── database.db
│
├── database/
│     └── db.py
│
├── templates/
│     ├── index.html
│     └── about.html
│
├── static/
│     ├── css/
│     │      style.css
│     ├── js/
│     │      script.js
│     └── images/
```

## Technologies
- **Backend:** Python 3, Flask
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Database:** SQLite

## Installation

1. Clone or download the repository.
2. Create and activate a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running Flask

Start the Flask development server:
```bash
python app.py
```
Or use the flask command:
```bash
flask run --debug
```

Access the application in your browser at `http://127.0.0.1:5000`.

## Screenshot
![Screenshot Placeholder](#)

## Future Phases
Upcoming phases of this project will implement:
- Registration and Login functionality.
- Password Hashing & Salting.
- Session Management.
- Protection against SQL Injection, XSS, and CSRF.

*(Note: Phase 1 only contains the project foundation, styling, and database connection scaffolding. No authentication mechanisms are active in this phase.)*
