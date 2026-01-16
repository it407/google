import streamlit as st
import pandas as pd

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Attendance Dashboard", layout="wide")

# ================= UI CLEAN =================
st.markdown("""
<style>
.block-container { padding-top: 1rem; }
header [data-testid="stToolbar"] { display: none; }
a[href*="share.streamlit"],
[data-testid="stShareButton"] { display: none !important; }
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ================= SESSION INIT =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.employee_id = None
    st.session_state.role = None

# ================= GOOGLE SHEET CONFIG =================
SHEET_ID = "1FVjiK9Y-AhrogECD6Q8tRZpPiSxOFMevlMKGQWTGsHI"
ATT_SHEET = "odata"
ACCESS_SHEET = "user_access_master"

ATT_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={ATT_SHEET}"
ACCESS_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={ACCESS_SHEET}"

# ================= LOAD USERS (BULLETPROOF) =================
@st.cache_data(ttl=600)
def load_users():
    df = pd.read_csv(ACCESS_CSV_URL)

    # Case 1: Entire header collapsed into one column
    if len(df.columns) == 1:
        df = df.iloc[:, 0].astype(str).str.split(r"\s+", expand=True)
        df.columns = ["user_id", "employee_id", "username", "password", "role", "is_active"]

    # Normalize headers
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "")
    )

    # Standardize column names
    rename_map = {
        "userid": "user_id",
        "employeeid": "employee_id",
        "username": "username",
        "password": "password",
        "role": "role",
        "isactive": "is_active",
        "active": "is_active"
    }
    df = df.rename(columns=rename_map)

    required = {"username", "password", "employee_id", "role"}
    if not required.issubset(df.columns):
        raise Exception(f"Missing columns: {required - set(df.columns)}")

    # Active flag
    if "is_active" in df.columns:
        df["is_active"] = df["is_active"].astype(str).str.upper() == "TRUE"
    else:
        df["is_active"] = True

    return df

users_df = load_users()

# ================= LOAD ATTENDANCE =================
@st.cache_data(ttl=600)
def load_attendance():
    df = pd.read_csv(ATT_CSV_URL)
    df.columns = df.columns.str.strip().str.lower()
    df["log_date"] = pd.to_datetime(df["log_date"], errors="coerce")
    df["work_hours"] = pd.to_numeric(df["work_hours"], errors="coerce")
    return df

# ================= LOGIN SCREEN =================
def login_screen():
    st.title("🔐 Attendance Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = users_df[
            (users_df["username"].astype(str) == username) &
            (users_df["password"].astype(str) == password) &
            (users_df["is_active"] == True)
        ]

        if user.empty:
            st.error("❌ Invalid credentials or inactive user")
        else:
            st.session_state.logged_in = True
            st.session_state.employee_id = user.iloc[0]["employee_id"]
            st.session_state.role = user.iloc[0]["role"]
            st.rerun()

# ================= LOGOUT =================
def logout_sidebar():
    with st.sidebar:
        st.markdown(f"👤 **Role:** {st.session_state.role}")
        st.markdown(f"🆔 **Employee ID:** {st.session_state.employee_id}")
        if st.button("🚪 Logout"):
            st.session_state.clear()
            st.rerun()

# ================= ROLE FILTER =================
def apply_role_filter(df):
    if st.session_state.role == "Admin":
        return df
    return df[df["empid"] == st.session_state.employee_id]

# ================= AUTH GATE =================
if not st.session_state.logged_in:
    login_screen()
    st.stop()

logout_sidebar()

# ================= LOAD DATA =================
df = load_attendance()
df = apply_role_filter(df)

st.title("📊 Attendance Dashboard")

if df.empty:
    st.warning("No data available.")
    st.stop()

# ================= FILTERS =================
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
            sorted(df["day_status"].dropna().unique()),
            sorted(df["day_status"].dropna().unique())
        )
    with col4:
        leave_status_filter = st.multiselect(
            "Leave Status",
            sorted(df["leave_status"].dropna().unique()),
            sorted(df["leave_status"].dropna().unique())
        )

    user_type_filter = st.multiselect(
        "User Type",
        sorted(df["user_type"].dropna().unique()),
        sorted(df["user_type"].dropna().unique())
    )

# ================= APPLY FILTERS =================
filtered = df.copy()

if search:
    filtered = filtered[
        filtered["employee_fname"].str.contains(search, case=False, na=False) |
        filtered["empid"].astype(str).str.contains(search)
    ]

start_dt = pd.to_datetime(start_date)
end_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

filtered = filtered[
    (filtered["log_date"] >= start_dt) &
    (filtered["log_date"] <= end_dt) &
    (filtered["day_status"].isin(day_status_filter)) &
    (filtered["leave_status"].isin(leave_status_filter)) &
    (filtered["user_type"].isin(user_type_filter))
]

# ================= WORK HOURS STATUS =================
def work_hour_status(hours):
    if pd.isna(hours):
        return "⚪ NA"
    if hours >= 8:
        return "🟢 Full"
    if hours >= 4:
        return "🟡 Partial"
    return "🔴 Low"

filtered["work hours status"] = filtered["work_hours"].apply(work_hour_status)

# ================= DISPLAY =================
display_df = filtered.copy()
display_df["log_date"] = display_df["log_date"].dt.strftime("%Y-%m-%d")

display_columns = [
    "empid", "employee_fname", "employee_lname", "gender",
    "log_date", "user_type", "first_in_time", "last_out_time",
    "work_hours", "work hours status",
    "day_status", "total_in_out", "leave_status"
]
display_columns = [c for c in display_columns if c in display_df.columns]

st.subheader("📋 Attendance Records")
st.dataframe(display_df[display_columns], use_container_width=True, height=520)

# ================= DOWNLOAD =================
st.download_button(
    "⬇ Download Filtered CSV",
    data=display_df[display_columns].to_csv(index=False).encode("utf-8"),
    file_name="attendance_filtered.csv",
    mime="text/csv"
)
