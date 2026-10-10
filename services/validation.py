def validate_prediction_inputs(form):
    """
    Validate and convert student prediction inputs.

    Returns:
        list: [studytime, failures, absences, health, G1, G2]

    Raises:
        ValueError: If any input is missing, invalid, or outside
                    the allowed range.
    """

    rules = {
        "studytime": (1, 4),
        "failures": (0, 10),
        "absences": (0, 100),
        "health": (1, 5),
        "G1": (0, 20),
        "G2": (0, 20)
    }

    values = []

    for field, (min_v, max_v) in rules.items():

        # Check if field exists
        if field not in form:
            raise ValueError(
                f"Missing required field: {field}"
            )

        # Get and clean input
        raw_value = form.get(field, "").strip()

        if not raw_value:
            raise ValueError(
                f"{field} cannot be empty"
            )

        # Convert to integer
        try:
            value = int(raw_value)

        except (ValueError, TypeError):
            raise ValueError(
                f"{field} must be a valid number"
            )

        # Range validation
        if value < min_v or value > max_v:
            raise ValueError(
                f"{field} must be between {min_v} and {max_v}"
            )

        values.append(value)

    return values

def validate_password(password):
    """
    Validate password strength.

    Returns:
        tuple: (True, None) when valid
               (False, error_message) when invalid
    """

    if not password:
        return False, "Password cannot be empty."

    if len(password) < 8:
        return False, "Password must contain at least 8 characters."

    if not any(char.isupper() for char in password):
        return False, "Password must contain at least one uppercase letter."

    if not any(char.islower() for char in password):
        return False, "Password must contain at least one lowercase letter."

    if not any(char.isdigit() for char in password):
        return False, "Password must contain at least one number."

    return True, None