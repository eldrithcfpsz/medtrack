def is_stock_low(stock):
    return stock < 5

def is_valid_medication(name, dosage, frequency, stock):
    if not name or not dosage or not frequency:
        return False
    if int(stock) < 0:
        return False
    return True

def calculate_days_remaining(stock, frequency):
    doses_per_day = int(frequency)
    if doses_per_day <= 0:
        return 0
    return int(stock) // doses_per_day