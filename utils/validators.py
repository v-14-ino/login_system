import re

def validate_username(username):
    if not username:
        return False
    # Only letters, numbers, underscore. Length 3 to 30.
    return re.match(r"^[a-zA-Z0-9_]{3,30}$", username) is not None

def validate_email(email):
    if not email:
        return False
    # Better email format validation
    return re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email) is not None

COMMON_PASSWORDS = {
    'password', 'password123', '12345678', '123456789', '1234567890',
    'qwerty', 'admin', 'admin123', 'letmein', 'welcome'
}

def validate_password(password):
    if not password:
        return False, "Password is required."
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if len(password) > 128:
        return False, "Password cannot exceed 128 characters."
    if " " in password:
        return False, "Password cannot contain spaces."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one numeric digit."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."
    if password.lower() in COMMON_PASSWORDS:
        return False, "Password is too common. Please choose a stronger password."
        
    return True, ""
