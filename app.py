
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from google.oauth2 import service_account
import datetime
import os
import json

# Optional OpenAI integration
# try:
#     import openai
# except Exception:
#     openai = None

# For Google Sheets access
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
except Exception:
    gspread = None

st.set_page_config(page_title="Impact Measurement Dashboard (Prototype)",
                   layout="wide",
                   initial_sidebar_state="expanded")

st.title("Impact Measurement Dashboard — Prototype")

# Sidebar: Data source selection
st.sidebar.header("Data Source & Settings")

data_source = st.sidebar.selectbox("Choose data source", ["Upload CSV (local)", "Google Sheets"])

@st.cache_data(ttl=600)
def load_csv(path):
    return pd.read_csv(path)

@st.cache_data(ttl=600)
def load_sheet(sheet_url, creds_json=None):
# Create credentials from Streamlit Secrets
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )

    # Authorize Google Sheets access
    client = gspread.authorize(creds)

    # Open the sheet by URL
    sheet = client.open_by_url(sheet_url).sheet1
    # sheet = "https://docs.google.com/spreadsheets/d/1pwHqqpEwYKZ0XkQeZ7rGW7Zm4bDperGhRr9ImYiSkAU/edit?usp=sharing"

    # Fetch all records into a DataFrame
    data = sheet.get_all_records()

    # Convert to pandas DataFrame
    df = pd.DataFrame(data)

    # Optional: clean column names
    df.columns = df.columns.str.strip().str.replace(" ", "_").str.lower()

    return df
    
df = pd.DataFrame()

if data_source == "Upload CSV (local)":
    uploaded = st.sidebar.file_uploader("Upload CSV file", type=["csv"], accept_multiple_files=False)
    if uploaded is not None:
        df = load_csv(uploaded)
    else:
        # provide example download link (from bundled sample)
        st.sidebar.info("No CSV uploaded — using bundled sample data for demo.")
        df = pd.read_csv("impact_data.csv")
else:
    st.sidebar.info("To use Google Sheets, share the sheet with the service account email (see README).")
    sheet_url = st.sidebar.text_input("Google Sheet URL or Key", value="")
    # use_secret = st.sidebar.checkbox("Provide service account JSON in secrets (advanced)")
    # creds_json = None
    # if use_secret:
    #     secret_key = st.sidebar.text_area("Paste service account JSON here (or store in Streamlit secrets)")
    #     if secret_key:
    #         try:
    #             creds_json = json.loads(secret_key)
    #         except Exception as e:
    #             st.sidebar.error("Invalid JSON pasted.")
    if sheet_url:
        try:
            df = load_sheet(sheet_url, creds_json=None)
        except Exception as e:
            st.sidebar.error(f"Failed to load sheet: {e}")
            df = pd.DataFrame()

# Basic validation / normalization
if df.empty:
    st.warning("No data loaded yet. Upload a CSV or provide a Google Sheet link, or use the bundled sample data.")
    st.stop()

# Normalize column names (simple cleaning)
df.columns = [c.strip() for c in df.columns]

# Expected columns: Region, Course, Gender, Trainees, Placed, CompletionRate (case-insensitive)
cols = {c.lower(): c for c in df.columns}
def col_name(pref):
    # find a column matching pref (lowercase substring)
    for k, v in cols.items():
        if pref in k:
            return v
    return None

region_col = col_name("region") or "Region"
course_col = col_name("course") or "Course"
gender_col = col_name("gender") or "Gender"
trainees_col = col_name("trainee") or "Trainees"
placed_col = col_name("place") or "Placed"
completion_col = col_name("completion") or "CompletionRate"

# Convert numeric fields
for c in [trainees_col, placed_col, completion_col]:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors='coerce')

# Sidebar filters
st.sidebar.header("Filters")
regions = df[region_col].dropna().unique().tolist() if region_col in df.columns else []
selected_regions = st.sidebar.multiselect("Region", options=regions, default=regions)

courses = df[course_col].dropna().unique().tolist() if course_col in df.columns else []
selected_courses = st.sidebar.multiselect("Course", options=courses, default=courses)

genders = df[gender_col].dropna().unique().tolist() if gender_col in df.columns else []
selected_genders = st.sidebar.multiselect("Gender", options=genders, default=genders)

# Filter dataframe
filtered = df[
    (df[region_col].isin(selected_regions)) &
    (df[course_col].isin(selected_courses)) &
    (df[gender_col].isin(selected_genders))
].copy()

st.markdown("### Key Metrics")
col1, col2, col3, col4 = st.columns(4)
total_tr = int(filtered[trainees_col].sum()) if trainees_col in filtered.columns else 0
total_placed = int(filtered[placed_col].sum()) if placed_col in filtered.columns else 0
avg_completion = round(filtered[completion_col].mean(), 2) if completion_col in filtered.columns else 0.0
placement_rate = round((total_placed / total_tr * 100) if total_tr > 0 else 0.0, 2)

col1.metric("Total Trainees", total_tr)
col2.metric("Total Placed", total_placed)
col3.metric("Avg Completion (%)", avg_completion)
col4.metric("Placement Rate (%)", placement_rate)

st.markdown("---")
# Charts
st.markdown("### Placement by Course")
fig1 = px.bar(filtered.groupby(course_col)[placed_col].sum().reset_index(), x=course_col, y=placed_col, title="Placed by Course")
st.plotly_chart(fig1, use_container_width=True)

st.markdown("### Completion Rate by Region")
if region_col in filtered.columns:
    comp_by_region = filtered.groupby(region_col)[completion_col].mean().reset_index()
    fig2 = px.bar(comp_by_region, x=region_col, y=completion_col, title="Avg Completion Rate by Region")
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("### Trainees by Gender")
if gender_col in filtered.columns:
    gender_count = filtered.groupby(gender_col)[trainees_col].sum().reset_index()
    fig3 = px.pie(gender_count, names=gender_col, values=trainees_col, title="Trainees by Gender")
    st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")

# AI Summary section
st.markdown("### 🤖 AI Insights & Recommendations")

# openai_key = st.secrets.get("OPENAI_API_KEY") if "OPENAI_API_KEY" in st.secrets else st.sidebar.text_input("OpenAI API Key (optional)", type="password")
# use_openai = False
# if openai_key and openai is not None:
#     openai.api_key = openai_key
#     use_openai = True

# Prepare facts to feed to AI or to prepare rule-based summary
facts = {
    "total_trainees": int(total_tr),
    "total_placed": int(total_placed),
    "avg_completion": float(avg_completion),
    "placement_rate": float(placement_rate),
    "top_region_by_completion": comp_by_region.sort_values(by=completion_col, ascending=False)[region_col].iloc[0] if not comp_by_region.empty else "",
    "bottom_region_by_completion": comp_by_region.sort_values(by=completion_col, ascending=True)[region_col].iloc[0] if not comp_by_region.empty else "",
}


# Display key facts (for developer reference)
st.subheader("📘 Dashboard Facts (Reference Data)")
# st.json(facts)

# ------------------------------
# Generate Rule-Based Summary
# ------------------------------
def generate_ai_summary(facts):
    summary = f"""
    ### 📊 **Performance Summary**
    - Total Trainees: {facts['total_trainees']:,}
    - Total Placed: {facts['total_placed']:,}
    - Average Course Completion: {facts['avg_completion']:.2f}%
    - Overall Placement Rate: {facts['placement_rate']:.2f}%
    - Top Region by Completion: **{facts['top_region_by_completion']}**
    - Region Needing Support: **{facts['bottom_region_by_completion']}**

    ### 💡 **AI-Driven Insights**
    - Regions with higher completion rates show stronger placement outcomes, indicating effective training and learner engagement.
    - There’s a noticeable opportunity to boost performance in `{facts['bottom_region_by_completion']}` by analyzing methods used in `{facts['top_region_by_completion']}`.
    - Trainee engagement and course completion strongly correlate with employability outcomes.

    ### ✅ **Suggested Actions**
    - Conduct peer-learning workshops for trainers in `{facts['bottom_region_by_completion']}`.
    - Replicate best practices from `{facts['top_region_by_completion']}` across other regions.
    - Enhance post-training support to increase placement conversion rates by 5–10%.
    """

    return summary



summary_text = ""
# if use_openai:
#     # Build a safe prompt and call OpenAI (if key supplied)
#     prompt = f\"\"\"You are an executive analyst for a training NGO. Given the following facts about a training program, write a concise executive summary of 4-5 sentences and 2 short actionable suggestions (each 1 sentence).
# Facts: {json.dumps(facts)}
# Instructions: Use plain language, be concise, avoid inventing facts, and provide two practical suggestions.\"\"\"
#     try:
#         response = openai.ChatCompletion.create(
#             model="gpt-4o-mini" if "gpt-4o-mini" in openai.api_key else "gpt-4o",
#             messages=[{"role":"system","content":"You are a helpful analyst."},{"role":"user","content":prompt}],
#             max_tokens=250,
#             temperature=0.2
#         )
#         # extract reply
#         summary_text = response['choices'][0]['message']['content'].strip()
#     except Exception as e:
#         st.error(f"OpenAI call failed: {e}")
#         summary_text = generate_ai_summary(facts)
# else:
#     summary_text = generate_ai_summary(facts)

summary_text = generate_ai_summary(facts)
st.markdown("### Executive Summary")
st.write(summary_text)

