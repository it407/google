import streamlit as st
import pandas as pd

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Attendance Dashboard",
    layout="wide"
)

# ---------------- CONSTANTS ----------------
SHEET_ID = "1FVjiK9Y-AhrogECD6Q8tRZpPiSxOFMevlMKGQWTGsHI"
SHEET_NAME = "odata"

# Public CSV URL
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

# ---------------- LOAD DATA ----------------
@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(CSV_URL)

    # Type conversions
    if "log_date" in df.columns:
        df["log_date"] = pd.to_datetime(df["log_date"], errors="coerce")

    if "work_hours" in df.columns:
        df["work_hours"] = pd.to_numeric(df["work_hours"], errors="coerce")

    return df

df = load_data()

st.title("📊 Attendance Dashboard")

if df.empty:
    st.warning("No data found in Google Sheet.")
    st.stop()

# ---------------- FILTERS ----------------
col1, col2 = st.columns(2)

with col1:
    search = st.text_input("🔍 Search (Emp ID / Name)")

with col2:
    min_date = df["log_date"].min()
    max_date = df["log_date"].max()

    start_date, end_date = st.date_input(
        "📅 Date Range",
        value=[min_date, max_date]
    )

# Apply search filter
if search:
    df = df[
        df["employee_fname"].str.contains(search, case=False, na=False)
        | df["empid"].astype(str).str.contains(search)
    ]

# Apply date filter
df = df[
    (df["log_date"] >= pd.to_datetime(start_date))
    & (df["log_date"] <= pd.to_datetime(end_date))
]

# ---------------- ROW COLOR HIGHLIGHTING ----------------
def highlight_row(row):
    if row.get("leave_status") == "YES":
        return ["background-color: #ffd6d6"] * len(row)
    if row.get("day_status") == "Full Day":
        return ["background-color: #d4f7d4"] * len(row)
    if row.get("day_status") == "Half Day":
        return ["background-color: #fff3cd"] * len(row)
    if row.get("day_status") == "Miss Punch":
        return ["background-color: #f8d7da"] * len(row)
    return [""] * len(row)

styled_df = df.style.apply(highlight_row, axis=1)

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
