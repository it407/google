import streamlit as st
import pandas as pd

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Attendance Dashboard",
    layout="wide"
)

# ---------------- GOOGLE SHEET (PUBLIC) ----------------
SHEET_ID = "1FVjiK9Y-AhrogECD6Q8tRZpPiSxOFMevlMKGQWTGsHI"
SHEET_NAME = "odata"

CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

# ---------------- LOAD DATA ----------------
@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv(CSV_URL)
    df["log_date"] = pd.to_datetime(df["log_date"], errors="coerce")
    df["work_hours"] = pd.to_numeric(df["work_hours"], errors="coerce")
    return df

df = load_data()

st.title("📊 Attendance Dashboard")

# ---------------- FILTERS (MOBILE FRIENDLY) ----------------
with st.expander("🔍 Filters", expanded=True):

    search = st.text_input("Search (Employee Name / Emp ID)")

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "Start Date",
            df["log_date"].min()
        )

    with col2:
        end_date = st.date_input(
            "End Date",
            df["log_date"].max()
        )

    status_filter = st.multiselect(
        "Day Status",
        options=sorted(df["day_status"].dropna().unique()),
        default=sorted(df["day_status"].dropna().unique())
    )

# ---------------- APPLY FILTERS ----------------
if search:
    df = df[
        df["employee_fname"].str.contains(search, case=False, na=False)
        | df["empid"].astype(str).str.contains(search)
    ]

df = df[
    (df["log_date"] >= pd.to_datetime(start_date))
    & (df["log_date"] <= pd.to_datetime(end_date))
    & (df["day_status"].isin(status_filter))
]

# ---------------- WORK HOURS STATUS (FAST COLOR TRICK) ----------------
def hours_status(hours):
    if pd.isna(hours):
        return "⚪ NA"
    if hours >= 8:
        return "🟢 Full"
    if hours >= 4:
        return "🟡 Partial"
    return "🔴 Low"

df["Work Hours Status"] = df["work_hours"].apply(hours_status)

# ---------------- CLEAN COLUMN ORDER ----------------
display_cols = [
    "empid",
    "employee_fname",
    "log_date",
    "day_status",
    "work_hours",
    "Work Hours Status",
    "leave_status"
]

display_cols = [c for c in display_cols if c in df.columns]

# ---------------- TABLE ----------------
st.subheader("📋 Attendance Records")

st.dataframe(
    df[display_cols],
    use_container_width=True,
    height=520
)

# ---------------- CSV DOWNLOAD ----------------
st.download_button(
    "⬇ Download Filtered CSV",
    df[display_cols].to_csv(index=False),
    "attendance_filtered.csv",
    "text/csv"
)
