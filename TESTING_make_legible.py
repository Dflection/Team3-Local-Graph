def make_legible(minutes):
    """Converts a time duration given in decimal minutes to a more human-readable format of minutes and seconds.

    For example:
        1.76 minutes is converted to: 1 minute and 46 seconds.
        0.5 minutes is converted to: 0 minutes and 30 seconds.
        3.25 minutes is converted to: 3 minutes and 15 seconds.

    Args:
        minutes (float): A time duration in minutes, which may include a decimal portion.

    Returns:
        None. This function prints the time in a human-readable format to the console.

    """
    decimal_minutes = minutes % 1
    seconds = round(decimal_minutes * 60)
    real_minutes = int(minutes)
    if real_minutes == 1:
        print(f"The real time is: {real_minutes} minute and {seconds} seconds.")
    else:
        print(f"The real time is: {real_minutes} minutes and {seconds} seconds.")

make_legible(1.76)
