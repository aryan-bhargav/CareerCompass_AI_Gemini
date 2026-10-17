# CareerCompass AI — Gemini Integrated

SDG 8: Decent Work and Economic Growth

## Project structure
- `app.py`: Streamlit UI and page navigation
- `services/recommender.py`: local role ranking using TF-IDF, cosine similarity, and skill overlap
- `services/gemini_service.py`: Gemini API calls for learning roadmaps and career-match explanations
- `data/job_roles.csv`: illustrative job-role dataset
- `.streamlit/secrets.toml.example`: example secret configuration; copy to `secrets.toml` and add your own key
- `requirements.txt`: dependencies

## Setup (Windows PowerShell)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .streamlit\secrets.toml.example .streamlit\secrets.toml
```
Open `.streamlit/secrets.toml`, replace the placeholder with your Gemini API key, then run:
```powershell
streamlit run app.py
```
If PowerShell blocks activation, use the venv interpreter directly:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Gemini logic
1. User clicks “Generate personalized roadmap with Gemini” or “Explain this match with Gemini”.
2. `app.py` passes role/profile data to a function in `services/gemini_service.py`.
3. That service reads the API key from Streamlit secrets or `GEMINI_API_KEY` environment variable.
4. The Google Gen AI SDK sends a prompt to `gemini-2.5-flash`.
5. The generated text is displayed in the UI.

Gemini is called only when the user clicks a relevant button. Do not hardcode or commit the API key. Verify that the model is available to your API key and region.

## Local recommendation logic
The recommender is separate from Gemini. It uses a small sample dataset, normalizes common skill aliases (e.g. DSA), computes text similarity with TF-IDF/cosine similarity, and combines that with skill overlap. The score is a heuristic, not an employment probability.

## Limitations
The role dataset is illustrative, not live job data. Gemini output can be inaccurate; verify resources and learning recommendations. This tool does not guarantee employment.
