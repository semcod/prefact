"""Sample code for demonstrating output formats."""


def process_data(data):
    """Process some data."""
    result = "Processed: " + str(data)
    print("Debug: processing data")
    return result


def calculate_sum(numbers):
    """Calculate sum of numbers."""
    total = 0
    for num in numbers:
        total += num
    print("Total is: " + str(total))
    return total
