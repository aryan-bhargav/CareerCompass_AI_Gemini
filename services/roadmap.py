
from datetime import date


def create_fallback_roadmap(
    role: str,
    missing_skills: list[str],
) -> dict:
    """
    Create a basic roadmap when Gemini is unavailable.
    This is a fallback, not an AI-generated response.
    """

    skills = [skill.title() for skill in missing_skills]

    if not skills:
        skills = [
            "Portfolio Project",
            "Interview Preparation",
        ]

    return {
        "Week 1 - Fundamentals": [
            f"Learn the fundamentals of {skill}."
            for skill in skills[:2]
        ],
        "Week 2 - Practice": [
            f"Complete practical exercises involving {skill}."
            for skill in (skills[2:4] or skills[:2])
        ],
        "Week 3 - Portfolio Project": [
            f"Build a small project relevant to {role}.",
            "Write a README explaining the project and setup.",
            "Capture genuine screenshots of the working application.",
        ],
        "Week 4 - Job Preparation": [
            "Review the skills required in current job postings.",
            "Practice role-specific interview questions.",
            "Update your resume with skills you can demonstrate.",
        ],
    }


def parse_roadmap_text(roadmap_text: str) -> list[dict]:
    """
    Convert a Markdown roadmap into a list of sections.

    Returns:
        [
            {
                "title": "Week 1 - Fundamentals",
                "tasks": ["Task 1", "Task 2"]
            }
        ]
    """

    sections = []
    current_section = None

    for raw_line in roadmap_text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if line.startswith("#"):
            title = line.lstrip("#").strip()

            current_section = {
                "title": title,
                "tasks": [],
            }

            sections.append(current_section)
            continue

        if line.startswith(("-", "*")):
            task = line.lstrip("-* ").strip()

            if task and current_section is not None:
                current_section["tasks"].append(task)

    return sections


def roadmap_to_csv_rows(
    sections: list[dict],
) -> list[dict]:
    """Convert roadmap sections into rows suitable for CSV export."""

    rows = []

    for section in sections:
        for task in section.get("tasks", []):
            rows.append({
                "Week": section.get("title", ""),
                "Task": task,
                "Status": "Not started",
            })

    return rows


def get_roadmap_metadata(role: str) -> dict:
    """Return basic metadata for a roadmap."""

    return {
        "target_role": role,
        "created_date": date.today().isoformat(),
        "duration": "4 weeks",
    }
