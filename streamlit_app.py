import streamlit as st
import pandas as pd

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Attendance Dashboard", layout="wide")

# ---------------- GOOGLE SHEET (PUBLIC) ----------------
SHEET_ID = "1FVjiK9Y-AhrogECD6Q8tRZpPiSxOFMevlMKGQWTGsHI"
SHEET_NAME = "odata"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

# ---------------- LOAD DATA ----------------
@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv(CSV_URL)

    # Keep as datetime for filtering
    df["log_date"] = pd.to_datetime(df["log_date"], errors="coerce")

    # Numeric conversion
    df["work_hours"] = pd.to_numeric(df["work_hours"], errors="coerce")

    return df

df = load_data()

st.title("📊 Attendance Dashboard")

if df.empty:
    st.warning("No data found in Google Sheet.")
    st.stop()

# ---------------- FILTERS (MOBILE FRIENDLY) ----------------
with st.expander("🔍 Filters", expanded=True):
    search = st.text_input("Search (Emp ID / First Name)")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", df["log_date"].min().date())
    with col2:
        end_date = st.date_input("End Date", df["log_date"].max().date())

    col3, col4 = st.columns(2)
    with col3:
        day_status_filter = st.multiselect(
            "Day Status",
            options=sorted(df["day_status"].dropna().unique()),
            default=sorted(df["day_status"].dropna().unique())
        )
    with col4:
        leave_status_filter = st.multiselect(
            "Leave Status",
            options=sorted(df["leave_status"].dropna().unique()),
            default=sorted(df["leave_status"].dropna().unique())
        )

    user_type_filter = st.multiselect(
        "User Type",
        options=sorted(df["user_type"].dropna().unique()),
        default=sorted(df["user_type"].dropna().unique())
    )

# ---------------- APPLY FILTERS ----------------
filtered = df.copy()

if search:
    filtered = filtered[
        filtered["employee_fname"].str.contains(search, case=False, na=False)
        | filtered["empid"].astype(str).str.contains(search)
    ]

start_dt = pd.to_datetime(start_date)
end_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)  # include full end day

filtered = filtered[
    (filtered["log_date"] >= start_dt)
    & (filtered["log_date"] <= end_dt)
    & (filtered["day_status"].isin(day_status_filter))
    & (filtered["leave_status"].isin(leave_status_filter))
    & (filtered["user_type"].isin(user_type_filter))
]

# ---------------- WORK HOURS STATUS (FAST VISUAL TRICK) ----------------
def work_hour_status(hours):
    if pd.isna(hours):
        return "⚪ NA"
    if hours >= 8:
        return "🟢 Full"
    if hours >= 4:
        return "🟡 Partial"
    return "🔴 Low"

filtered["Work Hours Status"] = filtered["work_hours"].apply(work_hour_status)

# ---------------- DISPLAY FORMAT (DATE AS YYYY-MM-DD) ----------------
display_df = filtered.copy()
display_df["log_date"] = display_df["log_date"].dt.strftime("%Y-%m-%d")

# ---------------- COLUMN ORDER ----------------
display_columns = [
    "empid",
    "employee_fname",
    "employee_lname",
    "gender",
    "log_date",
    "user_type",
    "first_in_time",
    "last_out_time",
    "work_hours",
    "Work Hours Status",
    "day_status",
    "total_in_out",
    "leave_status"
]
display_columns = [c for c in display_columns if c in display_df.columns]

# ---------------- TABLE ----------------
st.subheader("📋 Attendance Records")
st.dataframe(display_df[display_columns], use_container_width=True, height=520)

# ---------------- CSV DOWNLOAD ----------------
st.download_button(
    "⬇ Download Filtered CSV",
    data=display_df[display_columns].to_csv(index=False).encode("utf-8"),
    file_name="attendance_filtered.csv",
    mime="text/csv"
)
