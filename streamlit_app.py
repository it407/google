import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Attendance Dashboard", layout="wide")

# ---------------- CONSTANTS ----------------
SHEET_ID = "1FVjiK9Y-AhrogECD6Q8tRZpPiSxOFMevlMKGQWTGsHI"
SHEET_NAME = "odata"

CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

# ---------------- LOAD DATA ----------------
@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv(CSV_URL)
    df["log_date"] = pd.to_datetime(df["log_date"], errors="coerce")
    return df

df = load_data()

st.title("📊 Attendance Dashboard")

# ---------------- AGGRID CONFIG ----------------
gb = GridOptionsBuilder.from_dataframe(df)

# Default column behavior
gb.configure_default_column(
    filter=True,
    sortable=True,
    resizable=True,
    floatingFilter=True   # 👈 Excel-like filter bar
)

# Enable SET FILTER (multi-select dropdown) for specific columns
set_filter_cols = ["day_status", "leave_status", "employee_fname", "empid"]

for col in set_filter_cols:
    if col in df.columns:
        gb.configure_column(
            col,
            filter="agSetColumnFilter",
            filterParams={
                "applyMiniFilterWhileTyping": True,
                "debounceMs": 200,
                "buttons": ["reset", "apply"]
            }
        )

# Date filter
if "log_date" in df.columns:
    gb.configure_column(
        "log_date",
        filter="agDateColumnFilter",
        filterParams={
            "browserDatePicker": True
        }
    )

# Pagination
gb.configure_pagination(paginationAutoPageSize=True)

# Row highlighting
gb.configure_grid_options(
    getRowStyle="""
    function(params) {
        if (params.data.leave_status === 'YES') {
            return { backgroundColor: '#ffd6d6' };
        }
        if (params.data.day_status === 'Full Day') {
            return { backgroundColor: '#d4f7d4' };
        }
        if (params.data.day_status === 'Half Day') {
            return { backgroundColor: '#fff3cd' };
        }
        if (params.data.day_status === 'Miss Punch') {
            return { backgroundColor: '#f8d7da' };
        }
    }
    """
)

# ---------------- TABLE ----------------
AgGrid(
    df,
    gridOptions=gb.build(),
    update_mode=GridUpdateMode.NO_UPDATE,
    height=600,
    allow_unsafe_jscode=True,
    theme="balham"
)
