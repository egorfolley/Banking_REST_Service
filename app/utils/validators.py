import re
from datetime import date


def validate_password(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not re.search(r"[A-Z]", value):
        raise ValueError("Password must include an uppercase letter")
    if not re.search(r"[a-z]", value):
        raise ValueError("Password must include a lowercase letter")
    if not re.search(r"\d", value):
        raise ValueError("Password must include a digit")
    if not re.search(r"[^A-Za-z0-9]", value):
        raise ValueError("Password must include a special character")
    return value


def validate_ssn_last_four(value: str) -> str:
    if not re.fullmatch(r"\d{4}", value):
        raise ValueError("SSN last four must be 4 digits")
    return value


def validate_card_number(value: str) -> str:
    if not re.fullmatch(r"\d{12,19}", value):
        raise ValueError("Card number must be 12-19 digits")
    return value


def validate_expiry_month(value: int) -> int:
    if value < 1 or value > 12:
        raise ValueError("Expiry month must be between 1 and 12")
    return value


def validate_expiry_year(value: int) -> int:
    current_year = date.today().year
    if value < current_year:
        raise ValueError("Expiry year must be current year or later")
    return value
