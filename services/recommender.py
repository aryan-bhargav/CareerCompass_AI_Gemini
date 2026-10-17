
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


DATA_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "job_roles.csv"
)

SKILL_ALIASES = {
    "dsa": "data structures algorithms",
    "data structures": "data structures algorithms",
    "algorithms": "data structures algorithms",
    "oops": "object oriented programming",
    "oop": "object oriented programming",
    "js": "javascript",
    "reactjs": "react",
    "react.js": "react",
    "nodejs": "node.js",
    "ml": "machine learning",
    "powerbi": "power bi",
    "postgres": "postgresql",
}


def normalize_skill(skill: str) -> str:
    """Normalize common skill names and abbreviations."""
    value = str(skill).strip().lower()
    return SKILL_ALIASES.get(value, value)


def load_job_roles() -> pd.DataFrame:
    """Load and validate the local job-role dataset."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Job dataset not found: {DATA_PATH}"
        )

    df = pd.read_csv(DATA_PATH)

    required_columns = {
        "role",
        "category",
        "description",
        "required_skills",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing dataset columns: {sorted(missing_columns)}"
        )

    df = df.dropna(
        subset=["role", "category", "required_skills"]
    ).copy()

    df = df.drop_duplicates(subset=["role"])

    for column in required_columns:
        df[column] = df[column].astype(str).str.strip()

    return df


def parse_skills(value: str) -> list[str]:
    """Convert comma-separated skills into normalized values."""
    if not value:
        return []

    skills = [
        normalize_skill(skill)
        for skill in value.split(",")
        if skill.strip()
    ]

    # Remove duplicates while preserving input order.
    return list(dict.fromkeys(skills))


def recommend_jobs(
    user_skills: list[str],
    interests: list[str] | None = None,
    level: str = "Beginner",
    goal: str = "Explore career options",
    top_n: int = 8,
) -> list[dict]:
    """
    Rank sample career roles using:
    1. Direct skill overlap
    2. TF-IDF text similarity
    3. A small interest-category bonus

    The resulting score is a heuristic, not a hiring probability.
    """
    if top_n < 1:
        raise ValueError("top_n must be at least 1.")

    skills = list(
        dict.fromkeys(
            normalize_skill(skill)
            for skill in user_skills
            if str(skill).strip()
        )
    )

    if not skills:
        return []

    roles = load_job_roles()
    interests = [
        str(item).strip().lower()
        for item in (interests or [])
        if str(item).strip()
    ]

    user_profile = " ".join(
        skills + interests + [level.lower(), goal.lower()]
    )

    role_documents = (
        roles["required_skills"]
        + " "
        + roles["category"]
        + " "
        + roles["description"]
    ).tolist()

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        stop_words="english",
    )

    matrix = vectorizer.fit_transform(
        [user_profile] + role_documents
    )

    similarities = cosine_similarity(
        matrix[0:1],
        matrix[1:],
    ).flatten()

    results = []

    for index, (_, row) in enumerate(roles.iterrows()):
        required_skills = parse_skills(
            row["required_skills"]
        )

        matched_skills = [
            skill
            for skill in required_skills
            if skill in skills
        ]

        missing_skills = [
            skill
            for skill in required_skills
            if skill not in matched_skills
        ]

        overlap = (
            len(matched_skills) / len(required_skills)
            if required_skills
            else 0.0
        )

        category = row["category"].lower()

        interest_bonus = (
            0.05
            if any(
                interest in category
                or category in interest
                for interest in interests
            )
            else 0.0
        )

        similarity = float(similarities[index])

        score = round(
            min(
                100,
                100 * (
                    0.70 * overlap
                    + 0.25 * similarity
                    + interest_bonus
                ),
            )
        )

        results.append({
            "role": row["role"],
            "category": row["category"],
            "description": row["description"],
            "match_score": score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "required_skills": required_skills,
        })

    results.sort(
        key=lambda item: (
            item["match_score"],
            len(item["matched_skills"]),
        ),
        reverse=True,
    )

    return results[:top_n]
