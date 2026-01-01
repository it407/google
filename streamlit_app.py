import streamlit as st
import pandas as pd
import json
from google.oauth2.service_account import Credentials
import gspread
from st_aggrid import AgGrid, GridOptionsBuilder
import plotly.express as px

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Attendance Report",
    layout="wide"
)

# ---------------- CONSTANTS ----------------
SHEET_ID = "1FVjiK9Y-AhrogECD6Q8tRZpPiSxOFMevlMKGQWTGsHI"
SHEET_NAME = "odata"

# ---------------- LOAD DATA ----------------
@st.cache_data(ttl=300)
def load_data():
    # 🔐 Credentials from Streamlit Secrets (RAW JSON)
    creds = Credentials.from_service_account_info(
        json.loads(st.secrets["GOOGLE_CREDS"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )

    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    if df.empty:
        return df

    df["log_date"] = pd.to_datetime(df["log_date"], errors="coerce")
    df["work_hours"] = pd.to_numeric(df["work_hours"], errors="coerce")

    return df

# ---------------- LOAD DATAFRAME ----------------
df = load_data()

st.title("📊 Attendance Report")

if df.empty:
    st.warning("No data available in Google Sheet.")
    st.stop()

# ---------------- SIDEBAR FILTERS ----------------
st.sidebar.header("Filters")

search = st.sidebar.text_input("Search (Emp ID / Name)")

min_date = df["log_date"].min().date()
max_date = df["log_date"].max().date()

sd, ed = st.sidebar.date_input(
    "Date Range",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

if search:
    df = df[
        df["employee_fname"].str.contains(search, case=False, na=False)
        | df["empid"].astype(str).str.contains(search)
    ]

df = df[
    (df["log_date"] >= pd.to_datetime(sd))
    & (df["log_date"] <= pd.to_datetime(ed))
]

# ---------------- KPIs ----------------
k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Total Records", len(df))
k2.metric("Full Day", len(df[df.day_status == "Full Day"]))
k3.metric("Half Day", len(df[df.day_status == "Half Day"]))
k4.metric("Miss Punch", len(df[df.day_status == "Miss Punch"]))
k5.metric("Leave YES", len(df[df.leave_status == "YES"]))

# ---------------- CHART ----------------
st.subheader("📈 Attendance Trend")

fig = px.histogram(
    df,
    x="log_date",
    color="day_status",
    title="Daily Attendance Status"
)
st.plotly_chart(fig, use_container_width=True)

# ---------------- TABLE ----------------
st.subheader("📋 Attendance Table")

gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_default_column(
    filterable=True,
    sortable=True,
    resizable=True
)
gb.configure_pagination(paginationAutoPageSize=True)

# Full row highlight if Leave = YES
gb.configure_grid_options(
    getRowStyle="""
    function(params) {
        if (params.data.leave_status === "YES") {
            return { backgroundColor: "#ffe0e0" };
        }
    }
    """
)

# Status-based colors
gb.configure_column(
    "day_status",
    cellStyle={
        "styleConditions": [
            {"condition": "value === 'Full Day'", "style": {"backgroundColor": "#c6f6c6"}},
            {"condition": "value === 'Half Day'", "style": {"backgroundColor": "#fff3b0"}},
            {"condition": "value === 'Punch In'", "style": {"backgroundColor": "#b3d9ff"}},
            {"condition": "value === 'Miss Punch'", "style": {"backgroundColor": "#ffb3b3"}},
        ]
    }
)

AgGrid(
    df,
    gridOptions=gb.build(),
    height=450,
    allow_unsafe_jscode=True
)

# ---------------- EXPORT ----------------
st.subheader("⬇ Export Data")

csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download CSV",
    data=csv,
    file_name="attendance_report.csv",
    mime="text/csv"
)
