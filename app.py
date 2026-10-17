
import streamlit as st
import pandas as pd
import plotly.express as px

from services.recommender import recommend_jobs
from services.gemini_service import (
    explain_career_match,
    generate_learning_roadmap,
)
from services.roadmap import (
    parse_roadmap_text,
    roadmap_to_csv_rows,
    create_fallback_roadmap,
    get_roadmap_metadata,
)


st.set_page_config(
    page_title="CareerCompass AI",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-container {
    padding-top: 1.3rem;
    max-width: 1450px;
}
[data-testid="stSidebar"] {
    background: #111827;
}
[data-testid="stSidebar"] * {
    color: #f3f4f6;
}
.hero {
    padding: 1.5rem;
    border-radius: 16px;
    background: linear-gradient(120deg, #14213d, #244a91);
    color: white;
}
.hero h1 { color: white; }
.hero p { color: #dbeafe; }
</style>
""", unsafe_allow_html=True)


# ---------- SESSION STATE ----------

if "results" not in st.session_state:
    st.session_state.results = None

if "profile" not in st.session_state:
    st.session_state.profile = {}


# ---------- SIDEBAR ----------

with st.sidebar:
    st.markdown("## 🧭 CareerCompass AI")
    st.caption("AI-powered career exploration")

    page = st.radio(
        "NAVIGATION",
        [
            "Overview",
            "Career Explorer",
            "Skill Gap Analysis",
            "AI Learning Roadmap",
            "About Project",
        ],
    )

    st.divider()
    st.markdown("### Your profile")

    name = st.text_input("Name", placeholder="Your name")

    skills_text = st.text_area(
        "Current skills",
        value="Java, DSA, SQL",
        help="Enter comma-separated skills.",
    )

    interests = st.multiselect(
        "Career interests",
        [
            "Software Development",
            "Web Development",
            "Data Analytics",
            "Machine Learning",
            "Cloud & DevOps",
            "Cybersecurity",
        ],
        default=["Software Development"],
    )

    level = st.selectbox(
        "Experience level",
        ["Beginner", "Intermediate", "Advanced"],
    )

    goal = st.selectbox(
        "Career goal",
        [
            "Get an internship",
            "Get an entry-level job",
            "Explore career options",
        ],
    )

    analyze = st.button(
        "Analyze my profile",
        type="primary",
        use_container_width=True,
    )


# ---------- RUN RECOMMENDATION ENGINE ----------

if analyze:
    user_skills = [
        skill.strip()
        for skill in skills_text.split(",")
        if skill.strip()
    ]

    if not user_skills:
        st.sidebar.error("Enter at least one skill.")
    else:
        try:
            results = recommend_jobs(
                user_skills=user_skills,
                interests=interests,
                level=level,
                goal=goal,
            )

            st.session_state.results = results
            st.session_state.profile = {
                "name": name.strip() or "Learner",
                "skills": user_skills,
                "interests": interests,
                "level": level,
                "goal": goal,
            }

        except Exception as error:
            st.error(
                "Could not generate recommendations. "
                "Check data/job_roles.csv and recommender.py."
            )
            st.caption(f"Error type: {type(error).__name__}")


results = st.session_state.results
profile = st.session_state.profile

skills = profile.get("skills", [])
display_name = profile.get("name", "Learner")


# ---------- OVERVIEW ----------

if page == "Overview":
    st.markdown(
        f"""
        <div class="hero">
            <h1>Welcome, {display_name} 👋</h1>
            <p>Discover suitable career roles and identify your next skills.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not results:
        st.subheader("Start your career analysis")
        st.write(
            "Fill in your profile in the sidebar and click "
            "**Analyze my profile**."
        )

        c1, c2, c3 = st.columns(3)
        c1.info("🎯 Career Explorer\n\nExplore relevant job roles.")
        c2.info("🧩 Skill Gap Analysis\n\nFind skills you need to develop.")
        c3.info("✨ AI Roadmap\n\nGenerate a learning plan using Gemini.")

    else:
        top_match = results[0]

        skill_gaps = len({
            skill
            for role in results[:5]
            for skill in role["missing_skills"]
        })

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Top match", f'{top_match["match_score"]}%')
        c2.metric("Your skills", len(skills))
        c3.metric("Roles analyzed", len(results))
        c4.metric("Skill gaps", skill_gaps)

        left, right = st.columns([1.1, 1])

        with left:
            st.subheader("Top career matches")

            for role in results[:3]:
                with st.container(border=True):
                    st.subheader(role["role"])
                    st.caption(role["category"])
                    st.write(role["description"])

                    st.progress(
                        role["match_score"] / 100,
                        text=f'{role["match_score"]}% heuristic match',
                    )

                    st.write(
                        "**Matched:** "
                        + (", ".join(role["matched_skills"]) or "None")
                    )

                    st.write(
                        "**To develop:** "
                        + (", ".join(role["missing_skills"][:5]) or "None")
                    )

        with right:
            st.subheader("Career match comparison")

            chart_data = pd.DataFrame([
                {
                    "Role": role["role"],
                    "Score": role["match_score"],
                }
                for role in results[:7]
            ])

            fig = px.bar(
                chart_data,
                x="Score",
                y="Role",
                orientation="h",
                range_x=[0, 100],
                text="Score",
            )

            fig.update_layout(
                height=420,
                margin=dict(l=5, r=15, t=10, b=5),
            )

            fig.update_traces(
                texttemplate="%{text}%",
                textposition="outside",
            )

            st.plotly_chart(fig, use_container_width=True)

        st.info(
            "Scores are prototype ranking indicators, not probabilities "
            "of getting hired."
        )


# ---------- CAREER EXPLORER ----------

elif page == "Career Explorer":
    st.title("🎯 Career Explorer")

    if not results:
        st.warning("Analyze your profile first.")
    else:
        categories = sorted({
            role["category"] for role in results
        })

        selected_category = st.selectbox(
            "Filter by category",
            ["All"] + categories,
        )

        for role in results:
            if (
                selected_category != "All"
                and role["category"] != selected_category
            ):
                continue

            with st.container(border=True):
                left, right = st.columns([3, 1])

                with left:
                    st.subheader(role["role"])
                    st.caption(role["description"])

                    st.progress(
                        role["match_score"] / 100,
                        text=f'{role["match_score"]}% match',
                    )

                with right:
                    st.metric("Match score", f'{role["match_score"]}%')
                    st.caption(role["category"])

                a, b = st.columns(2)

                with a:
                    st.markdown("**Skills you have**")
                    st.write(
                        ", ".join(role["matched_skills"]) or "No direct matches"
                    )

                with b:
                    st.markdown("**Skills to develop**")
                    st.write(
                        ", ".join(role["missing_skills"]) or "None listed"
                    )

                with st.expander("Explain this career match with Gemini"):
                    if st.button(
                        "Generate explanation",
                        key="explain_" + role["role"],
                    ):
                        with st.spinner("Asking Gemini..."):
                            explanation = explain_career_match(
                                skills,
                                role,
                            )

                            st.session_state[
                                "explanation_" + role["role"]
                            ] = explanation

                    explanation = st.session_state.get(
                        "explanation_" + role["role"]
                    )

                    if explanation:
                        st.markdown(explanation)


# ---------- SKILL GAP ANALYSIS ----------

elif page == "Skill Gap Analysis":
    st.title("🧩 Skill Gap Analysis")

    if not results:
        st.warning("Analyze your profile first.")
    else:
        counts = {}

        for role in results[:5]:
            for skill in role["missing_skills"]:
                counts[skill] = counts.get(skill, 0) + 1

        if not counts:
            st.success("No missing skills found in the displayed roles.")
        else:
            gap_df = pd.DataFrame([
                {
                    "Skill": skill.title(),
                    "Relevant roles": count,
                }
                for skill, count in counts.items()
            ])

            gap_df = gap_df.sort_values(
                "Relevant roles",
                ascending=False,
            )

            left, right = st.columns([1.2, 1])

            with left:
                fig = px.bar(
                    gap_df.head(10).sort_values("Relevant roles"),
                    x="Relevant roles",
                    y="Skill",
                    orientation="h",
                    text="Relevant roles",
                )

                fig.update_layout(height=420)
                st.plotly_chart(fig, use_container_width=True)

            with right:
                st.subheader("Priority skills")
                st.dataframe(gap_df, hide_index=True)

                st.download_button(
                    "Download skill gap report",
                    gap_df.to_csv(index=False).encode("utf-8"),
                    file_name="skill_gap_report.csv",
                    mime="text/csv",
                )


# ---------- GEMINI LEARNING ROADMAP ----------

elif page == "AI Learning Roadmap":
    st.title("✨ AI Learning Roadmap")

    if not results:
        st.warning("Analyze your profile first.")
    else:
        selected_role_name = st.selectbox(
            "Choose your target role",
            [role["role"] for role in results],
        )

        selected_role = next(
            role for role in results
            if role["role"] == selected_role_name
        )

        st.write("**Current skills:**", ", ".join(skills))

        st.write(
            "**Skills to develop:**",
            ", ".join(selected_role["missing_skills"]) or "None listed",
        )

        if st.button(
            "Generate roadmap with Gemini",
            type="primary",
        ):
            with st.spinner("Generating your personalized roadmap..."):
                roadmap_text = generate_learning_roadmap(
                    user_skills=skills,
                    missing_skills=selected_role["missing_skills"],
                    role=selected_role["role"],
                    level=profile.get("level", "Beginner"),
                    goal=profile.get("goal", "Explore career options"),
                )

                st.session_state[
                    "roadmap_" + selected_role_name
                ] = roadmap_text

        roadmap_text = st.session_state.get(
            "roadmap_" + selected_role_name
        )

        if roadmap_text:
            st.markdown(roadmap_text)

            sections = parse_roadmap_text(roadmap_text)
            rows = roadmap_to_csv_rows(sections)

            if rows:
                roadmap_df = pd.DataFrame(rows)

                st.download_button(
                    "Download roadmap tasks as CSV",
                    roadmap_df.to_csv(index=False).encode("utf-8"),
                    file_name="learning_roadmap.csv",
                    mime="text/csv",
                )

            st.download_button(
                "Download full roadmap as TXT",
                roadmap_text.encode("utf-8"),
                file_name="learning_roadmap.txt",
                mime="text/plain",
            )

            metadata = get_roadmap_metadata(selected_role_name)
            st.caption(
                f'Created: {metadata["created_date"]} · '
                f'Duration: {metadata["duration"]}'
            )

            st.caption(
                "Verify AI-generated advice and resources before relying on them."
            )


# ---------- ABOUT ----------

else:
    st.title("ℹ️ About CareerCompass AI")

    st.markdown("""
    **Problem:** Students may struggle to map their current skills to
    entry-level roles and identify what to learn next.

    **Solution:** CareerCompass recommends sample roles, identifies
    skill gaps, and uses Gemini to generate personalized learning plans.

    **SDG alignment:** SDG 8 — Decent Work and Economic Growth.

    **Recommendation engine:** TF-IDF, cosine similarity, and direct
    skill overlap.

    **Generative AI:** Gemini API generates career explanations and
    learning roadmaps when requested.

    **Limitations:** The included dataset is illustrative, not live job
    market data. Match scores are heuristics, not hiring probabilities.
    """)

    st.markdown(
        "**Tech stack:** Python · Streamlit · Pandas · "
        "Scikit-learn · Plotly · Google Gemini API"
    )
