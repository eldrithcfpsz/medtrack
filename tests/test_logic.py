import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logic import (
    is_stock_low,
    is_valid_medication,
    calculate_days_remaining,
    is_valid_password,
    MIN_PASSWORD_LENGTH,
    parse_dosage_mg,
    is_valid_dosage,
    MAX_NAME_LENGTH,
    MAX_DOSAGE_MG,
    MAX_DAILY_DOSES,
    ALLOWED_DOSAGES_MG,
)

def test_stock_is_low():
    assert is_stock_low(3) == True

def test_stock_is_not_low():
    assert is_stock_low(10) == False

def test_stock_exactly_five():
    assert is_stock_low(5) == False

def test_valid_medication():
    assert is_valid_medication('Aspirin', '500mg', '2', 10) == True

def test_missing_name():
    assert is_valid_medication('', '500mg', '2', 10) == False

def test_missing_dosage():
    assert is_valid_medication('Aspirin', '', '2', 10) == False

def test_negative_stock():
    assert is_valid_medication('Aspirin', '500mg', '2', -1) == False

def test_days_remaining_normal():
    assert calculate_days_remaining(10, 2) == 5

def test_days_remaining_zero_stock():
    assert calculate_days_remaining(0, 2) == 0

def test_days_remaining_once_a_day():
    assert calculate_days_remaining(7, 1) == 7

# --- additional edge cases ---

def test_stock_zero_is_low():
    assert is_stock_low(0) == True

def test_missing_frequency():
    assert is_valid_medication('Aspirin', '500mg', '', 10) == False

def test_zero_stock_is_valid():
    assert is_valid_medication('Aspirin', '500mg', '2', 0) == True

def test_valid_medication_accepts_string_stock():
    assert is_valid_medication('Aspirin', '500mg', '2', '10') == True

def test_days_remaining_rounds_down():
    assert calculate_days_remaining(10, 3) == 3

def test_days_remaining_zero_frequency():
    assert calculate_days_remaining(10, 0) == 0

def test_days_remaining_negative_frequency():
    assert calculate_days_remaining(10, -1) == 0

# --- password validation ---

def test_password_too_short_rejected():
    assert is_valid_password('1') == False

def test_password_just_below_minimum_rejected():
    assert is_valid_password('a' * (MIN_PASSWORD_LENGTH - 1)) == False

def test_password_at_minimum_accepted():
    assert is_valid_password('a' * MIN_PASSWORD_LENGTH) == True

def test_password_above_minimum_accepted():
    assert is_valid_password('a' * (MIN_PASSWORD_LENGTH + 5)) == True

def test_empty_password_rejected():
    assert is_valid_password('') == False

# --- dosage parsing ---

def test_parse_dosage_basic():
    assert parse_dosage_mg('500mg') == 500

def test_parse_dosage_plain_number():
    assert parse_dosage_mg('1000') == 1000

def test_parse_dosage_decimal():
    assert parse_dosage_mg('2.5mg') == 2.5

def test_parse_dosage_no_number_returns_none():
    assert parse_dosage_mg('mg') is None

# --- medication constraint: dosage <= 1000mg ---

def test_dosage_at_max_accepted():
    assert is_valid_medication('Aspirin', '1000mg', '2', 10) == True

def test_dosage_above_max_rejected():
    assert is_valid_medication('Aspirin', '1001mg', '2', 10) == False

def test_dosage_zero_rejected():
    assert is_valid_medication('Aspirin', '0mg', '2', 10) == False

def test_dosage_without_number_rejected():
    assert is_valid_medication('Aspirin', 'mg', '2', 10) == False

# --- medication constraint: only standard tablet strengths ---

def test_nonstandard_dosage_333_rejected():
    # 333mg is not a real tablet strength.
    assert is_valid_medication('Aspirin', '333mg', '2', 10) == False

def test_nonstandard_dosage_rejected_examples():
    for bad in ['7mg', '99mg', '321mg', '510mg']:
        assert is_valid_medication('Aspirin', bad, '2', 10) == False

def test_standard_dosages_accepted():
    for good in ['81mg', '325mg', '500mg', '1000mg']:
        assert is_valid_medication('Aspirin', good, '2', 10) == True

def test_is_valid_dosage_standard():
    assert is_valid_dosage('500mg') == True

def test_is_valid_dosage_nonstandard():
    assert is_valid_dosage('333mg') == False

def test_every_allowed_dosage_validates():
    for d in ALLOWED_DOSAGES_MG:
        assert is_valid_dosage(str(d) + 'mg') == True

# --- medication constraint: frequency 1..5 ---

def test_frequency_at_max_accepted():
    assert is_valid_medication('Aspirin', '500mg', str(MAX_DAILY_DOSES), 10) == True

def test_frequency_above_max_rejected():
    assert is_valid_medication('Aspirin', '500mg', '6', 10) == False

def test_frequency_zero_rejected():
    assert is_valid_medication('Aspirin', '500mg', '0', 10) == False

def test_frequency_non_numeric_rejected():
    assert is_valid_medication('Aspirin', '500mg', 'abc', 10) == False

# --- medication constraint: name length ---

def test_name_at_max_length_accepted():
    assert is_valid_medication('A' * MAX_NAME_LENGTH, '500mg', '2', 10) == True

def test_name_too_long_rejected():
    assert is_valid_medication('A' * (MAX_NAME_LENGTH + 1), '500mg', '2', 10) == False