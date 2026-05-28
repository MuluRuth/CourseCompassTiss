def jaccard_similarity(set_a, set_b):
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


PROGRAM_DOMAINS = {
    "Business Informatics": [
        "Data Analytics", "Enterprise Engineering", "Economic Modeling",
        "Information Systems Engineering", "Management Science",
        "Research Methods",
    ],
    "Data Science": [
        "Data Analytics", "Information Systems Engineering",
        "Economic Modeling", "Enterprise Engineering",
    ],
    "Software Engineering": [
        "Information Systems Engineering", "Enterprise Engineering",
        "Data Analytics",
    ],
    "Logic and Artificial Intelligence": [
        "Data Analytics", "Information Systems Engineering",
        "Economic Modeling",
    ],
    "Media and Human-Centered Computing": [
        "Enterprise Engineering", "Data Analytics",
        "Information Systems Engineering",
    ],
    "Visual Computing": [
        "Data Analytics", "Information Systems Engineering",
        "Enterprise Engineering",
    ],
    "Embedded Computing Systems": [
        "Information Systems Engineering", "Data Analytics",
    ],
    "Computer Engineering": [
        "Information Systems Engineering", "Economic Modeling",
        "Data Analytics",
    ],
    "Quantum Information Science and Technology": [
        "Economic Modeling", "Information Systems Engineering",
        "Data Analytics",
    ],
}


def score_courses(courses, completed_ids, program, mode="deepen", extra_keywords=None):
    completed_courses = [c for c in courses if c["id"] in completed_ids]
    completed_domains = set(c["domain"] for c in completed_courses)

    completed_keywords = set(extra_keywords or [])
    for c in completed_courses:
        completed_keywords.update(c.get("keywords", []))

    program_domains = PROGRAM_DOMAINS.get(program, [])

    eligible_all = []
    locked = []
    for c in courses:
        if c["id"] in completed_ids:
            continue
        if c.get("domain") not in program_domains:
            continue
        unmet = [p for p in c.get("prerequisites", []) if p not in completed_ids]
        if unmet:
            locked.append({"course": c, "unmet": unmet})
        else:
            eligible_all.append(c)

    if not eligible_all:
        return [], locked

    has_history = len(completed_domains) > 0

    if has_history:
        if mode == "deepen":
            eligible = [c for c in eligible_all if c["domain"] in completed_domains]
            if not eligible:
                eligible = eligible_all
        else:
            eligible = [c for c in eligible_all if c["domain"] not in completed_domains]
            if not eligible:
                eligible = eligible_all
    else:
        primary = program_domains[:3]
        secondary = program_domains[3:]
        if mode == "deepen":
            eligible = [c for c in eligible_all if c["domain"] in primary and c.get("level") == "Foundation"]
            if not eligible:
                eligible = [c for c in eligible_all if c["domain"] in primary]
            if not eligible:
                eligible = eligible_all
        else:
            eligible = [c for c in eligible_all if c["domain"] in secondary and c.get("level") == "Foundation"]
            if not eligible:
                eligible = [c for c in eligible_all if c["domain"] in secondary]
            if not eligible:
                eligible = eligible_all

    scored = []
    for course in eligible:
        course_keywords = set(course.get("keywords", []))

        if completed_keywords and course_keywords:
            score = jaccard_similarity(completed_keywords, course_keywords)
        elif not completed_keywords:
            idx = program_domains.index(course["domain"]) if course["domain"] in program_domains else len(program_domains)
            score = max(0.1, 1.0 - (idx * 0.1))
        else:
            score = 0.2

        score = min(round(score, 4), 1.0)

        reasons = []
        shared = completed_keywords & course_keywords
        if not completed_ids and not extra_keywords:
            reasons.append(f"it is a core subject in the {program} program")
        elif shared:
            top = list(shared)[:3]
            reasons.append(f"it shares topics with your background: {', '.join(top)}")
        if mode == "deepen" and course["domain"] in completed_domains:
            reasons.append(f"it deepens your knowledge in {course['domain']}")
        elif mode == "explore" and course["domain"] not in completed_domains:
            reasons.append(f"it introduces you to {course['domain']}")
        if not reasons:
            reasons.append("it matches your academic profile")

        explanation = "Suggested because " + ", ".join(reasons) + "."
        scored.append({**course, "score": score, "explanation": explanation})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored, locked