def validate_prediction_inputs(form):
    """
    Validate and convert student prediction inputs from a form.

    Returns:
        list: [studytime, failures, absences, health, G1, G2]
    """

    required_fields = ["studytime", "failures", "absences", "health", "G1", "G2"]

    # ---------------- REQUIRED FIELD CHECK ----------------
    for field in required_fields:
        if field not in form or not form[field].strip():
            raise ValueError(f"{field} is required")

    # ---------------- CONVERT TO INTEGERS ----------------
    try:
        studytime = int(form["studytime"])
        failures  = int(form["failures"])
        absences  = int(form["absences"])
        health    = int(form["health"])
        G1        = int(form["G1"])
        G2        = int(form["G2"])

    except ValueError:
        raise ValueError("All inputs must be numeric values")

    # ---------------- RANGE VALIDATION ----------------
    if not (1 <= studytime <= 5):
        raise ValueError("Study time must be between 1 and 5")

    if not (0 <= failures <= 3):
        raise ValueError("Failures must be between 0 and 3")

    if not (0 <= absences <= 30):
        raise ValueError("Absences must be between 0 and 30")

    if not (1 <= health <= 5):
        raise ValueError("Health must be between 1 and 5")

    if not (0 <= G1 <= 20):
        raise ValueError("G1 must be between 0 and 20")

    if not (0 <= G2 <= 20):
        raise ValueError("G2 must be between 0 and 20")

    # ---------------- RETURN CLEAN VALUES ----------------
    return [studytime, failures, absences, health, G1, G2]