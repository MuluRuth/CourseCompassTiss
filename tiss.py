import requests
import xml.etree.ElementTree as ET

BASE_URL = "https://tiss.tuwien.ac.at/api"

ORG_UNITS = ["E194", "E193", "E192", "E188", "E185"]

DOMAIN_MAP = {
    "machine learning": "Artificial Intelligence",
    "deep learning": "Artificial Intelligence",
    "artificial intelligence": "Artificial Intelligence",
    "neural": "Artificial Intelligence",
    "nlp": "Artificial Intelligence",
    "computer vision": "Artificial Intelligence",
    "recommender": "Artificial Intelligence",
    "software": "Software Engineering",
    "agile": "Software Engineering",
    "devops": "Software Engineering",
    "distributed": "Software Engineering",
    "testing": "Software Engineering",
    "cloud": "Software Engineering",
    "ethics": "Ethics and Society",
    "privacy": "Ethics and Society",
    "fairness": "Ethics and Society",
    "digital inclusion": "Ethics and Society",
    "sustainable": "Sustainable Engineering",
    "climate": "Sustainable Engineering",
    "green": "Sustainable Engineering",
    "energy": "Sustainable Engineering",
    "statistics": "Mathematics and Statistics",
    "econometrics": "Mathematics and Statistics",
    "linear algebra": "Mathematics and Statistics",
    "stochastic": "Mathematics and Statistics",
    "operations research": "Mathematics and Statistics",
    "signal": "Electrical Engineering",
    "embedded": "Electrical Engineering",
    "wireless": "Electrical Engineering",
    "data": "Data Science",
    "database": "Data Science",
    "visualization": "Data Science",
    "mining": "Data Science",
    "big data": "Data Science",
}

NS = {
    "c": "https://tiss.tuwien.ac.at/api/schemas/course/v10",
    "i": "https://tiss.tuwien.ac.at/api/schemas/i18n/v10",
    "c11": "https://tiss.tuwien.ac.at/api/schemas/course/v11",
}


def guess_domain(title, description=""):
    text = (title + " " + description).lower()
    for keyword, domain in DOMAIN_MAP.items():
        if keyword in text:
            return domain
    return "Data Science"


def parse_courses_from_xml(xml_text, semester="2025W"):
    courses = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        print(f"  XML parse error: {e}")
        return []

    sem_type = semester[-1]
    semester_label = "WS" if sem_type == "W" else "SS"

    course_elements = (
        root.findall(".//c:course", NS) or
        root.findall(".//c11:course", NS) or
        root.findall(".//{https://tiss.tuwien.ac.at/api/schemas/course/v10}course") or
        root.findall(".//{https://tiss.tuwien.ac.at/api/schemas/course/v11}course")
    )

    print(f"  Found {len(course_elements)} course elements in XML")

    for course_el in course_elements:
        number = course_el.get("courseNumber") or course_el.get("nr") or ""
        if not number:
            child = course_el.find(".//{https://tiss.tuwien.ac.at/api/schemas/course/v10}courseNumber")
            if child is not None and child.text:
                number = child.text.strip()
        if not number:
            continue

        name = ""
        title_el = course_el.find("c:title", NS)
        if title_el is not None:
            en = title_el.find("i:en", NS)
            de = title_el.find("i:de", NS)
            if en is not None and en.text:
                name = en.text.strip()
            elif de is not None and de.text:
                name = de.text.strip()
        if not name:
            name = course_el.get("title", number)

        ects_raw = course_el.get("ects", "3.0")
        try:
            ects = round(float(ects_raw), 1)
        except (ValueError, TypeError):
            ects = 3.0

        lang_raw = course_el.get("teachingLanguage", "German")
        language = "English" if "en" in str(lang_raw).lower() else "German"

        enroll_raw = course_el.get("maxParticipants", "50")
        try:
            enrollment = int(float(enroll_raw))
            if enrollment == 0:
                enrollment = 50
        except (ValueError, TypeError):
            enrollment = 50

        description = ""
        desc_el = course_el.find("c:description", NS)
        if desc_el is not None:
            en = desc_el.find("i:en", NS)
            de = desc_el.find("i:de", NS)
            if en is not None and en.text:
                description = en.text.strip()
            elif de is not None and de.text:
                description = de.text.strip()
        description = description[:120] + "..." if len(description) > 120 else description

        domain = guess_domain(name, description)

        courses.append({
            "id": number,
            "name": name,
            "ects": ects,
            "domain": domain,
            "difficulty": 2,
            "language": language,
            "semester": semester_label,
            "prerequisites": [],
            "programs": ["Business Informatics", "Computer Science"],
            "enrollment": enrollment,
            "description": description,
        })

    return courses


def get_courses_by_orgunit(org_code, semester="2025W"):
    url = f"{BASE_URL}/course/orgUnit/{org_code}"
    params = {"semester": semester}
    cookies = {"TISS_AUTH": "08057e41dbfbabd8f0696440338a0be557e8f69ff9a040e9f196c22747fe5d22"}

    try:
        response = requests.get(url, params=params, cookies=cookies, timeout=15)
        print(f"  Status: {response.status_code} | Size: {len(response.text)} chars")

        if response.status_code != 200 or not response.text.strip():
            return []

        return parse_courses_from_xml(response.text, semester)

    except requests.exceptions.RequestException as e:
        print(f"  Request error for {org_code}: {e}")
        return []


def fetch_all_courses(semester="2025W"):
    all_courses = []
    seen_ids = set()

    for org_code in ORG_UNITS:
        print(f"Fetching courses from org unit {org_code}...")
        raw_courses = get_courses_by_orgunit(org_code, semester)

        for course in raw_courses:
            cid = course.get("id", "")
            if cid and cid not in seen_ids:
                seen_ids.add(cid)
                all_courses.append(course)

    print(f"Total courses fetched: {len(all_courses)}")
    return all_courses