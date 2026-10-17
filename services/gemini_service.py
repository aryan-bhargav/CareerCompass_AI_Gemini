
import os

import streamlit as st
from google import genai
from google.genai import types


MODEL_NAME = "gemini-2.5-flash"


def get_api_key() -> str:
    """Read the Gemini key from Streamlit secrets or environment."""

    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        key = ""

    return key or os.getenv("GEMINI_API_KEY", "")


def generate_response(prompt: str) -> str:
    """Send a prompt to Gemini and return its text response."""

    api_key = get_api_key()

    if not api_key:
        return (
            "Gemini API key configure nahi hai.\n\n"
            "Project ke `.streamlit/secrets.toml` mein "
            "`GEMINI_API_KEY` add karo."
        )

    try:
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4,
                max_output_tokens=1800,
            ),
        )

        if not response.text:
            return "Gemini ne empty response diya. Dobara try karo."

        return response.text.strip()

    except Exception as error:
        # API key aur request headers ko error message mein expose mat karo.
        error_type = type(error).__name__

        return (
            "Gemini request fail ho gayi.\n\n"
            "API key, internet connection, model availability "
            "aur API quota check karo.\n\n"
            f"Error type: {error_type}"
        )


def generate_learning_roadmap(
    user_skills: list[str],
    missing_skills: list[str],
    role: str,
    level: str,
    goal: str,
) -> str:
    """Generate a personalized four-week learning roadmap."""

    prompt = f"""
You are a practical career-learning assistant for college students.

Create a realistic four-week learning roadmap.

Target role: {role}
Experience level: {level}
Career goal: {goal}
Current skills: {", ".join(user_skills) or "Not provided"}
Identified skill gaps: {", ".join(missing_skills) or "None identified"}

Instructions:
1. Use Markdown headings for Week 1, Week 2, Week 3 and Week 4.
2. Give three to five actionable tasks per week.
3. Start with fundamentals and gradually increase difficulty.
4. Include practical exercises and one portfolio project.
5. Include interview preparation and resume improvement.
6. Prefer free learning resources.
7. Do not invent resource URLs.
8. Do not guarantee employment or certification.
9. End with three measurable completion criteria.
10. Keep the plan suitable for a college student.

Return only the roadmap in Markdown.
"""

    return generate_response(prompt)


def explain_career_match(
    user_skills: list[str],
    role_result: dict,
) -> str:
    """Explain why a recommended career may fit the user's profile."""

    prompt = f"""
You are a career advisor helping a college student explore job roles.

Target role: {role_result.get("role", "Unknown")}
Role description: {role_result.get("description", "")}
User skills: {", ".join(user_skills)}
Matched skills: {", ".join(role_result.get("matched_skills", []))}
Missing skills: {", ".join(role_result.get("missing_skills", []))}
Prototype match score: {role_result.get("match_score", 0)}%

Explain in simple language:
1. Why this role appeared in the recommendations.
2. Which existing skills are relevant.
3. Which skills should be developed next.
4. Three practical next steps.

Important:
- The score is a heuristic, not a probability of getting hired.
- Do not invent qualifications or work experience.
- Do not guarantee employment.
- Keep the answer concise and use Markdown.
"""

    return generate_response(prompt)
