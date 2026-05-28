def score_courses(courses, completed_ids, program, mode="default"):
    """
    Content-Based Recommender scoring.

    Relevance mode:  S = C
    Diversity mode:  S = 0.4*C + 0.6*D

    C = content match (domain overlap with completed courses)
    D = diversity bonus (rewards domains not yet explored)

    Cold start (no completed courses):
      C = 1.0 if course domain matches program primary domains
      C = 0.3 otherwise
    """

    PROGRAM_DOMAINS = {
        "Business Informatics": ["Data Analytics", "Management Science", "Economic Modeling", "Information Systems Engineering"],
        "Data Science": ["Data Analytics", "Artificial Intelligence", "Mathematics and Statistics"],
        "Software Engineering": ["Software Engineering", "Information Systems Engineering", "Artificial Intelligence"],
        "Logic and Artificial Intelligence": ["Artificial Intelligence", "Mathematics and Statistics"],
        "Media and Human-Centered Computing": ["Ethics and Society", "Software Engineering", "Data Analytics"],
        "Visual Computing": ["Artificial Intelligence", "Data Analytics", "Electrical Engineering"],
        "Embedded Computing Systems": ["Electrical Engineering", "Software Engineering"],
        "Computer Engineering": ["Electrical Engineering", "Mathematics and Statistics"],
        "Quantum Information Science and Technology": ["Mathematics and Statistics", "Electrical Engineering"],
    }

    completed_courses = [c for c in courses if c["id"] in completed_ids]
    completed_domains = set(c["domain"] for c in completed_courses)

    # filter: remove completed and courses with unmet prerequisites
    eligible = []
    locked = []
    for c in courses:
        if c["id"] in completed_ids:
            continue
        unmet = [p for p in c.get("prerequisites", []) if p not in completed_ids]
        if unmet:
            locked.append({"course": c, "unmet": unmet})
        else:
            eligible.append(c)

    if not eligible:
        return [], locked

    program_domains = PROGRAM_DOMAINS.get(program, [])
    scored = []

    for course in eligible:
        if not completed_domains:
            C = 1.0 if course["domain"] in program_domains else 0.3
        else:
            C = 1.0 if course["domain"] in completed_domains else 0.2

        D = 1.0 if (completed_domains and course["domain"] not in completed_domains) else 0.2

        if mode == "default":
            score = C
        else:
            score = 0.4 * C + 0.6 * D

        score = min(round(score, 4), 1.0)

        reasons = []
        if not completed_domains:
            if course["domain"] in program_domains:
                reasons.append(f"it is relevant to the {program} program")
            else:
                reasons.append("it broadens your academic profile")
        else:
            if course["domain"] in completed_domains:
                reasons.append(f"it builds on your background in {course['domain']}")
            elif mode == "diversity":
                reasons.append(f"it expands your knowledge into {course['domain']}")

        if not reasons:
            reasons.append("it matches your academic profile")

        explanation = "Suggested because " + ", ".join(reasons) + "."
        scored.append({**course, "score": score, "explanation": explanation})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored, locked
