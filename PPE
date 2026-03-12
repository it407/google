import streamlit as st
import pandas as pd

st.set_page_config(page_title="AI CCTV Monitoring", layout="wide")

st.title("AI CCTV Monitoring Dashboard")

GOOGLE_SHEET_CSV_URL = "PASTE_YOUR_GOOGLE_SHEET_CSV_URL_HERE"


@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(GOOGLE_SHEET_CSV_URL)

    if "Timestamp" in df.columns:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")

    df = df.fillna("")
    return df


try:
    df = load_data()

    st.sidebar.header("Filters")

    section_options = sorted([x for x in df["Section"].dropna().unique() if x != ""])
    event_options = sorted([x for x in df["Event_Type"].dropna().unique() if x != ""])
    severity_options = sorted([x for x in df["Severity"].dropna().unique() if x != ""])
    status_options = sorted([x for x in df["Violation_Status"].dropna().unique() if x != ""])

    selected_sections = st.sidebar.multiselect("Section", section_options, default=section_options)
    selected_events = st.sidebar.multiselect("Event Type", event_options, default=event_options)
    selected_severity = st.sidebar.multiselect("Severity", severity_options, default=severity_options)
    selected_status = st.sidebar.multiselect("Violation Status", status_options, default=status_options)

    search_text = st.sidebar.text_input("Search description / camera")

    filtered_df = df.copy()

    if selected_sections:
        filtered_df = filtered_df[filtered_df["Section"].isin(selected_sections)]

    if selected_events:
        filtered_df = filtered_df[filtered_df["Event_Type"].isin(selected_events)]

    if selected_severity:
        filtered_df = filtered_df[filtered_df["Severity"].isin(selected_severity)]

    if selected_status:
        filtered_df = filtered_df[filtered_df["Violation_Status"].isin(selected_status)]

    if search_text:
        filtered_df = filtered_df[
            filtered_df["Description"].astype(str).str.contains(search_text, case=False, na=False)
            | filtered_df["Camera_ID"].astype(str).str.contains(search_text, case=False, na=False)
            | filtered_df["Specific_Violations"].astype(str).str.contains(search_text, case=False, na=False)
        ]

    filtered_df = filtered_df.reset_index(drop=True)
    filtered_df.index = filtered_df.index + 1

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Records", len(filtered_df))
    col2.metric("Total Violations", (filtered_df["Violation_Status"] == "VIOLATION").sum())
    col3.metric("Critical", (filtered_df["Severity"] == "CRITICAL").sum())
    col4.metric("High", (filtered_df["Severity"] == "HIGH").sum())

    st.subheader("Violation Log Table")

    # Show table without Image_URL
    table_columns = [
        "Timestamp",
        "Camera_ID",
        "Section",
        "Event_Type",
        "Severity",
        "Description",
        "Specific_Violations",
        "Violation_Status"
    ]

    available_columns = [col for col in table_columns if col in filtered_df.columns]

    st.dataframe(
        filtered_df[available_columns],
        use_container_width=True,
        hide_index=False,
        column_config={
            "Timestamp": st.column_config.DatetimeColumn("Timestamp", format="YYYY-MM-DD HH:mm:ss"),
            "Camera_ID": st.column_config.TextColumn("Camera ID"),
            "Section": st.column_config.TextColumn("Section"),
            "Event_Type": st.column_config.TextColumn("Event Type"),
            "Severity": st.column_config.TextColumn("Severity"),
            "Description": st.column_config.TextColumn("Description", width="large"),
            "Specific_Violations": st.column_config.TextColumn("Specific Violations", width="large"),
            "Violation_Status": st.column_config.TextColumn("Violation Status"),
        },
    )

    st.markdown("---")
    st.subheader("View Image")

    if len(filtered_df) > 0:
        selected_row = st.selectbox(
            "Select row number",
            filtered_df.index.tolist(),
            format_func=lambda x: f"Row {x} | {filtered_df.loc[x, 'Camera_ID']} | {filtered_df.loc[x, 'Event_Type']}"
        )

        if st.button("View Image"):
            image_url = filtered_df.loc[selected_row, "Image_URL"] if "Image_URL" in filtered_df.columns else ""

            if image_url:
                st.image(image_url, caption=f"Row {selected_row} Image", use_container_width=True)
            else:
                st.warning("No image URL found for this row.")
    else:
        st.info("No records found.")

    st.download_button(
        "Download Filtered CSV",
        filtered_df.to_csv(index=False).encode("utf-8"),
        file_name="filtered_violation_log.csv",
        mime="text/csv",
    )

except Exception as e:
    st.error(f"Error loading Google Sheet data: {e}")
    st.info("Check your Google Sheet CSV URL and sharing settings.")
