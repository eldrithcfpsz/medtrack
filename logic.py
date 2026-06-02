import re

def is_stock_low(stock):
    return stock < 5

MIN_PASSWORD_LENGTH = 8

def is_valid_password(password):
    if not password:
        return False
    return len(password) >= MIN_PASSWORD_LENGTH

# Medication input constraints
MAX_NAME_LENGTH = 50      # characters
MAX_DAILY_DOSES = 5       # doses per day

# Standard pharmaceutical tablet/capsule strengths in milligrams.
# Real medications only come in specific strengths, so an arbitrary value
# such as 333mg is not a valid dose. This list is the single source of truth
# for both the dropdown shown to users and server-side validation.
ALLOWED_DOSAGES_MG = [
    1, 2, 2.5, 4, 5, 10, 12.5, 20, 25, 40, 50, 60, 75, 80, 81, 90,
    100, 120, 125, 150, 160, 200, 250, 300, 325, 400, 500, 600, 650,
    750, 800, 850, 875, 1000,
]
MAX_DOSAGE_MG = max(ALLOWED_DOSAGES_MG)  # 1000

def parse_dosage_mg(dosage):
    """Extract the numeric milligram value from a dosage string like '500mg'.

    Returns the value as a float, or None if no number can be found.
    """
    if dosage is None:
        return None
    match = re.search(r'\d+(\.\d+)?', str(dosage))
    if not match:
        return None
    return float(match.group())

def is_valid_dosage(dosage):
    """A dosage is valid only if its mg value is a standard tablet strength."""
    dose = parse_dosage_mg(dosage)
    return dose is not None and dose in ALLOWED_DOSAGES_MG

def is_valid_medication(name, dosage, frequency, stock):
    # Required fields must be present.
    if not name or not dosage or not frequency:
        return False
    # Name length limit.
    if len(name) > MAX_NAME_LENGTH:
        return False
    # Dosage must be one of the standard strengths (no arbitrary values).
    if not is_valid_dosage(dosage):
        return False
    # Frequency must be a whole number between 1 and MAX_DAILY_DOSES.
    try:
        freq = int(frequency)
    except (ValueError, TypeError):
        return False
    if freq < 1 or freq > MAX_DAILY_DOSES:
        return False
    # Stock must be a non-negative whole number.
    try:
        if int(stock) < 0:
            return False
    except (ValueError, TypeError):
        return False
    return True

def calculate_days_remaining(stock, frequency):
    doses_per_day = int(frequency)
    if doses_per_day <= 0:
        return 0
    return int(stock) // doses_per_day