import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Attendance Dashboard", layout="wide")

# ---------------- CONSTANTS ----------------
SHEET_ID = "YOUR_GOOGLE_SHEET_ID"
SHEET_NAME = "Sheet1"

# ---------------- LOAD DATA ----------------
@st.cache_data(ttl=300)
def load_data():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )

    gc = gspread.authorize(creds)
    ws = gc.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

    data = ws.get_all_records()
    df = pd.DataFrame(data)

    df["log_date"] = pd.to_datetime(df["log_date"])
    df["work_hours"] = pd.to_numeric(df["work_hours"], errors="coerce")

    return df

df = load_data()

st.title("📊 Attendance Dashboard")

# ---------------- FILTERS ----------------
col1, col2 = st.columns(2)

with col1:
    search = st.text_input("🔍 Search (Emp ID / Name)")

with col2:
    start_date, end_date = st.date_input(
        "📅 Date Range",
        [df["log_date"].min(), df["log_date"].max()]
    )

# Apply filters
if search:
    df = df[
        df["employee_name"].str.contains(search, case=False, na=False)
        | df["empid"].astype(str).str.contains(search)
    ]

df = df[
    (df["log_date"] >= pd.to_datetime(start_date))
    & (df["log_date"] <= pd.to_datetime(end_date))
]

# ---------------- HIGHLIGHTING ----------------
def highlight_rows(row):
    if row["leave_status"] == "YES":
        return ["background-color: #ffd6d6"] * len(row)
    if row["day_status"] == "Full Day":
        return ["background-color: #d4f7d4"] * len(row)
    if row["day_status"] == "Half Day":
        return ["background-color: #fff3cd"] * len(row)
    if row["day_status"] == "Miss Punch":
        return ["background-color: #f8d7da"] * len(row)
    return [""] * len(row)

styled_df = df.style.apply(highlight_rows, axis=1)

# ---------------- TABLE ----------------
st.subheader("📋 Attendance Table")
st.dataframe(styled_df, use_container_width=True)

# ---------------- DOWNLOAD ----------------
csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇ Download CSV",
    csv,
    "attendance_report.csv",
    "text/csv"
)
