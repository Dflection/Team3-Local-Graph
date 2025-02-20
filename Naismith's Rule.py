def input_validation():
    """Ensures km is a positive float and elevation gain is a float."""

    def get_positive_float(prompt):
        """Gets a positive float input from the user with validation."""
        while True:
            try:
                value = float(input(prompt))
                if value > 0:
                    return value
                else:
                    print("Please enter a positive number.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    def get_float(prompt):
        """Gets a float input from the user with validation."""
        while True:
            try:
                value = float(input(prompt))
                return value
            except ValueError:
                print("Invalid input. Please enter a number.")

    km = get_positive_float("Kilometers?\n")
    elevation_gain = get_float("Elevation Gain?\n")
    return km, elevation_gain  # Return both values

def calculate_naismiths_time(distance_km, vertical_distance_m):
    """Calculates Naismith's Rule time in seconds. Metric.

    Args:
        distance_km: Distance in kilometers (float).
        vertical_distance_m: Elevation change in meters (float, positive or negative).

    Returns:
        Estimated time in seconds (float).
    """
    seconds = ((distance_km / 5) + (vertical_distance_m / 600)) * 3600  # Corrected!
    return seconds

km, elevation_gain = input_validation()  # Get validated inputs
seconds = calculate_naismiths_time(km, elevation_gain)
print(seconds)