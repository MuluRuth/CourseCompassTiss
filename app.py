from flask import Flask, jsonify, request, render_template
from recommender import score_courses
from tiss import fetch_all_courses
import json
import os

app = Flask(__name__)

COURSES = []
CACHE_FILE = "courses_cache.json"

PROGRAMS = [
    "Business Informatics",
    "Data Science",
    "Software Engineering",
    "Logic and Artificial Intelligence",
    "Media and Human-Centered Computing",
    "Visual Computing",
    "Embedded Computing Systems",
    "Computer Engineering",
    "Quantum Information Science and Technology",
]

# ── Mock course catalog with 4-level structure ────────────────────────────
# Foundation → Core → Extension per domain
# Each domain follows: FD (no prereqs) → COR (requires FD) → EXT (requires COR)

MOCK_COURSES = [
    # ── Data Analytics ──────────────────────────────────────────────────
    {
        "id": "DA-FD", "name": "Data Analytics Foundation",
        "ects": 6.0, "domain": "Data Analytics", "level": "Foundation",
        "language": "English", "semester": "WS", "prerequisites": [],
        "description": "Foundations of data analysis, business intelligence, data warehousing and data mining.",
        "enrollment": 120,
    },
    {
        "id": "DA-COR", "name": "Data Analytics Core",
        "ects": 12.0, "domain": "Data Analytics", "level": "Core",
        "language": "English", "semester": "SS", "prerequisites": ["DA-FD"],
        "description": "Multivariate analysis, clustering, visualization, and computational thinking.",
        "enrollment": 90,
    },
    {
        "id": "DA-EXT", "name": "Data Analytics Extension",
        "ects": 12.0, "domain": "Data Analytics", "level": "Extension",
        "language": "English", "semester": "WS", "prerequisites": ["DA-COR"],
        "description": "Advanced topics in data analytics deepening core competencies.",
        "enrollment": 60,
    },

    # ── Enterprise Engineering ───────────────────────────────────────────
    {
        "id": "EE-FD", "name": "Enterprise Engineering Foundation",
        "ects": 6.0, "domain": "Enterprise Engineering", "level": "Foundation",
        "language": "English", "semester": "WS", "prerequisites": [],
        "description": "Enterprise architecture, business process management, and model-driven engineering.",
        "enrollment": 110,
    },
    {
        "id": "EE-COR", "name": "Enterprise Engineering Core",
        "ects": 12.0, "domain": "Enterprise Engineering", "level": "Core",
        "language": "English", "semester": "SS", "prerequisites": ["EE-FD"],
        "description": "E-commerce, recommender systems, and social network analysis.",
        "enrollment": 85,
    },
    {
        "id": "EE-EXT", "name": "Enterprise Engineering Extension",
        "ects": 12.0, "domain": "Enterprise Engineering", "level": "Extension",
        "language": "English", "semester": "WS", "prerequisites": ["EE-COR"],
        "description": "Advanced enterprise engineering topics and digital business models.",
        "enrollment": 55,
    },

    # ── Economic Modeling ────────────────────────────────────────────────
    {
        "id": "EM-FD", "name": "Economic Modeling Foundation",
        "ects": 6.0, "domain": "Economic Modeling", "level": "Foundation",
        "language": "English", "semester": "WS", "prerequisites": [],
        "description": "Econometric methods and computer simulation techniques.",
        "enrollment": 100,
    },
    {
        "id": "EM-COR", "name": "Economic Modeling Core",
        "ects": 12.0, "domain": "Economic Modeling", "level": "Core",
        "language": "English", "semester": "SS", "prerequisites": ["EM-FD"],
        "description": "Simulation methods, macroeconomic modeling and international trade theory.",
        "enrollment": 75,
    },
    {
        "id": "EM-EXT", "name": "Economic Modeling Extension",
        "ects": 12.0, "domain": "Economic Modeling", "level": "Extension",
        "language": "English", "semester": "WS", "prerequisites": ["EM-COR"],
        "description": "Advanced economic modeling and applied simulations.",
        "enrollment": 45,
    },

    # ── Information Systems Engineering ──────────────────────────────────
    {
        "id": "ISE-FD", "name": "Information Systems Engineering Foundation",
        "ects": 6.0, "domain": "Information Systems Engineering", "level": "Foundation",
        "language": "English", "semester": "WS", "prerequisites": [],
        "description": "Models, modeling languages, transformations and model management.",
        "enrollment": 115,
    },
    {
        "id": "ISE-COR", "name": "Information Systems Engineering Core",
        "ects": 12.0, "domain": "Information Systems Engineering", "level": "Core",
        "language": "English", "semester": "SS", "prerequisites": ["ISE-FD"],
        "description": "Data-intensive, distributed and semantic web systems.",
        "enrollment": 88,
    },
    {
        "id": "ISE-EXT", "name": "Information Systems Engineering Extension",
        "ects": 12.0, "domain": "Information Systems Engineering", "level": "Extension",
        "language": "English", "semester": "WS", "prerequisites": ["ISE-COR"],
        "description": "Advanced information systems topics.",
        "enrollment": 52,
    },

    # ── Management Science ───────────────────────────────────────────────
    {
        "id": "MS-FD", "name": "Management Science Foundation",
        "ects": 6.0, "domain": "Management Science", "level": "Foundation",
        "language": "English", "semester": "WS", "prerequisites": [],
        "description": "Managing complex socio-technical systems, IT management and leadership.",
        "enrollment": 105,
    },
    {
        "id": "MS-COR", "name": "Management Science Core",
        "ects": 12.0, "domain": "Management Science", "level": "Core",
        "language": "English", "semester": "SS", "prerequisites": ["MS-FD"],
        "description": "Digitalized work systems, project finance and organizational behavior.",
        "enrollment": 80,
    },
    {
        "id": "MS-EXT", "name": "Management Science Extension",
        "ects": 12.0, "domain": "Management Science", "level": "Extension",
        "language": "English", "semester": "WS", "prerequisites": ["MS-COR"],
        "description": "Advanced management science and digital organization topics.",
        "enrollment": 50,
    },

    # ── Artificial Intelligence ──────────────────────────────────────────
    {
        "id": "AI-FD", "name": "Artificial Intelligence Foundation",
        "ects": 4.5, "domain": "Artificial Intelligence", "level": "Foundation",
        "language": "English", "semester": "WS", "prerequisites": [],
        "description": "Introduction to AI, search algorithms, logic and knowledge representation.",
        "enrollment": 180,
    },
    {
        "id": "AI-COR", "name": "Machine Learning Core",
        "ects": 4.5, "domain": "Artificial Intelligence", "level": "Core",
        "language": "English", "semester": "SS", "prerequisites": ["AI-FD"],
        "description": "Supervised and unsupervised learning, model evaluation and practical applications.",
        "enrollment": 140,
    },
    {
        "id": "AI-EXT1", "name": "Deep Learning Extension",
        "ects": 4.5, "domain": "Artificial Intelligence", "level": "Extension",
        "language": "English", "semester": "WS", "prerequisites": ["AI-COR"],
        "description": "Neural networks, CNNs, RNNs, transformers and deep learning applications.",
        "enrollment": 110,
    },
    {
        "id": "AI-EXT2", "name": "Natural Language Processing Extension",
        "ects": 3.0, "domain": "Artificial Intelligence", "level": "Extension",
        "language": "English", "semester": "SS", "prerequisites": ["AI-COR"],
        "description": "Text processing, language models and NLP pipelines.",
        "enrollment": 85,
    },
    {
        "id": "AI-EXT3", "name": "Recommender Systems Extension",
        "ects": 3.0, "domain": "Artificial Intelligence", "level": "Extension",
        "language": "English", "semester": "SS", "prerequisites": ["AI-COR"],
        "description": "Collaborative filtering, content-based and hybrid recommendation approaches.",
        "enrollment": 75,
    },

    # ── Software Engineering ─────────────────────────────────────────────
    {
        "id": "SE-FD", "name": "Software Engineering Foundation",
        "ects": 4.5, "domain": "Software Engineering", "level": "Foundation",
        "language": "English", "semester": "WS", "prerequisites": [],
        "description": "Software architecture, design patterns and quality attributes.",
        "enrollment": 160,
    },
    {
        "id": "SE-COR", "name": "Software Engineering Core",
        "ects": 4.5, "domain": "Software Engineering", "level": "Core",
        "language": "English", "semester": "SS", "prerequisites": ["SE-FD"],
        "description": "Agile methods, testing, DevOps and CI/CD pipelines.",
        "enrollment": 130,
    },
    {
        "id": "SE-EXT1", "name": "Distributed Systems Extension",
        "ects": 4.5, "domain": "Software Engineering", "level": "Extension",
        "language": "English", "semester": "WS", "prerequisites": ["SE-COR"],
        "description": "Consistency models, consensus algorithms and distributed architectures.",
        "enrollment": 95,
    },
    {
        "id": "SE-EXT2", "name": "Cloud Computing Extension",
        "ects": 4.5, "domain": "Software Engineering", "level": "Extension",
        "language": "English", "semester": "SS", "prerequisites": ["SE-COR"],
        "description": "AWS, Azure, GCP, serverless computing and microservices.",
        "enrollment": 120,
    },

    # ── Mathematics and Statistics ───────────────────────────────────────
    {
        "id": "MATH-FD", "name": "Mathematics and Statistics Foundation",
        "ects": 4.5, "domain": "Mathematics and Statistics", "level": "Foundation",
        "language": "English", "semester": "WS", "prerequisites": [],
        "description": "Linear algebra, probability theory and statistical inference.",
        "enrollment": 155,
    },
    {
        "id": "MATH-COR", "name": "Applied Statistics Core",
        "ects": 4.5, "domain": "Mathematics and Statistics", "level": "Core",
        "language": "English", "semester": "SS", "prerequisites": ["MATH-FD"],
        "description": "Regression analysis, hypothesis testing and multivariate statistics.",
        "enrollment": 115,
    },
    {
        "id": "MATH-EXT1", "name": "Econometrics Extension",
        "ects": 4.5, "domain": "Mathematics and Statistics", "level": "Extension",
        "language": "English", "semester": "SS", "prerequisites": ["MATH-COR"],
        "description": "Time series, panel data, causal inference and economic models.",
        "enrollment": 80,
    },
    {
        "id": "MATH-EXT2", "name": "Operations Research Extension",
        "ects": 4.5, "domain": "Mathematics and Statistics", "level": "Extension",
        "language": "English", "semester": "WS", "prerequisites": ["MATH-COR"],
        "description": "Linear programming, optimization and decision theory.",
        "enrollment": 65,
    },

    # ── Ethics and Society ───────────────────────────────────────────────
    {
        "id": "ETH-FD", "name": "Ethics and Society Foundation",
        "ects": 3.0, "domain": "Ethics and Society", "level": "Foundation",
        "language": "English", "semester": "WS+SS", "prerequisites": [],
        "description": "Ethical frameworks for technology, privacy and digital rights.",
        "enrollment": 90,
    },
    {
        "id": "ETH-COR", "name": "AI Ethics and Fairness Core",
        "ects": 3.0, "domain": "Ethics and Society", "level": "Core",
        "language": "English", "semester": "WS", "prerequisites": ["ETH-FD"],
        "description": "Bias, fairness, accountability and transparency in AI systems.",
        "enrollment": 70,
    },
    {
        "id": "ETH-EXT", "name": "Digital Inclusion Extension",
        "ects": 3.0, "domain": "Ethics and Society", "level": "Extension",
        "language": "English", "semester": "SS", "prerequisites": ["ETH-COR"],
        "description": "Accessibility, digital literacy and reducing technology-based inequalities.",
        "enrollment": 45,
    },

    # ── Sustainable Engineering ──────────────────────────────────────────
    {
        "id": "SU-FD", "name": "Sustainable Engineering Foundation",
        "ects": 3.0, "domain": "Sustainable Engineering", "level": "Foundation",
        "language": "English", "semester": "WS", "prerequisites": [],
        "description": "Life cycle assessment, circular economy and green engineering principles.",
        "enrollment": 75,
    },
    {
        "id": "SU-COR", "name": "Climate Informatics Core",
        "ects": 3.0, "domain": "Sustainable Engineering", "level": "Core",
        "language": "English", "semester": "SS", "prerequisites": ["SU-FD"],
        "description": "Data-driven approaches to climate change and sustainability.",
        "enrollment": 55,
    },
    {
        "id": "SU-EXT", "name": "Energy Systems Modeling Extension",
        "ects": 4.5, "domain": "Sustainable Engineering", "level": "Extension",
        "language": "English", "semester": "WS", "prerequisites": ["SU-COR"],
        "description": "Renewable energy systems, smart grids and energy modeling.",
        "enrollment": 35,
    },

    # ── Electrical Engineering ───────────────────────────────────────────
    {
        "id": "EE2-FD", "name": "Electrical Engineering Foundation",
        "ects": 4.5, "domain": "Electrical Engineering", "level": "Foundation",
        "language": "English", "semester": "WS", "prerequisites": [],
        "description": "Circuits, signals and systems fundamentals.",
        "enrollment": 95,
    },
    {
        "id": "EE2-COR", "name": "Signal Processing Core",
        "ects": 4.5, "domain": "Electrical Engineering", "level": "Core",
        "language": "English", "semester": "SS", "prerequisites": ["EE2-FD"],
        "description": "Fourier analysis, digital signal processing and filtering.",
        "enrollment": 72,
    },
    {
        "id": "EE2-EXT1", "name": "Embedded Systems Extension",
        "ects": 4.5, "domain": "Electrical Engineering", "level": "Extension",
        "language": "English", "semester": "WS", "prerequisites": ["EE2-COR"],
        "description": "Microcontrollers, RTOS and hardware-software interfaces.",
        "enrollment": 58,
    },
    {
        "id": "EE2-EXT2", "name": "Wireless Communications Extension",
        "ects": 3.0, "domain": "Electrical Engineering", "level": "Extension",
        "language": "English", "semester": "SS", "prerequisites": ["EE2-COR"],
        "description": "Wireless standards, antenna design and communication systems.",
        "enrollment": 48,
    },
]


def load_courses():
    global COURSES
    if os.path.exists(CACHE_FILE):
        print("Loading courses from cache...")
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            tiss_courses = json.load(f)
        # merge mock courses + TISS courses (mock takes priority for IDs)
        mock_ids = {c["id"] for c in MOCK_COURSES}
        tiss_filtered = [c for c in tiss_courses if c["id"] not in mock_ids]
        COURSES = MOCK_COURSES + tiss_filtered
        print(f"Loaded {len(COURSES)} courses ({len(MOCK_COURSES)} mock + {len(tiss_filtered)} TISS).")
    else:
        print("No cache found. Using mock course catalog.")
        COURSES = MOCK_COURSES


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/programs", methods=["GET"])
def get_programs():
    return jsonify({"programs": PROGRAMS})


@app.route("/api/courses", methods=["GET"])
def get_courses():
    return jsonify({"courses": COURSES, "total": len(COURSES)})


@app.route("/api/recommend", methods=["POST"])
def recommend():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    program = data.get("program", "")
    completed_ids = data.get("completed_ids", [])
    mode = data.get("mode", "default")
    num_results = int(data.get("num_results", 5))

    if not program:
        return jsonify({"error": "program is required"}), 400
    if mode not in ("default", "diversity"):
        return jsonify({"error": "mode must be default or diversity"}), 400

    num_results = max(3, min(num_results, 10))

    recommendations, locked = score_courses(
        courses=COURSES,
        completed_ids=completed_ids,
        program=program,
        mode=mode,
    )

    locked_output = [
        {
            "id": item["course"]["id"],
            "name": item["course"]["name"],
            "domain": item["course"]["domain"],
            "level": item["course"].get("level", ""),
            "unmet_prerequisites": item["unmet"],
        }
        for item in locked[:5]
    ]

    return jsonify({
        "recommendations": recommendations[:num_results],
        "locked_courses": locked_output,
        "total_eligible": len(recommendations),
        "mode": mode,
        "program": program,
    })


@app.route("/api/refresh", methods=["POST"])
def refresh_courses():
    global COURSES
    body = request.get_json(silent=True) or {}
    sem = body.get("semester", "2025W")
    fetched = fetch_all_courses(semester=sem)
    if fetched:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(fetched, f, ensure_ascii=False, indent=2)
        mock_ids = {c["id"] for c in MOCK_COURSES}
        tiss_filtered = [c for c in fetched if c["id"] not in mock_ids]
        COURSES = MOCK_COURSES + tiss_filtered
        return jsonify({"message": f"Refreshed — {len(COURSES)} total courses", "total": len(COURSES)})
    else:
        return jsonify({"message": "TISS fetch failed, keeping existing courses", "total": len(COURSES)}), 500


@app.route("/api/stats", methods=["GET"])
def stats():
    if not COURSES:
        return jsonify({"error": "No courses loaded"}), 500

    domains = {}
    levels = {"Foundation": 0, "Core": 0, "Extension": 0, "Other": 0}

    for course in COURSES:
        d = course["domain"]
        if d not in domains:
            domains[d] = {"count": 0, "total_enrollment": 0}
        domains[d]["count"] += 1
        domains[d]["total_enrollment"] += course.get("enrollment", 50)
        lvl = course.get("level", "Other")
        if lvl in levels:
            levels[lvl] += 1
        else:
            levels["Other"] += 1

    for d in domains:
        domains[d]["avg_enrollment"] = round(
            domains[d]["total_enrollment"] / domains[d]["count"]
        )

    return jsonify({
        "total_courses": len(COURSES),
        "avg_enrollment": round(sum(c.get("enrollment", 50) for c in COURSES) / len(COURSES)),
        "domains": domains,
        "levels": levels,
    })


if __name__ == "__main__":
    load_courses()
    app.run(debug=True, port=5001)
