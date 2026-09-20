"""Example with print statements (flagged only)."""


def process_data(data):
    """Process data with debug prints."""
    print("Starting processing")
    doubled = data * 2
    print(f"Result: {doubled}")
    return doubled


def calculate(a, b):
    """Calculate with debug output."""
    print(f"Calculating {a} + {b}")
    return a + b
