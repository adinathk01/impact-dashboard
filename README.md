
# Impact Measurement Dashboard (Streamlit Prototype)

This is a prototype Streamlit app for the **Impact Measurement & Reporting** agent for Anudip Foundation.
It uses a Google Sheet or a CSV file as input and provides KPIs, charts and an AI-generated (or rule-based) summary.

## What is included
- `app.py` : Streamlit application
- `requirements.txt` : Python dependencies
- `README.md` : Setup and deployment instructions

## How it works (non-technical)
1. The app reads training data from either a local CSV or a Google Sheet.
2. It computes KPIs (e.g., trainees, placements, completion rates).
3. It displays charts and an executive summary.
4. If you provide an OpenAI API key, the app will use OpenAI to generate a natural-language summary. If no key is provided, the app uses a built-in rule-based summary (no cost).

## Setup Steps (quick)
### 1) Prepare environment
- Create a GitHub repo with the project files.
- Deploy to Streamlit Cloud (https://streamlit.io/cloud). Follow Streamlit Cloud prompts to connect GitHub and deploy.

### 2) Use Google Sheets as data source (optional)
- Create or copy a Google Sheet with your data in the top worksheet.
- Share the sheet with a Google Service Account (email) or allow the service account access.
- Save the service account JSON as `service_account.json` in the app folder or paste it into Streamlit secrets (recommended).

### 3) Deploy on Streamlit Cloud
- Push `app.py`, `requirements.txt`, and `impact_data.csv` to GitHub.
- Connect the repo on Streamlit Cloud and deploy.
- Add your OpenAI API key in Streamlit secrets as `OPENAI_API_KEY` to enable LLM summaries (optional).
- To use Google Sheets, either upload service_account.json (not recommended) or paste JSON into Streamlit Secrets following Streamlit instructions.

## Notes & Security
- Do not share personal identifiers with external APIs. Anonymize trainee IDs before external calls.
- OpenAI usage may incur costs. If you don't want costs, leave the OpenAI API key empty — the app will fall back to rule-based summaries that are free.

## Next steps
- Connect to your real CMIS / LMS exports.
- Improve summary templates and add more KPI types.
- Add automatic scheduling & email distribution via an automation tool or background task runner.
