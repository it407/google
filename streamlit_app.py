import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

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
    df["log_date"] = pd.to_datetime(df["log_date"], errors="coerce")
    return df

df = load_data()

st.title("📊 Attendance Dashboard")

# ---------------- AGGRID CONFIG ----------------
gb = GridOptionsBuilder.from_dataframe(df)

gb.configure_default_column(
    filter=True,
    sortable=True,
    resizable=True,
    floatingFilter=True
)

# Multi-select dropdown filters
set_filter_cols = ["day_status", "leave_status", "employee_fname", "empid"]

for col in set_filter_cols:
    if col in df.columns:
        gb.configure_column(
            col,
            filter="agSetColumnFilter",
            filterParams={
                "applyMiniFilterWhileTyping": True,
                "buttons": ["reset", "apply"]
            }
        )

# Date filter
if "log_date" in df.columns:
    gb.configure_column(
        "log_date",
        filter="agDateColumnFilter",
        filterParams={"browserDatePicker": True}
    )

# Cell-level color highlights (SAFE)
gb.configure_column(
    "day_status",
    cellStyle={
        "styleConditions": [
            {"condition": "value == 'Full Day'", "style": {"backgroundColor": "#d4f7d4"}},
            {"condition": "value == 'Half Day'", "style": {"backgroundColor": "#fff3cd"}},
            {"condition": "value == 'Miss Punch'", "style": {"backgroundColor": "#f8d7da"}},
        ]
    }
)

gb.configure_column(
    "leave_status",
    cellStyle={
        "styleConditions": [
            {"condition": "value == 'YES'", "style": {"backgroundColor": "#ffd6d6"}}
        ]
    }
)

gb.configure_pagination(paginationAutoPageSize=True)

# ---------------- RENDER GRID ----------------
grid_response = AgGrid(
    df,
    gridOptions=gb.build(),
    height=600,
    theme="balham",
    fit_columns_on_grid_load=True
)

# ---------------- CSV DOWNLOAD (FILTERED DATA) ----------------
filtered_df = pd.DataFrame(grid_response["data"])

st.download_button(
    label="⬇ Download Filtered CSV",
    data=filtered_df.to_csv(index=False).encode("utf-8"),
    file_name="attendance_filtered.csv",
    mime="text/csv"
)
