from datetime import datetime as dt

from jgutils import utils as utl


def test_last_day_of_period():
    # Test cases
    test_cases = [
        (dt(2023, 1, 1), 'W', dt(2023, 1, 1)),
        (dt(2023, 12, 26), 'W', dt(2023, 12, 31)),

        (dt(2023, 1, 15), 'M', dt(2023, 1, 31)),
        (dt(2023, 12, 31), 'M', dt(2023, 12, 31)),
        (dt(2023, 11, 1), 'M', dt(2023, 11, 30)),

        (dt(2023, 1, 1), 'Y', dt(2023, 12, 31)),
        (dt(2023, 1, 15), 'Y', dt(2023, 12, 31)),
        (dt(2023, 12, 31), 'Y', dt(2023, 12, 31)),
    ]

    for input_date, freq, expected in test_cases:
        result = utl.last_day_of_period(input_date, freq)
        assert result == expected, f'{input_date} with freq "{freq}". Expected {expected}, got {result}.'
