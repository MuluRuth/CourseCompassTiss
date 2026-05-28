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

# Synonym map — normalises abbreviations from free-text bachelor input
SYNONYMS = {
    "ml": "machine learning", "ai": "artificial intelligence",
    "maths": "mathematics", "math": "mathematics",
    "stats": "statistics", "stat": "statistics",
    "db": "database", "dbms": "database", "dbs": "database",
    "oop": "software engineering", "java": "programming",
    "python": "programming", "coding": "programming",
    "c++": "programming", "js": "programming",
    "bi": "business intelligence", "bpm": "business process",
    "se": "software engineering", "os": "operating systems",
    "nlp": "natural language processing", "cv": "computer vision",
    "ds": "data science", "dl": "deep learning",
    "sql": "database", "nosql": "database",
    "er": "economics", "econ": "economics",
    "hr": "human resource", "pm": "project management",
    "ux": "user experience", "ui": "user interface",
}

def parse_bachelor_text(text):
    """
    Parse free-text bachelor background into a list of keywords.
    e.g. "ML, stats, Java, databases" -> ["machine learning", "statistics", "programming", "database"]
    """
    if not text:
        return []
    keywords = []
    for token in text.split(","):
        token = token.strip().lower()
        if token:
            keywords.append(SYNONYMS.get(token, token))
    return keywords

# ── REAL TU Wien Business Informatics courses ─────────────────────────────
# Source: Curriculum 066 926 Master programme Business Informatics 2025W-2026S
# ─────────────────────────────────────────────────────────────────────────────

MOCK_COURSES = [

    # ════════════════════════════════════════════════════════════════════
    # FOUNDATIONS — Prüfungsfach Business Informatics Foundations
    # ════════════════════════════════════════════════════════════════════

    {
        "id": "DA-FD", "name": "Business Intelligence",
        "tiss_id": "188.429",
        "ects": 6.0, "domain": "Data Analytics", "level": "Foundation",
        "language": "English", "semester": "WS", "prerequisites": [],
        "keywords": ["business intelligence", "data warehouse", "BI", "analytics", "reporting", "data", "SQL"],
        "description": "Foundations of business intelligence, data warehousing and analytical processing.",
        "enrollment": 120,
    },
    {
        "id": "EE-FD", "name": "Enterprise & Process Engineering",
        "tiss_id": "194.152",
        "ects": 6.0, "domain": "Enterprise Engineering", "level": "Foundation",
        "language": "English", "semester": "WS", "prerequisites": [],
        "keywords": ["enterprise", "process engineering", "business process", "modeling", "BPM", "architecture"],
        "description": "Enterprise architecture, business process management and model-driven engineering.",
        "enrollment": 110,
    },
    {
        "id": "EM-FD1", "name": "Econometrics for Business Informatics",
        "tiss_id": "105.628",
        "ects": 3.0, "domain": "Economic Modeling", "level": "Foundation",
        "language": "English", "semester": "SS", "prerequisites": [],
        "keywords": ["econometrics", "regression", "statistics", "economics", "quantitative", "inference", "OLS"],
        "description": "Econometric methods applied to business informatics problems.",
        "enrollment": 95,
    },
    {
        "id": "EM-FD2", "name": "Computational Social Simulation",
        "tiss_id": "105.622",
        "ects": 3.0, "domain": "Economic Modeling", "level": "Foundation",
        "language": "English", "semester": "SS", "prerequisites": [],
        "keywords": ["simulation", "agent-based", "social", "computational", "modeling", "systems", "complexity"],
        "description": "Agent-based and social simulation techniques for modeling complex systems.",
        "enrollment": 85,
    },
    {
        "id": "ISE-FD", "name": "Model Engineering",
        "tiss_id": "188.923",
        "ects": 6.0, "domain": "Information Systems Engineering", "level": "Foundation",
        "language": "English", "semester": "WS", "prerequisites": [],
        "keywords": ["model engineering", "models", "modeling languages", "transformations", "MDE", "software engineering"],
        "description": "Models, modeling languages, transformations and model management.",
        "enrollment": 115,
    },
    {
        "id": "MS-FD1", "name": "Human Resource Management and Leadership",
        "tiss_id": "330.188",
        "ects": 3.0, "domain": "Management Science", "level": "Foundation",
        "language": "English", "semester": "WS", "prerequisites": [],
        "keywords": ["HR", "human resource", "leadership", "management", "organization", "people", "talent"],
        "description": "HR management, leadership theory and organizational behavior.",
        "enrollment": 100,
    },
    {
        "id": "MS-FD2", "name": "IT-based Management",
        "tiss_id": "330.232",
        "ects": 3.0, "domain": "Management Science", "level": "Foundation",
        "language": "English", "semester": "WS", "prerequisites": [],
        "keywords": ["IT management", "management", "digital", "strategy", "governance", "IT systems"],
        "description": "Managing organizations using IT systems and digital tools.",
        "enrollment": 105,
    },
    {
        "id": "RM-FD", "name": "Research Methods",
        "tiss_id": "194.078",
        "ects": 3.0, "domain": "Research Methods", "level": "Foundation",
        "language": "English", "semester": "WS+SS", "prerequisites": [],
        "keywords": ["research methods", "scientific writing", "methodology", "research design", "empirical"],
        "description": "Scientific research methods, empirical study design and academic writing.",
        "enrollment": 90,
    },

    # ════════════════════════════════════════════════════════════════════
    # DATA ANALYTICS — Core and Extensions
    # ════════════════════════════════════════════════════════════════════

    {
        "id": "DA-COR1", "name": "Experiment Design and Execution",
        "tiss_id": "194.192",
        "ects": 6.0, "domain": "Data Analytics", "level": "Core",
        "language": "English", "semester": "WS", "prerequisites": ["DA-FD"],
        "keywords": ["experiment design", "hypothesis testing", "evaluation", "empirical", "analytics", "data", "scientific method"],
        "description": "Designing and executing data-driven experiments and evaluations.",
        "enrollment": 88,
    },
    {
        "id": "DA-COR2", "name": "Multivariate Statistics",
        "tiss_id": "107.388",
        "ects": 4.5, "domain": "Data Analytics", "level": "Core",
        "language": "English", "semester": "WS", "prerequisites": ["DA-FD"],
        "keywords": ["multivariate statistics", "clustering", "PCA", "factor analysis", "statistics", "data analysis", "MANOVA"],
        "description": "Multivariate statistical methods including PCA, clustering and factor analysis.",
        "enrollment": 92,
    },
    # DA Extensions — student picks 12 ECTS from these
    {
        "id": "DA-EXT1", "name": "Machine Learning",
        "tiss_id": "184.702",
        "ects": 4.5, "domain": "Data Analytics", "level": "Extension",
        "language": "English", "semester": "WS", "prerequisites": ["DA-COR1"],
        "keywords": ["machine learning", "supervised learning", "classification", "regression", "algorithms", "model", "features"],
        "description": "Core machine learning algorithms, model evaluation and practical applications.",
        "enrollment": 140,
    },
    {
        "id": "DA-EXT2", "name": "Applied Deep Learning",
        "tiss_id": "194.077",
        "ects": 3.0, "domain": "Data Analytics", "level": "Extension",
        "language": "English", "semester": "WS", "prerequisites": ["DA-COR1"],
        "keywords": ["deep learning", "neural networks", "CNN", "applied AI", "transformers", "image", "classification"],
        "description": "Practical deep learning with neural networks and modern architectures.",
        "enrollment": 110,
    },
    {
        "id": "DA-EXT3", "name": "Generative AI",
        "tiss_id": "194.207",
        "ects": 6.0, "domain": "Data Analytics", "level": "Extension",
        "language": "English", "semester": "WS", "prerequisites": ["DA-COR1"],
        "keywords": ["generative AI", "LLM", "GPT", "diffusion models", "generative models", "AI", "language models"],
        "description": "Generative AI systems including large language models and diffusion models.",
        "enrollment": 130,
    },
    {
        "id": "DA-EXT4", "name": "Information Visualization",
        "tiss_id": "193.171",
        "ects": 6.0, "domain": "Data Analytics", "level": "Extension",
        "language": "English", "semester": "SS", "prerequisites": ["DA-COR1"],
        "keywords": ["visualization", "information visualization", "visual analytics", "charts", "data storytelling", "dashboard"],
        "description": "Principles and techniques of information visualization and visual analytics.",
        "enrollment": 75,
    },
    {
        "id": "DA-EXT5", "name": "Computational Statistics",
        "tiss_id": "107.258",
        "ects": 4.5, "domain": "Data Analytics", "level": "Extension",
        "language": "English", "semester": "WS", "prerequisites": ["DA-COR2"],
        "keywords": ["computational statistics", "simulation", "bootstrap", "Monte Carlo", "statistics", "R", "Python"],
        "description": "Statistical computing methods including simulation and resampling techniques.",
        "enrollment": 65,
    },
    {
        "id": "DA-EXT6", "name": "Advanced Information Retrieval",
        "tiss_id": "188.980",
        "ects": 3.0, "domain": "Data Analytics", "level": "Extension",
        "language": "English", "semester": "SS", "prerequisites": ["DA-COR1"],
        "keywords": ["information retrieval", "search", "indexing", "ranking", "NLP", "text", "IR"],
        "description": "Search engine principles, indexing, ranking and modern IR techniques.",
        "enrollment": 70,
    },
    {
        "id": "DA-EXT7", "name": "Security, Privacy and Explainability in ML",
        "tiss_id": "194.055",
        "ects": 3.0, "domain": "Data Analytics", "level": "Extension",
        "language": "English", "semester": "SS", "prerequisites": ["DA-COR1"],
        "keywords": ["explainability", "XAI", "fairness", "privacy", "security", "machine learning", "interpretability"],
        "description": "Explainability, fairness, privacy and security considerations in ML systems.",
        "enrollment": 60,
    },
    {
        "id": "DA-EXT8", "name": "Visual Data Science",
        "tiss_id": "186.868",
        "ects": 3.0, "domain": "Data Analytics", "level": "Extension",
        "language": "English", "semester": "WS", "prerequisites": ["DA-COR1"],
        "keywords": ["visual data science", "data visualization", "exploration", "analytics", "visual", "dashboards"],
        "description": "Visual approaches to data science, exploration and analysis.",
        "enrollment": 55,
    },
    {
        "id": "DA-EXT9", "name": "AI Programming",
        "tiss_id": "194.193",
        "ects": 6.0, "domain": "Data Analytics", "level": "Extension",
        "language": "English", "semester": "WS", "prerequisites": ["DA-COR1"],
        "keywords": ["AI programming", "Python", "machine learning", "coding", "implementation", "algorithms", "AI development"],
        "description": "Programming AI systems in Python with hands-on implementation of ML algorithms.",
        "enrollment": 95,
    },

    # ════════════════════════════════════════════════════════════════════
    # ENTERPRISE ENGINEERING — Core and Extensions
    # ════════════════════════════════════════════════════════════════════

    {
        "id": "EE-COR1", "name": "Recommender Systems and User Modeling",
        "tiss_id": "194.210",
        "ects": 6.0, "domain": "Enterprise Engineering", "level": "Core",
        "language": "English", "semester": "SS", "prerequisites": ["EE-FD"],
        "keywords": ["recommender systems", "user modeling", "collaborative filtering", "content-based", "hybrid", "personalization"],
        "description": "Collaborative filtering, content-based and hybrid recommender systems with user modeling.",
        "enrollment": 85,
    },
    {
        "id": "EE-COR2", "name": "E-Commerce",
        "tiss_id": "188.427",
        "ects": 3.0, "domain": "Enterprise Engineering", "level": "Core",
        "language": "English", "semester": "WS", "prerequisites": ["EE-FD"],
        "keywords": ["e-commerce", "online business", "digital commerce", "marketplace", "payments", "customer", "web"],
        "description": "E-commerce systems, platforms and digital business models.",
        "enrollment": 92,
    },
    {
        "id": "EE-COR3", "name": "Innovation",
        "tiss_id": "188.915",
        "ects": 3.0, "domain": "Enterprise Engineering", "level": "Core",
        "language": "English", "semester": "SS", "prerequisites": ["EE-FD"],
        "keywords": ["innovation", "product development", "entrepreneurship", "design thinking", "startup", "business"],
        "description": "Innovation processes, design thinking and product development methodologies.",
        "enrollment": 88,
    },
    # EE Extensions
    {
        "id": "EE-EXT1", "name": "E-Marketing",
        "tiss_id": "194.034",
        "ects": 3.0, "domain": "Enterprise Engineering", "level": "Extension",
        "language": "English", "semester": "SS", "prerequisites": ["EE-COR2"],
        "keywords": ["e-marketing", "digital marketing", "SEO", "social media marketing", "online advertising", "customer acquisition"],
        "description": "Digital marketing strategies, SEO, online advertising and customer acquisition.",
        "enrollment": 78,
    },
    {
        "id": "EE-EXT2", "name": "Social Media",
        "tiss_id": "188.956",
        "ects": 3.0, "domain": "Enterprise Engineering", "level": "Extension",
        "language": "English", "semester": "WS", "prerequisites": ["EE-COR1"],
        "keywords": ["social media", "social networks", "platforms", "content", "community", "engagement", "analytics"],
        "description": "Social media platforms, analytics and community management strategies.",
        "enrollment": 82,
    },
    {
        "id": "EE-EXT3", "name": "IT Governance",
        "tiss_id": "188.978",
        "ects": 3.0, "domain": "Enterprise Engineering", "level": "Extension",
        "language": "English", "semester": "SS", "prerequisites": ["EE-COR3"],
        "keywords": ["IT governance", "governance", "compliance", "COBIT", "risk", "IT management", "frameworks"],
        "description": "IT governance frameworks, compliance and risk management for enterprises.",
        "enrollment": 65,
    },
    {
        "id": "EE-EXT4", "name": "Digital Humanism",
        "tiss_id": "194.072",
        "ects": 3.0, "domain": "Enterprise Engineering", "level": "Extension",
        "language": "English", "semester": "WS", "prerequisites": ["EE-COR3"],
        "keywords": ["digital humanism", "ethics", "technology society", "human-centered", "values", "digital transformation"],
        "description": "The impact of digital technologies on society and human-centered design values.",
        "enrollment": 70,
    },
    {
        "id": "EE-EXT5", "name": "Information Search on the Internet",
        "tiss_id": "188.484",
        "ects": 3.0, "domain": "Enterprise Engineering", "level": "Extension",
        "language": "English", "semester": "SS", "prerequisites": ["EE-COR1"],
        "keywords": ["information search", "web search", "search engines", "information retrieval", "internet", "crawling"],
        "description": "Web search technologies, information retrieval on the internet and search engine optimization.",
        "enrollment": 60,
    },
    {
        "id": "EE-EXT6", "name": "Introduction to Computational Sustainability",
        "tiss_id": "191.021",
        "ects": 6.0, "domain": "Enterprise Engineering", "level": "Extension",
        "language": "English", "semester": "WS", "prerequisites": ["EE-COR3"],
        "keywords": ["sustainability", "computational sustainability", "environment", "green IT", "climate", "energy"],
        "description": "Applying computational methods to sustainability challenges and environmental problems.",
        "enrollment": 50,
    },
    {
        "id": "EE-EXT7", "name": "Management of Software Projects",
        "tiss_id": "188.407",
        "ects": 3.0, "domain": "Enterprise Engineering", "level": "Extension",
        "language": "English", "semester": "WS", "prerequisites": ["EE-COR3"],
        "keywords": ["software project management", "project planning", "agile", "scrum", "teams", "delivery", "management"],
        "description": "Managing software development projects using agile and traditional methodologies.",
        "enrollment": 88,
    },
    {
        "id": "EE-EXT8", "name": "Advanced Topics in Recommender Systems and Generative AI",
        "tiss_id": "ADV-RS-GAI",
        "ects": 3.0, "domain": "Enterprise Engineering", "level": "Extension",
        "language": "English", "semester": "SS", "prerequisites": ["EE-COR1"],
        "keywords": ["recommender systems", "generative AI", "LLM", "advanced", "user modeling", "personalization", "AI"],
        "description": "Advanced topics combining recommender systems with generative AI techniques.",
        "enrollment": 55,
    },

    # ════════════════════════════════════════════════════════════════════
    # ECONOMIC MODELING — Core and Extensions
    # ════════════════════════════════════════════════════════════════════

    {
        "id": "EM-COR1", "name": "Modeling and Simulation",
        "tiss_id": "194.076",
        "ects": 3.0, "domain": "Economic Modeling", "level": "Core",
        "language": "English", "semester": "WS", "prerequisites": ["EM-FD1"],
        "keywords": ["modeling", "simulation", "systems", "dynamic", "computational", "model building"],
        "description": "System modeling and simulation methods for business and economic systems.",
        "enrollment": 80,
    },
    {
        "id": "EM-COR2", "name": "Model-based Decision Support",
        "tiss_id": "105.632",
        "ects": 3.0, "domain": "Economic Modeling", "level": "Core",
        "language": "English", "semester": "SS", "prerequisites": ["EM-FD1"],
        "keywords": ["decision support", "models", "optimization", "decision making", "analytics", "quantitative"],
        "description": "Model-based approaches to decision support and optimization.",
        "enrollment": 75,
    },
    {
        "id": "EM-COR3", "name": "International Trade Theory and Policy",
        "tiss_id": "105.623",
        "ects": 3.0, "domain": "Economic Modeling", "level": "Core",
        "language": "English", "semester": "SS", "prerequisites": ["EM-FD1"],
        "keywords": ["international trade", "trade policy", "economics", "globalization", "markets", "macroeconomics"],
        "description": "Theories of international trade, trade policy and global economic integration.",
        "enrollment": 70,
    },
    # EM Extensions
    {
        "id": "EM-EXT1", "name": "Advanced Modeling and Simulation",
        "tiss_id": "194.056",
        "ects": 3.0, "domain": "Economic Modeling", "level": "Extension",
        "language": "English", "semester": "SS", "prerequisites": ["EM-COR1"],
        "keywords": ["advanced simulation", "agent-based modeling", "complex systems", "simulation", "modeling"],
        "description": "Advanced simulation techniques including agent-based and complex systems modeling.",
        "enrollment": 50,
    },
    {
        "id": "EM-EXT2", "name": "Game Theoretic Modelling",
        "tiss_id": "105.649",
        "ects": 3.0, "domain": "Economic Modeling", "level": "Extension",
        "language": "English", "semester": "WS", "prerequisites": ["EM-COR2"],
        "keywords": ["game theory", "Nash equilibrium", "strategic interaction", "economics", "decision", "optimization"],
        "description": "Game theory and strategic interaction modeling for economic and business decisions.",
        "enrollment": 55,
    },
    {
        "id": "EM-EXT3", "name": "Dynamic Macroeconomics",
        "tiss_id": "105.646",
        "ects": 3.0, "domain": "Economic Modeling", "level": "Extension",
        "language": "English", "semester": "WS", "prerequisites": ["EM-COR3"],
        "keywords": ["macroeconomics", "dynamic", "growth", "cycles", "monetary", "fiscal", "economic modeling"],
        "description": "Dynamic macroeconomic models, growth theory and business cycle analysis.",
        "enrollment": 45,
    },
    {
        "id": "EM-EXT4", "name": "International Macroeconomics",
        "tiss_id": "105.214",
        "ects": 3.0, "domain": "Economic Modeling", "level": "Extension",
        "language": "English", "semester": "SS", "prerequisites": ["EM-COR3"],
        "keywords": ["international macroeconomics", "exchange rates", "balance of payments", "open economy", "globalization"],
        "description": "Open economy macroeconomics, exchange rates and international financial systems.",
        "enrollment": 48,
    },

    # ════════════════════════════════════════════════════════════════════
    # INFORMATION SYSTEMS ENGINEERING — Core and Extensions
    # ════════════════════════════════════════════════════════════════════

    {
        "id": "ISE-COR1", "name": "Advanced Database Systems",
        "tiss_id": "184.780",
        "ects": 6.0, "domain": "Information Systems Engineering", "level": "Core",
        "language": "English", "semester": "SS", "prerequisites": ["ISE-FD"],
        "keywords": ["database", "advanced database", "SQL", "NoSQL", "query optimization", "transactions", "indexing"],
        "description": "Advanced database concepts including query optimization, transactions and distributed databases.",
        "enrollment": 90,
    },
    {
        "id": "ISE-COR2", "name": "Advanced Internet Computing",
        "tiss_id": "194.196",
        "ects": 6.0, "domain": "Information Systems Engineering", "level": "Core",
        "language": "English", "semester": "WS", "prerequisites": ["ISE-FD"],
        "keywords": ["internet computing", "web", "cloud", "distributed", "API", "services", "scalability"],
        "description": "Advanced internet computing including cloud services, APIs and distributed architectures.",
        "enrollment": 88,
    },
    {
        "id": "ISE-COR3", "name": "Introduction to Semantic Systems",
        "tiss_id": "188.399",
        "ects": 3.0, "domain": "Information Systems Engineering", "level": "Core",
        "language": "English", "semester": "WS", "prerequisites": ["ISE-FD"],
        "keywords": ["semantic systems", "ontology", "RDF", "knowledge representation", "linked data", "semantic web"],
        "description": "Semantic web technologies, ontologies and knowledge representation.",
        "enrollment": 72,
    },
    # ISE Extensions
    {
        "id": "ISE-EXT1", "name": "Knowledge Graphs",
        "tiss_id": "192.116",
        "ects": 6.0, "domain": "Information Systems Engineering", "level": "Extension",
        "language": "English", "semester": "SS", "prerequisites": ["ISE-COR3"],
        "keywords": ["knowledge graphs", "RDF", "SPARQL", "ontology", "linked data", "graph database", "semantic"],
        "description": "Building and querying knowledge graphs with RDF, SPARQL and ontologies.",
        "enrollment": 58,
    },
    {
        "id": "ISE-EXT2", "name": "Distributed Systems Technologies",
        "tiss_id": "184.260",
        "ects": 6.0, "domain": "Information Systems Engineering", "level": "Extension",
        "language": "English", "semester": "SS", "prerequisites": ["ISE-COR2"],
        "keywords": ["distributed systems", "middleware", "consistency", "microservices", "cloud", "fault tolerance"],
        "description": "Distributed systems middleware, consistency models and cloud architectures.",
        "enrollment": 75,
    },
    {
        "id": "ISE-EXT3", "name": "Internet of Things",
        "tiss_id": "182.753",
        "ects": 6.0, "domain": "Information Systems Engineering", "level": "Extension",
        "language": "English", "semester": "WS", "prerequisites": ["ISE-COR2"],
        "keywords": ["IoT", "internet of things", "sensors", "smart devices", "edge computing", "embedded", "connectivity"],
        "description": "IoT architectures, sensor systems, edge computing and smart device integration.",
        "enrollment": 70,
    },
    {
        "id": "ISE-EXT4", "name": "Serverless Computing",
        "tiss_id": "194.151",
        "ects": 3.0, "domain": "Information Systems Engineering", "level": "Extension",
        "language": "English", "semester": "WS", "prerequisites": ["ISE-COR2"],
        "keywords": ["serverless", "FaaS", "AWS Lambda", "cloud", "microservices", "event-driven", "scalability"],
        "description": "Serverless computing architectures, FaaS platforms and event-driven systems.",
        "enrollment": 62,
    },
    {
        "id": "ISE-EXT5", "name": "System and Application Security",
        "tiss_id": "192.112",
        "ects": 6.0, "domain": "Information Systems Engineering", "level": "Extension",
        "language": "English", "semester": "SS", "prerequisites": ["ISE-COR2"],
        "keywords": ["security", "application security", "vulnerabilities", "cryptography", "authentication", "secure coding"],
        "description": "System security, application vulnerabilities and secure software development.",
        "enrollment": 80,
    },
    {
        "id": "ISE-EXT6", "name": "Digital Forensics",
        "tiss_id": "188.922",
        "ects": 3.0, "domain": "Information Systems Engineering", "level": "Extension",
        "language": "English", "semester": "SS", "prerequisites": ["ISE-COR1"],
        "keywords": ["digital forensics", "investigation", "security", "evidence", "cybercrime", "incident response"],
        "description": "Digital forensics techniques for investigating cyber incidents and security breaches.",
        "enrollment": 55,
    },

    # ════════════════════════════════════════════════════════════════════
    # MANAGEMENT SCIENCE — Core and Extensions
    # ════════════════════════════════════════════════════════════════════

    {
        "id": "MS-COR1", "name": "Managing People and Organizations",
        "tiss_id": "330.190",
        "ects": 3.0, "domain": "Management Science", "level": "Core",
        "language": "English", "semester": "WS", "prerequisites": ["MS-FD1"],
        "keywords": ["people management", "organization", "teams", "leadership", "HR", "culture", "change management"],
        "description": "Managing people, teams and organizational change in technology-driven environments.",
        "enrollment": 88,
    },
    {
        "id": "MS-COR2", "name": "Project and Enterprise Financing",
        "tiss_id": "330.214",
        "ects": 3.0, "domain": "Management Science", "level": "Core",
        "language": "English", "semester": "SS", "prerequisites": ["MS-FD2"],
        "keywords": ["project financing", "enterprise finance", "investment", "capital", "funding", "financial planning"],
        "description": "Financing strategies for projects and enterprises including investment and capital planning.",
        "enrollment": 82,
    },
    # MS Extensions
    {
        "id": "MS-EXT1", "name": "Strategic Management",
        "tiss_id": "330.130",
        "ects": 3.0, "domain": "Management Science", "level": "Extension",
        "language": "English", "semester": "SS", "prerequisites": ["MS-COR1"],
        "keywords": ["strategic management", "strategy", "competitive advantage", "Porter", "business strategy", "planning"],
        "description": "Business strategy, competitive analysis and strategic planning frameworks.",
        "enrollment": 85,
    },
    {
        "id": "MS-EXT2", "name": "E&I Garage - Business Model Development",
        "tiss_id": "330.255",
        "ects": 5.0, "domain": "Management Science", "level": "Extension",
        "language": "English", "semester": "SS", "prerequisites": ["MS-COR2"],
        "keywords": ["business model", "entrepreneurship", "startup", "lean", "MVP", "innovation", "venture"],
        "description": "Developing and validating business models through entrepreneurship and lean startup methods.",
        "enrollment": 72,
    },
    {
        "id": "MS-EXT3", "name": "Enterprise Risk Management",
        "tiss_id": "330.239",
        "ects": 3.0, "domain": "Management Science", "level": "Extension",
        "language": "English", "semester": "SS", "prerequisites": ["MS-COR2"],
        "keywords": ["risk management", "enterprise risk", "ERM", "compliance", "governance", "risk assessment"],
        "description": "Enterprise risk management frameworks, risk assessment and mitigation strategies.",
        "enrollment": 68,
    },
    {
        "id": "MS-EXT4", "name": "Innovation Theory",
        "tiss_id": "330.258",
        "ects": 3.0, "domain": "Management Science", "level": "Extension",
        "language": "English", "semester": "WS", "prerequisites": ["MS-COR1"],
        "keywords": ["innovation theory", "disruptive innovation", "technology adoption", "R&D", "creativity", "innovation management"],
        "description": "Theories of innovation, technology adoption and managing R&D in organizations.",
        "enrollment": 62,
    },
    {
        "id": "MS-EXT5", "name": "International Negotiations",
        "tiss_id": "330.131",
        "ects": 3.0, "domain": "Management Science", "level": "Extension",
        "language": "English", "semester": "SS", "prerequisites": ["MS-COR1"],
        "keywords": ["negotiations", "international", "communication", "conflict resolution", "business negotiations", "diplomacy"],
        "description": "Negotiation strategies and tactics in international business contexts.",
        "enrollment": 75,
    },
    {
        "id": "MS-EXT6", "name": "Financial Management and Reporting",
        "tiss_id": "330.215",
        "ects": 3.0, "domain": "Management Science", "level": "Extension",
        "language": "English", "semester": "SS", "prerequisites": ["MS-COR2"],
        "keywords": ["financial management", "financial reporting", "accounting", "balance sheet", "P&L", "controlling"],
        "description": "Financial management, reporting frameworks and controlling for IT organisations.",
        "enrollment": 70,
    },
    {
        "id": "MS-EXT7", "name": "Organization Theory",
        "tiss_id": "330.219",
        "ects": 5.0, "domain": "Management Science", "level": "Extension",
        "language": "English", "semester": "SS", "prerequisites": ["MS-COR1"],
        "keywords": ["organization theory", "organizational design", "structure", "culture", "institutions", "bureaucracy"],
        "description": "Theories of organizational design, structure and institutional behavior.",
        "enrollment": 58,
    },
]


def load_courses():
    global COURSES
    if os.path.exists(CACHE_FILE):
        print("Loading courses from cache...")
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            tiss_courses = json.load(f)
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
    bachelor_topics = data.get("bachelor_topics", [])
    mode = data.get("mode", "deepen")
    num_results = int(data.get("num_results", 5))

    if not program:
        return jsonify({"error": "program is required"}), 400
    if mode not in ("deepen", "explore"):
        return jsonify({"error": "mode must be deepen or explore"}), 400

    num_results = max(3, min(num_results, 10))

    # parse free-text bachelor background into keywords
    bachelor_text = data.get("bachelor_topics", "")
    if isinstance(bachelor_text, list):
        bachelor_text = ", ".join(bachelor_text)
    extra_keywords = parse_bachelor_text(bachelor_text)

    recommendations, locked = score_courses(
        courses=COURSES,
        completed_ids=completed_ids,
        program=program,
        mode=mode,
        extra_keywords=extra_keywords,
    )

    locked_output = [
        {
            "id": item["course"]["id"],
            "name": item["course"]["name"],
            "domain": item["course"]["domain"],
            "level": item["course"].get("level", ""),
            "unmet_prerequisites": item["unmet"],
        }
        for item in locked[:8]
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
        levels[lvl if lvl in levels else "Other"] += 1

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
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=False, host="0.0.0.0", port=port)