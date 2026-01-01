import streamlit as st
import pandas as pd

st.set_page_config(page_title="Attendance Dashboard", layout="wide")

SHEET_ID = "1FVjiK9Y-AhrogECD6Q8tRZpPiSxOFMevlMKGQWTGsHI"
SHEET_NAME = "odata"

CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv(CSV_URL)
    df["log_date"] = pd.to_datetime(df["log_date"], errors="coerce")
    return df

df = load_data()

st.title("📊 Attendance Dashboard")

# ---------------- FILTERS ----------------
c1, c2 = st.columns(2)

with c1:
    search = st.text_input("🔍 Search (Emp ID / Name)")

with c2:
    start, end = st.date_input(
        "📅 Date Range",
        [df["log_date"].min(), df["log_date"].max()]
    )

if search:
    df = df[
        df["employee_fname"].str.contains(search, case=False, na=False)
        | df["empid"].astype(str).str.contains(search)
    ]

df = df[
    (df["log_date"] >= pd.to_datetime(start))
    & (df["log_date"] <= pd.to_datetime(end))
]

# ---------------- STATUS INDICATOR ----------------
def status_icon(row):
    if row["leave_status"] == "YES":
        return "🔴 Leave"
    if row["day_status"] == "Full Day":
        return "🟢 Full"
    if row["day_status"] == "Half Day":
        return "🟡 Half"
    if row["day_status"] == "Miss Punch":
        return "🔴 Miss"
    return ""

df.insert(0, "Status", df.apply(status_icon, axis=1))

# ---------------- TABLE ----------------
st.subheader("📋 Attendance Table (Fast)")
st.dataframe(df, use_container_width=True, height=520)

# ---------------- DOWNLOAD ----------------
st.download_button(
    "⬇ Download CSV",
    df.to_csv(index=False),
    "attendance_report.csv",
    "text/csv"
)
