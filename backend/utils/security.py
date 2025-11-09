"""
Security utilities for password validation and other security features.
"""
import re
from typing import Tuple
import secrets
import string

from app.config import settings


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validate password strength based on configured requirements.

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check minimum length
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long"

    # Check for uppercase letter
    if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"

    # Check for lowercase letter
    if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"

    # Check for digit
    if settings.PASSWORD_REQUIRE_DIGIT and not re.search(r'\d', password):
        return False, "Password must contain at least one digit"

    # Check for special character
    if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"

    # Check for common passwords (basic list)
    common_passwords = [
        "password", "123456", "12345678", "qwerty", "abc123",
        "monkey", "1234567", "letmein", "trustno1", "dragon",
        "baseball", "iloveyou", "master", "sunshine", "ashley",
        "bailey", "shadow", "superman", "qazwsx", "michael"
    ]

    if password.lower() in common_passwords:
        return False, "Password is too common. Please choose a more secure password"

    return True, ""


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.

    Args:
        length: Length of the token

    Returns:
        Random token string
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_api_key() -> str:
    """
    Generate a secure API key.

    Returns:
        API key string
    """
    return f"vf_{generate_secure_token(40)}"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent directory traversal and other attacks.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove any directory path components
    filename = filename.split('/')[-1].split('\\')[-1]

    # Remove or replace dangerous characters
    filename = re.sub(r'[^\w\s\-\.]', '', filename)

    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')

    return filename


def is_safe_url(url: str, allowed_hosts: list[str] = None) -> bool:
    """
    Check if a URL is safe for redirects.

    Args:
        url: URL to check
        allowed_hosts: List of allowed hostnames

    Returns:
        True if URL is safe, False otherwise
    """
    if not url:
        return False

    # Check for protocol-relative URLs
    if url.startswith('//'):
        return False

    # Check for absolute URLs
    if url.startswith('http://') or url.startswith('https://'):
        if allowed_hosts:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc in allowed_hosts
        return False

    # Relative URLs are safe
    return True


def sanitize_html(text: str) -> str:
    """
    Basic HTML sanitization to prevent XSS.

    Args:
        text: Text that may contain HTML

    Returns:
        Sanitized text
    """
    # Replace dangerous characters
    replacements = {
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        '/': '&#x2F;'
    }

    for char, replacement in replacements.items():
        text = text.replace(char, replacement)

    return text


def validate_email_format(email: str) -> bool:
    """
    Validate email format using regex.

    Args:
        email: Email address to validate

    Returns:
        True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """
    Mask sensitive data, showing only last few characters.

    Args:
        data: Data to mask
        visible_chars: Number of characters to show at the end

    Returns:
        Masked string
    """
    if len(data) <= visible_chars:
        return '*' * len(data)

    return '*' * (len(data) - visible_chars) + data[-visible_chars:]


def check_rate_limit_key(identifier: str, prefix: str = "rate_limit") -> str:
    """
    Generate a cache key for rate limiting.

    Args:
        identifier: Unique identifier (user_id, IP, etc.)
        prefix: Key prefix

    Returns:
        Cache key
    """
    return f"{prefix}:{identifier}"


def constant_time_compare(val1: str, val2: str) -> bool:
    """
    Perform constant-time string comparison to prevent timing attacks.

    Args:
        val1: First string
        val2: Second string

    Returns:
        True if strings are equal, False otherwise
    """
    if len(val1) != len(val2):
        return False

    result = 0
    for x, y in zip(val1, val2):
        result |= ord(x) ^ ord(y)

    return result == 0
