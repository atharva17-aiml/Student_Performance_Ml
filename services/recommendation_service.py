import logging


logging.basicConfig(level=logging.INFO)


def generate_recommendations(
    studytime,
    failures,
    absences,
    health,
    G1,
    G2,
    predicted_score
):
    """
    Generate personalized recommendations based on
    student inputs and ML prediction.

    Returns:
        list of dictionaries containing:
        title, message, priority
    """

    recommendations = []


    # ========================================================
    # PREDICTED SCORE
    # ========================================================

    if predicted_score < 8:

        recommendations.append({
            "title": "High Academic Risk",
            "message": (
                "Your predicted final score indicates that "
                "you may need immediate academic improvement. "
                "Focus on your weak subjects and consider "
                "additional academic support."
            ),
            "priority": "high"
        })

    elif predicted_score < 12:

        recommendations.append({
            "title": "Needs Improvement",
            "message": (
                "Your predicted score indicates that there "
                "is room for improvement. Increase your study "
                "consistency and revise important topics regularly."
            ),
            "priority": "medium"
        })

    elif predicted_score < 15:

        recommendations.append({
            "title": "Maintain Consistent Progress",
            "message": (
                "Your predicted performance is in the average "
                "range. Maintaining a consistent study routine "
                "can help you improve further."
            ),
            "priority": "medium"
        })

    elif predicted_score < 18:

        recommendations.append({
            "title": "Good Performance",
            "message": (
                "Your predicted performance is good. Continue "
                "your current study routine and focus on "
                "strengthening weaker subjects."
            ),
            "priority": "low"
        })

    else:

        recommendations.append({
            "title": "Excellent Performance",
            "message": (
                "Your predicted performance is excellent. "
                "Maintain your current academic routine and "
                "continue preparing consistently."
            ),
            "priority": "low"
        })


    # ========================================================
    # G2 — MOST IMPORTANT MODEL FEATURE
    # ========================================================

    if G2 < 10:

        recommendations.append({
            "title": "Focus on Current Academic Performance",
            "message": (
                f"Your G2 score is {G2}. Since G2 is the strongest "
                "predictive feature used by the model, improving "
                "your current academic performance should be "
                "your highest priority."
            ),
            "priority": "high"
        })

    elif G2 < 14:

        recommendations.append({
            "title": "Improve Your Current Score",
            "message": (
                f"Your G2 score is {G2}. Strengthening your "
                "current academic performance could improve "
                "your expected final result."
            ),
            "priority": "medium"
        })

    else:

        recommendations.append({
            "title": "Maintain Your Academic Performance",
            "message": (
                f"Your G2 score is {G2}, which indicates "
                "relatively strong current performance. "
                "Focus on maintaining this level."
            ),
            "priority": "low"
        })


    # ========================================================
    # ABSENCES
    # ========================================================

    if absences >= 20:

        recommendations.append({
            "title": "Reduce Absences",
            "message": (
                f"You have {absences} recorded absences. "
                "High absence levels may affect academic "
                "consistency. Try to attend classes regularly."
            ),
            "priority": "high"
        })

    elif absences >= 10:

        recommendations.append({
            "title": "Improve Attendance",
            "message": (
                f"You have {absences} absences. Maintaining "
                "better attendance can help you stay consistent "
                "with coursework."
            ),
            "priority": "medium"
        })

    else:

        recommendations.append({
            "title": "Good Attendance",
            "message": (
                f"Your absence count is {absences}. "
                "Continue maintaining regular attendance."
            ),
            "priority": "low"
        })


    # ========================================================
    # STUDY TIME
    # ========================================================

    if studytime <= 1:

        recommendations.append({
            "title": "Increase Study Time",
            "message": (
                "Your reported study time is low. Consider "
                "creating a structured daily study schedule "
                "and allocating additional time for revision."
            ),
            "priority": "high"
        })

    elif studytime == 2:

        recommendations.append({
            "title": "Strengthen Your Study Routine",
            "message": (
                "Your study time is moderate. A more consistent "
                "study schedule could help improve your academic "
                "performance."
            ),
            "priority": "medium"
        })

    else:

        recommendations.append({
            "title": "Maintain Your Study Routine",
            "message": (
                "Your reported study time is good. Continue "
                "maintaining a consistent study schedule."
            ),
            "priority": "low"
        })


    # ========================================================
    # FAILURES
    # ========================================================

    if failures >= 2:

        recommendations.append({
            "title": "Address Previous Failures",
            "message": (
                f"You have {failures} previous failures. "
                "Prioritize subjects where you have struggled "
                "and consider additional revision or academic "
                "support."
            ),
            "priority": "high"
        })

    elif failures == 1:

        recommendations.append({
            "title": "Review Previously Difficult Subjects",
            "message": (
                "You have one previous failure. Pay additional "
                "attention to subjects where you experienced "
                "difficulty."
            ),
            "priority": "medium"
        })

    else:

        recommendations.append({
            "title": "No Previous Failures",
            "message": (
                "You have no recorded previous failures. "
                "Continue maintaining your current academic habits."
            ),
            "priority": "low"
        })


    # ========================================================
    # HEALTH
    # ========================================================

    if health <= 2:

        recommendations.append({
            "title": "Take Care of Your Wellbeing",
            "message": (
                "Your reported health value is relatively low. "
                "Maintaining healthy routines and adequate rest "
                "can support consistent academic activity."
            ),
            "priority": "medium"
        })


    # ========================================================
    # G1 vs G2 TREND
    # ========================================================

    if G2 > G1:

        recommendations.append({
            "title": "Positive Academic Trend",
            "message": (
                f"Your G2 score ({G2}) is higher than your "
                f"G1 score ({G1}). Keep following the habits "
                "that helped you improve."
            ),
            "priority": "low"
        })

    elif G2 < G1:

        recommendations.append({
            "title": "Performance Has Declined",
            "message": (
                f"Your G2 score ({G2}) is lower than your "
                f"G1 score ({G1}). Review recent difficulties "
                "and focus on improving your weaker areas."
            ),
            "priority": "medium"
        })


    logging.info(
        f"Generated {len(recommendations)} "
        f"recommendations for prediction={predicted_score}"
    )


    return recommendations