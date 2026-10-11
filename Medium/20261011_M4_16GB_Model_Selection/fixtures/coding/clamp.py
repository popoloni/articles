"""Deliberately faulty coding fixture. Do not copy this implementation into a product."""
def clamp(value, lower, upper):
    """Return value clipped into [lower, upper]; reversed bounds must raise ValueError."""
    return max(upper, min(lower, value))
