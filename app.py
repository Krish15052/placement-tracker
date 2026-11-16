from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    flash
)

import os
import re
import time
import requests
import mysql.connector
from urllib.parse import quote_plus

from werkzeug.utils import secure_filename
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from PyPDF2 import PdfReader


# =========================================================
# APP CONFIG
# =========================================================

app = Flask(
    __name__,
    template_folder="."
)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "placement-tracker-secret-change-this"
)

UPLOAD_FOLDER = "uploads"

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# =========================================================
# DATABASE
# =========================================================

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": os.environ.get(
        "DB_PASSWORD",
        "krish@12"
    ),
    "database": "placement_tracker"
}


def get_db():

    return mysql.connector.connect(
        **DB_CONFIG
    )


# =========================================================
# API CONFIG
# =========================================================

ADZUNA_APP_ID = os.environ.get(
    "ADZUNA_APP_ID"
)

ADZUNA_APP_KEY = os.environ.get(
    "ADZUNA_APP_KEY"
)

ARBEITNOW_URL = (
    "https://www.arbeitnow.com/"
    "api/job-board-api"
)


# =========================================================
# INDIA LOCATION FILTER
# =========================================================
#
# IMPORTANT:
# Only jobs whose location is clearly India/Indian-city based
# will be displayed.
#
# Remote jobs without an India location are NOT included.
# =========================================================

INDIA_LOCATION_KEYWORDS = [

    # Country
    "india",
    "bharat",

    # Major cities
    "delhi",
    "new delhi",
    "gurgaon",
    "gurugram",
    "noida",
    "ghaziabad",
    "faridabad",

    "mumbai",
    "bombay",

    "pune",

    "bangalore",
    "bengaluru",

    "hyderabad",

    "chennai",
    "madras",

    "kolkata",
    "calcutta",

    "ahmedabad",

    "jaipur",

    "lucknow",

    "chandigarh",

    "indore",

    "bhopal",

    "nagpur",

    "surat",

    "vadodara",

    "kochi",
    "cochin",

    "coimbatore",

    "visakhapatnam",
    "vizag",

    "bhubaneswar",

    "patna",

    "ranchi",

    "dehradun",

    "mysore",
    "mysuru",

    "thiruvananthapuram",
    "trivandrum",

    "kanpur",

    "agra",

    "nashik",

    "rajkot",

    "ludhiana",

    "amritsar",

    "jodhpur",

    "udaipur",

    "varanasi",

    "meerut",

    "srinagar",

    "goa",

    # States / UTs
    "andhra pradesh",
    "arunachal pradesh",
    "assam",
    "bihar",
    "chhattisgarh",
    "goa",
    "gujarat",
    "haryana",
    "himachal pradesh",
    "jharkhand",
    "karnataka",
    "kerala",
    "madhya pradesh",
    "maharashtra",
    "manipur",
    "meghalaya",
    "mizoram",
    "nagaland",
    "odisha",
    "orissa",
    "punjab",
    "rajasthan",
    "sikkim",
    "tamil nadu",
    "telangana",
    "tripura",
    "uttar pradesh",
    "uttarakhand",
    "west bengal",

    "jammu and kashmir",
    "ladakh",

    "delhi ncr",
    "ncr"
]


def is_india_location(location):

    if not location:
        return False

    location = normalize_text(
        location
    )

    if not location:
        return False

    for keyword in INDIA_LOCATION_KEYWORDS:

        if keyword in location:
            return True

    return False


# =========================================================
# SKILL DATABASE
# =========================================================

SKILL_ALIASES = {

    "Python": [
        "python",
        "python3"
    ],

    "Java": [
        "java"
    ],

    "C++": [
        "c++",
        "cpp"
    ],

    "C": [
        "c language",
        "c programming"
    ],

    "C#": [
        "c#",
        "c sharp"
    ],

    "JavaScript": [
        "javascript",
        "js",
        "ecmascript"
    ],

    "TypeScript": [
        "typescript",
        "ts"
    ],

    "HTML": [
        "html",
        "html5"
    ],

    "CSS": [
        "css",
        "css3"
    ],

    "React": [
        "react",
        "reactjs",
        "react.js"
    ],

    "Angular": [
        "angular",
        "angularjs"
    ],

    "Vue": [
        "vue",
        "vuejs",
        "vue.js"
    ],

    "Node.js": [
        "node.js",
        "nodejs",
        "node js"
    ],

    "Express.js": [
        "express.js",
        "expressjs",
        "express js"
    ],

    "Django": [
        "django"
    ],

    "Flask": [
        "flask"
    ],

    "Spring Boot": [
        "spring boot",
        "springboot"
    ],

    "SQL": [
        "sql"
    ],

    "MySQL": [
        "mysql"
    ],

    "PostgreSQL": [
        "postgresql",
        "postgres"
    ],

    "MongoDB": [
        "mongodb",
        "mongo db",
        "mongo"
    ],

    "Oracle": [
        "oracle database",
        "oracle db"
    ],

    "Redis": [
        "redis"
    ],

    "Machine Learning": [
        "machine learning",
        "machine-learning",
        "ml"
    ],

    "Deep Learning": [
        "deep learning",
        "deep-learning"
    ],

    "Artificial Intelligence": [
        "artificial intelligence",
        "artificial intelligence ai"
    ],

    "Generative AI": [
        "generative ai",
        "genai",
        "gen ai"
    ],

    "NLP": [
        "natural language processing",
        "nlp"
    ],

    "TensorFlow": [
        "tensorflow"
    ],

    "PyTorch": [
        "pytorch"
    ],

    "Pandas": [
        "pandas"
    ],

    "NumPy": [
        "numpy"
    ],

    "Scikit-learn": [
        "scikit-learn",
        "sklearn"
    ],

    "AWS": [
        "aws",
        "amazon web services"
    ],

    "Azure": [
        "azure",
        "microsoft azure"
    ],

    "Google Cloud": [
        "google cloud",
        "gcp",
        "google cloud platform"
    ],

    "Git": [
        "git"
    ],

    "GitHub": [
        "github"
    ],

    "Docker": [
        "docker"
    ],

    "Kubernetes": [
        "kubernetes",
        "k8s"
    ],

    "Jenkins": [
        "jenkins"
    ],

    "Linux": [
        "linux"
    ],

    "REST API": [
        "rest api",
        "restful api",
        "restful"
    ],

    "Data Structures": [
        "data structures",
        "data structure",
        "dsa"
    ],

    "Algorithms": [
        "algorithms",
        "algorithm"
    ],

    "Power BI": [
        "power bi"
    ],

    "Tableau": [
        "tableau"
    ]
}


# =========================================================
# SKILL CATEGORIES
# =========================================================

SKILL_CATEGORIES = {

    "Programming": [
        "Python",
        "Java",
        "C++",
        "C",
        "C#",
        "JavaScript",
        "TypeScript"
    ],

    "Web Development": [
        "HTML",
        "CSS",
        "React",
        "Angular",
        "Vue",
        "Node.js",
        "Express.js",
        "Django",
        "Flask",
        "Spring Boot"
    ],

    "Database": [
        "SQL",
        "MySQL",
        "PostgreSQL",
        "MongoDB",
        "Oracle",
        "Redis"
    ],

    "AI / Machine Learning": [
        "Machine Learning",
        "Deep Learning",
        "Artificial Intelligence",
        "Generative AI",
        "NLP",
        "TensorFlow",
        "PyTorch",
        "Pandas",
        "NumPy",
        "Scikit-learn"
    ],

    "Cloud / DevOps": [
        "AWS",
        "Azure",
        "Google Cloud",
        "Git",
        "GitHub",
        "Docker",
        "Kubernetes",
        "Jenkins",
        "Linux"
    ],

    "Other Technical Skills": [
        "REST API",
        "Data Structures",
        "Algorithms",
        "Power BI",
        "Tableau"
    ]
}


# =========================================================
# JOB ROLE KEYWORDS
# =========================================================

ROLE_KEYWORDS = {

    "Software Developer": [
        "software developer",
        "software engineer",
        "application developer"
    ],

    "Full Stack Developer": [
        "full stack",
        "fullstack",
        "web developer"
    ],

    "Frontend Developer": [
        "frontend",
        "front end",
        "react developer",
        "javascript developer",
        "ui developer"
    ],

    "Backend Developer": [
        "backend",
        "back end",
        "python developer",
        "java developer",
        "node developer",
        "server side"
    ],

    "Python Developer": [
        "python developer",
        "python engineer",
        "django developer",
        "flask developer"
    ],

    "Java Developer": [
        "java developer",
        "java engineer",
        "spring boot developer"
    ],

    "Data Analyst": [
        "data analyst",
        "data analytics",
        "business analyst",
        "reporting analyst"
    ],

    "Data Scientist": [
        "data scientist",
        "data science"
    ],

    "Machine Learning Engineer": [
        "machine learning engineer",
        "machine learning",
        "ml engineer"
    ],

    "AI Engineer": [
        "ai engineer",
        "artificial intelligence engineer",
        "ai developer"
    ],

    "DevOps Engineer": [
        "devops",
        "devops engineer",
        "cloud engineer"
    ]
}


# =========================================================
# JOB CACHE
# =========================================================

JOB_CACHE = {
    "jobs": [],
    "timestamp": 0
}

CACHE_SECONDS = 15 * 60


# =========================================================
# TEXT HELPERS
# =========================================================

def normalize_text(text):

    if not text:
        return ""

    text = str(text)

    text = text.replace(
        "\n",
        " "
    )

    text = text.replace(
        "\r",
        " "
    )

    text = text.replace(
        "\t",
        " "
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.lower().strip()


def compact_text(text):

    text = normalize_text(
        text
    )

    return re.sub(
        r"[^a-z0-9+#.]+",
        "",
        text
    )


# =========================================================
# SKILL DETECTION
# =========================================================

def contains_skill(
    text,
    alias
):

    normalized = normalize_text(
        text
    )

    alias = normalize_text(
        alias
    )

    if not alias:
        return False

    if len(alias) <= 2:

        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(alias)
            + r"(?![a-z0-9])"
        )

        return bool(
            re.search(
                pattern,
                normalized
            )
        )

    if alias in normalized:
        return True

    compact = compact_text(
        normalized
    )

    compact_alias = compact_text(
        alias
    )

    if (
        compact_alias
        and compact_alias in compact
    ):
        return True

    return False


def detect_skills(text):

    detected = []

    if not text:
        return detected

    for skill, aliases in SKILL_ALIASES.items():

        for alias in aliases:

            if contains_skill(
                text,
                alias
            ):

                detected.append(
                    skill
                )

                break

    return sorted(
        detected
    )


# =========================================================
# CATEGORIZE SKILLS
# =========================================================

def categorize_skills(skills):

    result = {}

    skills_set = set(
        skills
    )

    for category, category_skills in (
        SKILL_CATEGORIES.items()
    ):

        matched = [
            skill
            for skill in category_skills
            if skill in skills_set
        ]

        if matched:

            result[category] = matched

    return result


# =========================================================
# PDF TEXT EXTRACTION
# =========================================================

def extract_pdf_text(filepath):

    text = ""

    try:

        reader = PdfReader(
            filepath
        )

        for page in reader.pages:

            try:

                page_text = (
                    page.extract_text()
                )

                if page_text:

                    text += (
                        "\n"
                        + page_text
                    )

            except Exception:
                continue

    except Exception as e:

        print(
            "PDF extraction error:",
            e
        )

    return text


# =========================================================
# ADZUNA
# =========================================================

def fetch_adzuna_jobs():

    if (
        not ADZUNA_APP_ID
        or not ADZUNA_APP_KEY
    ):

        print(
            "Adzuna credentials not configured."
        )

        return []

    jobs = []

    queries = [
        "software developer",
        "full stack developer",
        "python developer",
        "java developer",
        "frontend developer",
        "backend developer",
        "data analyst",
        "machine learning"
    ]

    for query in queries:

        try:

            # INDIA endpoint
            url = (
                "https://api.adzuna.com/"
                "v1/api/jobs/in/search/1"
            )

            params = {

                "app_id":
                    ADZUNA_APP_ID,

                "app_key":
                    ADZUNA_APP_KEY,

                "results_per_page":
                    20,

                "what":
                    query,

                "where":
                    "India",

                "content-type":
                    "application/json"
            }

            response = requests.get(
                url,
                params=params,
                timeout=15
            )

            if response.status_code != 200:

                print(
                    "Adzuna status:",
                    response.status_code
                )

                continue

            data = response.json()

            results = data.get(
                "results",
                []
            )

            for job in results:

                title = job.get(
                    "title",
                    "Unknown Position"
                )

                description = job.get(
                    "description",
                    ""
                )

                company = job.get(
                    "company",
                    {}
                )

                if isinstance(
                    company,
                    dict
                ):

                    company_name = (
                        company.get(
                            "display_name",
                            "Unknown Company"
                        )
                    )

                else:

                    company_name = str(
                        company
                    )

                location = job.get(
                    "location",
                    {}
                )

                if isinstance(
                    location,
                    dict
                ):

                    location_name = (
                        location.get(
                            "display_name",
                            ""
                        )
                    )

                else:

                    location_name = str(
                        location
                    )

                # -------------------------------------------------
                # INDIA FILTER
                # -------------------------------------------------

                if not is_india_location(
                    location_name
                ):

                    continue

                searchable = (
                    title
                    + " "
                    + description
                )

                jobs.append({

                    "id":
                        "adzuna_"
                        + str(
                            job.get(
                                "id",
                                ""
                            )
                        ),

                    "title":
                        title,

                    "company":
                        company_name,

                    "location":
                        location_name,

                    "description":
                        description,

                    "url":
                        job.get(
                            "redirect_url",
                            "#"
                        ),

                    "skills":
                        detect_skills(
                            searchable
                        ),

                    "source":
                        "Adzuna"
                })

        except Exception as e:

            print(
                "Adzuna request error:",
                e
            )

    return deduplicate_jobs(
        jobs
    )


# =========================================================
# ARBEITNOW
# =========================================================

def fetch_arbeitnow_jobs():

    jobs = []

    try:

        response = requests.get(
            ARBEITNOW_URL,
            timeout=20
        )

        if response.status_code != 200:

            print(
                "Arbeitnow error:",
                response.status_code
            )

            return []

        data = response.json()

        results = data.get(
            "data",
            []
        )

        for job in results:

            title = job.get(
                "title",
                "Unknown Position"
            )

            description = job.get(
                "description",
                ""
            )

            company = job.get(
                "company_name",
                "Unknown Company"
            )

            location = job.get(
                "location",
                ""
            )

            # -------------------------------------------------
            # INDIA FILTER
            # -------------------------------------------------

            if not is_india_location(
                location
            ):

                continue

            searchable = (
                title
                + " "
                + description
            )

            jobs.append({

                "id":
                    "arbeitnow_"
                    + str(
                        job.get(
                            "slug",
                            ""
                        )
                    ),

                "title":
                    title,

                "company":
                    company,

                "location":
                    location,

                "description":
                    description,

                "url":
                    job.get(
                        "url",
                        "#"
                    ),

                "skills":
                    detect_skills(
                        searchable
                    ),

                "source":
                    "Arbeitnow"
            })

    except Exception as e:

        print(
            "Arbeitnow request error:",
            e
        )

    return deduplicate_jobs(
        jobs
    )


# =========================================================
# REMOVE DUPLICATES
# =========================================================

def deduplicate_jobs(jobs):

    unique = {}

    for job in jobs:

        key = (
            normalize_text(
                job.get(
                    "title",
                    ""
                )
            )
            + "|"
            + normalize_text(
                job.get(
                    "company",
                    ""
                )
            )
            + "|"
            + normalize_text(
                job.get(
                    "location",
                    ""
                )
            )
        )

        if key not in unique:

            unique[key] = job

    return list(
        unique.values()
    )


# =========================================================
# FETCH LIVE JOBS
# =========================================================

def build_job_search_url(source, query):
    """Build an India-focused job search URL. These are search links, not scraped job postings."""
    q = quote_plus(query.strip())

    if source == "LinkedIn":
        # LinkedIn documents location filtering in its Jobs search UI.
        return (
            "https://www.linkedin.com/jobs/search/?"
            f"keywords={q}&geoId=102713980"
        )

    if source == "Indeed":
        return (
            "https://in.indeed.com/jobs?"
            f"q={q}&l=India"
        )

    if source == "Naukri":
        return "https://www.naukri.com/"

    if source == "Internshala":
        return "https://internshala.com/jobs/"

    return "#"


def generate_fallback_search_jobs(student_skills):
    """
    If public job APIs return no India jobs, show honest India job-search
    links instead of an empty dashboard. No fake company/job posting is
    created here; every card opens a real job-board search.
    """
    skill_text = " ".join(student_skills[:5])

    roles = [
        (
            "Full Stack Developer",
            ["HTML", "CSS", "JavaScript", "React", "Node.js", "SQL", "Git"],
        ),
        (
            "Python Developer",
            ["Python", "Django", "Flask", "SQL", "REST API", "Git"],
        ),
        (
            "Backend Developer",
            ["Python", "Java", "SQL", "REST API", "Git", "Docker"],
        ),
        (
            "Frontend Developer",
            ["HTML", "CSS", "JavaScript", "React", "TypeScript", "Git"],
        ),
        (
            "Data Analyst",
            ["Python", "SQL", "Excel", "Power BI", "Pandas", "Statistics"],
        ),
        (
            "Machine Learning Engineer",
            ["Python", "Machine Learning", "Pandas", "NumPy", "Scikit-learn", "SQL"],
        ),
        (
            "Software Developer",
            ["Python", "Java", "C++", "SQL", "DSA", "Git"],
        ),
    ]

    jobs = []
    for role, skills in roles:
        query = role
        if skill_text:
            query += " " + skill_text

        source_links = {
            source: build_job_search_url(source, query)
            for source in ["LinkedIn", "Indeed", "Naukri", "Internshala"]
        }

        jobs.append({
            "id": "search_" + re.sub(r"[^a-z0-9]+", "_", role.lower()).strip("_"),
            "title": role,
            "company": "India job search",
            "location": "India",
            "description": "India-focused job search results for this role.",
            "url": source_links["LinkedIn"],
            "source": "Job-board search links",
            "skills": skills,
            "source_links": source_links,
            "search_only": True,
        })

    return jobs


def fetch_live_jobs(force_refresh=False):
    global JOB_CACHE

    current_time = time.time()

    if (
        not force_refresh
        and JOB_CACHE["jobs"]
        and (current_time - JOB_CACHE["timestamp"]) < CACHE_SECONDS
    ):
        return JOB_CACHE["jobs"]

    all_jobs = []

    adzuna_jobs = fetch_adzuna_jobs()
    if adzuna_jobs:
        print("India Adzuna jobs fetched:", len(adzuna_jobs))
        all_jobs.extend(adzuna_jobs)

    arbeitnow_jobs = fetch_arbeitnow_jobs()
    if arbeitnow_jobs:
        print("India Arbeitnow jobs fetched:", len(arbeitnow_jobs))
        all_jobs.extend(arbeitnow_jobs)

    # Keep only clearly India-based postings from the API sources.
    all_jobs = [
        job for job in all_jobs
        if is_india_location(job.get("location", ""))
    ]

    all_jobs = deduplicate_jobs(all_jobs)

    # Important: an empty public API response must not make the dashboard
    # unusable. Use real job-board search links as an explicit fallback.
    # The resume-specific skills are added later by recommend_jobs().
    JOB_CACHE["jobs"] = all_jobs
    JOB_CACHE["timestamp"] = current_time

    print("TOTAL INDIA API JOBS:", len(all_jobs))
    return all_jobs

# =========================================================
# MATCH JOB
# =========================================================

def match_job(
    job,
    student_skills
):

    student_set = set(
        skill.lower()
        for skill in student_skills
    )

    job_skills = set(
        skill.lower()
        for skill in job.get(
            "skills",
            []
        )
    )

    job_text = (
        job.get(
            "title",
            ""
        )
        + " "
        + job.get(
            "description",
            ""
        )
    )

    detected = set(
        skill.lower()
        for skill in detect_skills(
            job_text
        )
    )

    job_skills.update(
        detected
    )

    matched = sorted(
        student_set.intersection(
            job_skills
        )
    )

    missing = sorted(
        job_skills.difference(
            student_set
        )
    )

    if job_skills:

        percentage = int(
            (
                len(matched)
                / len(job_skills)
            )
            * 100
        )

    else:

        percentage = 0

    return {

        "title":
            job.get(
                "title",
                "Unknown Position"
            ),

        "role":
            job.get(
                "title",
                "Unknown Position"
            ),

        "company":
            job.get(
                "company",
                "Unknown Company"
            ),

        "location":
            job.get(
                "location",
                "India"
            ),

        "url":
            job.get(
                "url",
                "#"
            ),

        "source":
            job.get(
                "source",
                "Unknown"
            ),

        "matched":
            matched,

        "missing":
            missing,

        "percentage":
            percentage,

        "match_percentage":
            percentage,

        "skills":
            sorted(job_skills),
        "source_links":
            job.get("source_links", {}),
        "search_only":
            bool(job.get("search_only", False))
    }


# =========================================================
# RECOMMEND JOBS
# =========================================================

def recommend_jobs(student_skills):
    jobs = fetch_live_jobs()

    # No API results -> use India job-board search links.
    if not jobs:
        jobs = generate_fallback_search_jobs(student_skills)

    recommendations = []

    for job in jobs:
        result = match_job(job, student_skills)
        recommendations.append(result)

    recommendations.sort(
        key=lambda x: (x["percentage"], len(x["matched"])),
        reverse=True,
    )

    return recommendations[:20]

# =========================================================
# GENERATE JOB PROFILES
# =========================================================

def generate_job_profiles(
    live_jobs
):

    profiles = {}

    for result in live_jobs:

        title = normalize_text(
            result.get(
                "title",
                ""
            )
        )

        for profile_name, keywords in (
            ROLE_KEYWORDS.items()
        ):

            matched_role = False

            for keyword in keywords:

                if keyword in title:

                    matched_role = True

                    break

            if not matched_role:

                continue

            if profile_name not in profiles:

                profiles[profile_name] = {

                    "name":
                        profile_name,

                    "jobs_count":
                        0,

                    "total_percentage":
                        0,

                    "common_skills":
                        set(),

                    "missing":
                        set()
                }

            profile = profiles[
                profile_name
            ]

            profile[
                "jobs_count"
            ] += 1

            profile[
                "total_percentage"
            ] += result[
                "percentage"
            ]

            for skill in result.get(
                "skills",
                []
            ):

                profile[
                    "common_skills"
                ].add(
                    skill
                )

            for skill in result.get(
                "missing",
                []
            ):

                profile[
                    "missing"
                ].add(
                    skill
                )

    final_profiles = []

    for profile_name, data in (
        profiles.items()
    ):

        if data["jobs_count"]:

            percentage = int(
                data["total_percentage"]
                / data["jobs_count"]
            )

        else:

            percentage = 0

        final_profiles.append({

            "name":
                data["name"],

            "percentage":
                max(
                    0,
                    min(
                        100,
                        percentage
                    )
                ),

            "jobs_count":
                data["jobs_count"],

            "common_skills":
                sorted(
                    data[
                        "common_skills"
                    ]
                )[:10],

            "missing":
                sorted(
                    data[
                        "missing"
                    ]
                )[:10]
        })

    final_profiles.sort(
        key=lambda x: (
            x["jobs_count"],
            x["percentage"]
        ),
        reverse=True
    )

    return final_profiles[:10]


# =========================================================
# MISSING SKILLS
# =========================================================

def calculate_missing_skills(
    live_jobs,
    student_skills
):

    student_set = set(
        skill.lower()
        for skill in student_skills
    )

    frequency = {}

    for job in live_jobs:

        for skill in job.get(
            "missing",
            []
        ):

            if skill.lower() in student_set:

                continue

            frequency[skill] = (
                frequency.get(
                    skill,
                    0
                )
                + 1
            )

    sorted_skills = sorted(
        frequency.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return [
        skill
        for skill, count
        in sorted_skills[:15]
    ]


# =========================================================
# ROADMAP
# =========================================================

def generate_roadmap(
    missing_skills
):

    roadmap = []

    step_number = 1

    for skill in missing_skills:

        roadmap.append({

            "step":
                f"Step {step_number}: "
                f"Learn {skill}",

            "description":
                f"Build practical knowledge "
                f"of {skill} and create "
                f"at least one project.",

            "skill":
                skill
        })

        step_number += 1

    roadmap.append({

        "step":
            f"Step {step_number}: "
            "Practice Data Structures & Algorithms",

        "description":
            "Practice arrays, strings, "
            "hash maps, stacks, queues "
            "and basic algorithms.",

        "skill":
            "Data Structures"
    })

    step_number += 1

    roadmap.append({

        "step":
            f"Step {step_number}: "
            "Interview Preparation",

        "description":
            "Practice technical questions, "
            "SQL, projects and HR questions.",

        "skill":
            "Interview"
    })

    return roadmap[:15]


# =========================================================
# COMPLETE ANALYSIS
# =========================================================

def analyze_resume(text):

    detected_skills = detect_skills(
        text
    )

    categorized_skills = (
        categorize_skills(
            detected_skills
        )
    )

    live_jobs = recommend_jobs(
        detected_skills
    )

    job_profiles = (
        generate_job_profiles(
            live_jobs
        )
    )

    missing_skills = (
        calculate_missing_skills(
            live_jobs,
            detected_skills
        )
    )

    roadmap = generate_roadmap(
        missing_skills
    )

    return {

        "detected_skills":
            detected_skills,

        "categorized_skills":
            categorized_skills,

        "live_jobs":
            live_jobs,

        "job_profiles":
            job_profiles,

        "missing_skills":
            missing_skills,

        "roadmap":
            roadmap
    }


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():

    if "user_id" in session:

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "index.html"
    )


# =========================================================
# REGISTER
# =========================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if (
            not name
            or not email
            or not password
        ):

            flash(
                "Please fill all fields.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        try:

            db = get_db()

            cursor = db.cursor(
                dictionary=True
            )

            cursor.execute(
                """
                SELECT id
                FROM users
                WHERE email = %s
                """,
                (email,)
            )

            existing = cursor.fetchone()

            if existing:

                cursor.close()
                db.close()

                flash(
                    "Email already registered.",
                    "error"
                )

                return redirect(
                    url_for("register")
                )

            hashed_password = (
                generate_password_hash(
                    password
                )
            )

            cursor.execute(
                """
                INSERT INTO users
                (name, email, password)
                VALUES (%s, %s, %s)
                """,
                (
                    name,
                    email,
                    hashed_password
                )
            )

            db.commit()

            cursor.close()
            db.close()

            flash(
                "Registration successful. Please login.",
                "success"
            )

            return redirect(
                url_for("login")
            )

        except Exception as e:

            print(
                "Registration error:",
                e
            )

            flash(
                "Registration failed.",
                "error"
            )

    return render_template(
        "register.html"
    )


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        try:

            db = get_db()

            cursor = db.cursor(
                dictionary=True
            )

            cursor.execute(
                """
                SELECT *
                FROM users
                WHERE email = %s
                """,
                (email,)
            )

            user = cursor.fetchone()

            cursor.close()
            db.close()

            if not user:

                flash(
                    "Invalid email or password.",
                    "error"
                )

                return redirect(
                    url_for("login")
                )

            stored_password = user.get(
                "password",
                ""
            )

            valid_password = False

            try:

                valid_password = (
                    check_password_hash(
                        stored_password,
                        password
                    )
                )

            except Exception:

                valid_password = False

            # Backward compatibility with old
            # plain-text passwords.
            if not valid_password:

                valid_password = (
                    stored_password
                    == password
                )

            if not valid_password:

                flash(
                    "Invalid email or password.",
                    "error"
                )

                return redirect(
                    url_for("login")
                )

            session["user_id"] = (
                user["id"]
            )

            session["user_name"] = (
                user.get(
                    "name",
                    ""
                )
            )

            session["user_email"] = (
                user.get(
                    "email",
                    ""
                )
            )

            return redirect(
                url_for("dashboard")
            )

        except Exception as e:

            print(
                "Login error:",
                e
            )

            flash(
                "Login failed.",
                "error"
            )

    return render_template(
        "login.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("index")
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    latest_resume = None

    resume_count = 0

    try:

        db = get_db()

        cursor = db.cursor(
            dictionary=True
        )

        # -------------------------------------------------
        # Latest resume
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT *
            FROM resumes
            WHERE user_id = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                session["user_id"],
            )
        )

        latest_resume = (
            cursor.fetchone()
        )

        # -------------------------------------------------
        # Resume count
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM resumes
            WHERE user_id = %s
            """,
            (
                session["user_id"],
            )
        )

        row = cursor.fetchone()

        if row:
            # mysql.connector dictionary cursors normally return `total`.
            # Keep a safe fallback so the card never shows 0 when a latest
            # resume was successfully found.
            try:
                resume_count = int(row.get("total", 0) or 0)
            except Exception:
                resume_count = 0

        if latest_resume and resume_count < 1:
            resume_count = 1

        cursor.close()
        db.close()

    except Exception as e:

        print(
            "Resume database error:",
            e
        )

    # -----------------------------------------------------
    # No resume
    # -----------------------------------------------------

    if not latest_resume:

        return render_template(

            "dashboard.html",

            username=
                session.get(
                    "user_name",
                    "Student"
                ),

            latest_resume=None,

            detected_skills=[],

            categorized_skills={},

            job_profiles=[],

            live_jobs=[],

            missing_skills=[],

            roadmap=[],

            resume_count=
                resume_count,

            skill_count=0,

            job_count=0,

            profile_count=0,

            job_profiles_count=0,

            recommended_jobs_count=0,

            skills_to_improve_count=0
        )

    # -----------------------------------------------------
    # Resume path
    # -----------------------------------------------------

    filename = latest_resume.get(
        "filename",
        ""
    )

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    resume_text = ""

    if os.path.exists(filepath):

        resume_text = (
            extract_pdf_text(
                filepath
            )
        )

    # -----------------------------------------------------
    # Analyze
    # -----------------------------------------------------

    analysis = analyze_resume(
        resume_text
    )

    return render_template(

        "dashboard.html",

        username=
            session.get(
                "user_name",
                "Student"
            ),

        latest_resume=
            latest_resume,

        detected_skills=
            analysis[
                "detected_skills"
            ],

        categorized_skills=
            analysis[
                "categorized_skills"
            ],

        job_profiles=
            analysis[
                "job_profiles"
            ],

        live_jobs=
            analysis[
                "live_jobs"
            ],

        missing_skills=
            analysis[
                "missing_skills"
            ],

        roadmap=
            analysis[
                "roadmap"
            ],

        # Statistics expected by dashboard.html

        resume_count=
            resume_count,

        skill_count=
            len(
                analysis[
                    "detected_skills"
                ]
            ),

        job_count=
            len(
                analysis[
                    "live_jobs"
                ]
            ),

        profile_count=
            len(
                analysis[
                    "job_profiles"
                ]
            ),

        # Backward-compatible names

        job_profiles_count=
            len(
                analysis[
                    "job_profiles"
                ]
            ),

        recommended_jobs_count=
            len(
                analysis[
                    "live_jobs"
                ]
            ),

        skills_to_improve_count=
            len(
                analysis[
                    "missing_skills"
                ]
            )
    )


# =========================================================
# RESUME
# =========================================================

@app.route(
    "/resume",
    methods=["GET", "POST"]
)
def resume():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    # -----------------------------------------------------
    # POST = UPLOAD RESUME
    # -----------------------------------------------------

    if request.method == "POST":

        file = request.files.get(
            "resume"
        )

        if not file:

            flash(
                "Please select a resume.",
                "error"
            )

            return redirect(
                url_for("dashboard")
            )

        if not file.filename:

            flash(
                "Please select a resume.",
                "error"
            )

            return redirect(
                url_for("dashboard")
            )

        if not file.filename.lower().endswith(
            ".pdf"
        ):

            flash(
                "Only PDF resumes are supported.",
                "error"
            )

            return redirect(
                url_for("dashboard")
            )

        filename = secure_filename(
            file.filename
        )

        if not filename:

            flash(
                "Invalid filename.",
                "error"
            )

            return redirect(
                url_for("dashboard")
            )

        timestamp = str(
            int(time.time())
        )

        base, ext = os.path.splitext(
            filename
        )

        filename = (
            base
            + "_"
            + timestamp
            + ext
        )

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        try:

            file.save(
                filepath
            )

            # Make sure PDF can actually be read
            try:

                PdfReader(
                    filepath
                )

            except Exception:

                if os.path.exists(
                    filepath
                ):

                    os.remove(
                        filepath
                    )

                flash(
                    "The uploaded file is not a valid PDF.",
                    "error"
                )

                return redirect(
                    url_for("dashboard")
                )

            db = get_db()

            cursor = db.cursor()

            cursor.execute(
                """
                INSERT INTO resumes
                (user_id, filename)
                VALUES (%s, %s)
                """,
                (
                    session["user_id"],
                    filename
                )
            )

            db.commit()

            cursor.close()
            db.close()

            flash(
                "Resume analyzed successfully.",
                "success"
            )

            return redirect(
                url_for("dashboard")
            )

        except Exception as e:

            print(
                "Resume analysis error:",
                e
            )

            if os.path.exists(
                filepath
            ):

                try:

                    os.remove(
                        filepath
                    )

                except Exception:
                    pass

            flash(
                "Resume analysis failed.",
                "error"
            )

            return redirect(
                url_for("dashboard")
            )

    # -----------------------------------------------------
    # GET
    # -----------------------------------------------------

    return redirect(
        url_for("dashboard")
    )


# =========================================================
# UPLOAD ROUTE
# =========================================================
@app.route("/upload", methods=["GET", "POST"])
def upload():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        file = request.files.get("resume")

        if not file or not file.filename:
            flash("Please select a resume.", "error")
            return redirect(url_for("dashboard"))

        if not file.filename.lower().endswith(".pdf"):
            flash("Only PDF resumes are supported.", "error")
            return redirect(url_for("dashboard"))

        filename = secure_filename(file.filename)

        timestamp = str(int(time.time()))

        base, ext = os.path.splitext(filename)

        filename = base + "_" + timestamp + ext

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        try:

            file.save(filepath)

            try:
                PdfReader(filepath)

            except Exception:

                if os.path.exists(filepath):
                    os.remove(filepath)

                flash(
                    "The uploaded file is not a valid PDF.",
                    "error"
                )

                return redirect(url_for("dashboard"))

            db = get_db()

            cursor = db.cursor()

            cursor.execute(
                """
                INSERT INTO resumes
                (user_id, filename)
                VALUES (%s, %s)
                """,
                (
                    session["user_id"],
                    filename
                )
            )

            db.commit()

            cursor.close()
            db.close()

            flash(
                "Resume uploaded successfully.",
                "success"
            )

            return redirect(url_for("dashboard"))

        except Exception as e:

            print("Upload error:", e)

            flash(
                "Resume upload failed.",
                "error"
            )

            return redirect(url_for("dashboard"))

    # GET /upload
    # We don't need upload.html anymore.
    return redirect(url_for("dashboard"))


# =========================================================
# SAVE ROADMAP PROGRESS
# =========================================================

@app.route(
    "/save-progress",
    methods=["POST"]
)
def save_progress():

    if "user_id" not in session:

        return jsonify({

            "success":
                False,

            "message":
                "Not logged in"

        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    job = data.get(
        "job",
        ""
    )

    step = data.get(
        "step",
        ""
    )

    completed = data.get(
        "completed",
        False
    )

    if not job or not step:

        return jsonify({

            "success":
                False,

            "message":
                "Missing data"

        }), 400

    try:

        db = get_db()

        cursor = db.cursor()

        cursor.execute(
            """
            SELECT id
            FROM roadmap_progress
            WHERE user_id = %s
            AND job = %s
            AND step = %s
            """,
            (
                session["user_id"],
                job,
                step
            )
        )

        existing = cursor.fetchone()

        completed_value = int(
            bool(
                completed
            )
        )

        if existing:

            cursor.execute(
                """
                UPDATE roadmap_progress
                SET completed = %s
                WHERE id = %s
                """,
                (
                    completed_value,
                    existing[0]
                )
            )

        else:

            cursor.execute(
                """
                INSERT INTO roadmap_progress
                (user_id, job, step, completed)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    session["user_id"],
                    job,
                    step,
                    completed_value
                )
            )

        db.commit()

        cursor.close()
        db.close()

        return jsonify({

            "success":
                True

        })

    except Exception as e:

        print(
            "Progress save error:",
            e
        )

        return jsonify({

            "success":
                False,

            "message":
                str(e)

        }), 500


# =========================================================
# API - LIVE JOBS
# =========================================================

@app.route("/api/jobs")
def api_jobs():

    if "user_id" not in session:

        return jsonify({

            "success":
                False,

            "message":
                "Login required"

        }), 401

    refresh = request.args.get(
        "refresh",
        "0"
    )

    jobs = fetch_live_jobs(

        force_refresh=(
            refresh == "1"
        )

    )

    # Extra safety filter before returning API data

    jobs = [

        job
        for job in jobs

        if is_india_location(
            job.get(
                "location",
                ""
            )
        )

    ]

    return jsonify({

        "success":
            True,

        "count":
            len(jobs),

        "location":
            "India",

        "adzuna_configured":
            bool(
                ADZUNA_APP_ID
                and ADZUNA_APP_KEY
            ),

        "jobs":
            jobs[:50]
    })


# =========================================================
# API TEST
# =========================================================

@app.route("/api/test")
def api_test():

    jobs = fetch_live_jobs(
        force_refresh=True
    )

    india_jobs = [

        job
        for job in jobs

        if is_india_location(
            job.get(
                "location",
                ""
            )
        )

    ]

    return jsonify({

        "status":
            "ok",

        "location":
            "India",

        "total_jobs":
            len(india_jobs),

        "adzuna_configured":
            bool(
                ADZUNA_APP_ID
                and ADZUNA_APP_KEY
            ),

        "sources": {

            "adzuna":
                len([
                    j
                    for j in india_jobs

                    if j.get(
                        "source"
                    ) == "Adzuna"
                ]),

            "arbeitnow":
                len([
                    j
                    for j in india_jobs

                    if j.get(
                        "source"
                    ) == "Arbeitnow"
                ])
        }
    })


# =========================================================
# RUN APP
# =========================================================

if __name__ == "__main__":

    print()

    print(
        "=" * 60
    )

    print(
        "PLACEMENT TRACKER"
    )

    print(
        "=" * 60
    )

    print(
        "Adzuna configured:",
        bool(
            ADZUNA_APP_ID
            and ADZUNA_APP_KEY
        )
    )

    print(
        "Arbeitnow:",
        "Enabled"
    )

    print(
        "Job location:",
        "INDIA ONLY"
    )

    print(
        "Remote-only international jobs:",
        "Blocked"
    )

    print(
        "=" * 60
    )

    print()

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )