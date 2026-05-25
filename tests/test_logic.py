import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logic import is_stock_low, is_valid_medication, calculate_days_remaining

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