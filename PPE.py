import streamlit as st
import pandas as pd
import html

st.set_page_config(page_title="AI CCTV Monitoring Dashboard", layout="wide")

GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/18cfgyHMGpoNGLzqGalg7DIu0VFKtIihUh-Nzn2HQDKQ/gviz/tq?tqx=out:csv&sheet=odata"


@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(GOOGLE_SHEET_CSV_URL)

    if "Timestamp" in df.columns:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")

    df = df.fillna("")
    return df


def build_html_table(dataframe):
    if dataframe.empty:
        return "<p>No records found.</p>"

    headers = [
        "Timestamp",
        "Camera_ID",
        "Section",
        "Event_Type",
        "Severity",
        "Description",
        "Specific_Violations",
        "Violation_Status",
        "Image_URL"
    ]

    available_headers = [col for col in headers if col in dataframe.columns]

    table_html = """
    <style>
        .table-wrap {
            overflow-x: auto;
            border: 1px solid #e6e6e6;
            border-radius: 10px;
            background: white;
        }
        table.custom-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }
        table.custom-table thead th {
            position: sticky;
            top: 0;
            background: #f7f7f7;
            z-index: 1;
            border-bottom: 1px solid #ddd;
            padding: 10px;
            text-align: left;
            white-space: nowrap;
        }
        table.custom-table tbody td {
            border-bottom: 1px solid #eee;
            padding: 10px;
            vertical-align: top;
        }
        table.custom-table tbody tr:hover {
            background: #fafafa;
        }
        .severity-critical {
            color: #b00020;
            font-weight: 700;
        }
        .severity-high {
            color: #d35400;
            font-weight: 700;
        }
        .severity-medium {
            color: #9c6b00;
            font-weight: 700;
        }
        .severity-low {
            color: #1f618d;
            font-weight: 700;
        }
        .severity-none {
            color: #2e7d32;
            font-weight: 700;
        }
        .status-violation {
            color: #b00020;
            font-weight: 700;
        }
        .status-no-violation {
            color: #2e7d32;
            font-weight: 700;
        }
        .open-link {
            color: #1565c0;
            text-decoration: none;
            font-weight: 600;
        }
        .open-link:hover {
            text-decoration: underline;
        }
        .small-col {
            white-space: nowrap;
        }
        .desc-col {
            min-width: 260px;
        }
        .viol-col {
            min-width: 220px;
        }
    </style>
    <div class="table-wrap">
    <table class="custom-table">
        <thead>
            <tr>
    """

    for col in available_headers:
        label = "Image" if col == "Image_URL" else col.replace("_", " ")
        table_html += f"<th>{html.escape(label)}</th>"

    table_html += "</tr></thead><tbody>"

    for _, row in dataframe.iterrows():
        table_html += "<tr>"

        for col in available_headers:
            val = row[col]

            if col == "Timestamp":
                if pd.notna(val) and str(val) != "":
                    try:
                        val = pd.to_datetime(val).strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        val = str(val)
                else:
                    val = ""

                table_html += f'<td class="small-col">{html.escape(str(val))}</td>'

            elif col == "Severity":
                sev = str(val).upper().strip()
                sev_class = {
                    "CRITICAL": "severity-critical",
                    "HIGH": "severity-high",
                    "MEDIUM": "severity-medium",
                    "LOW": "severity-low",
                    "NONE": "severity-none"
                }.get(sev, "")
                table_html += f'<td class="small-col {sev_class}">{html.escape(sev)}</td>'

            elif col == "Violation_Status":
                status = str(val).upper().strip()
                status_class = {
                    "VIOLATION": "status-violation",
                    "NO_VIOLATION": "status-no-violation"
                }.get(status, "")
                table_html += f'<td class="small-col {status_class}">{html.escape(status)}</td>'

            elif col == "Description":
                table_html += f'<td class="desc-col">{html.escape(str(val))}</td>'

            elif col == "Specific_Violations":
                table_html += f'<td class="viol-col">{html.escape(str(val))}</td>'

            elif col == "Image_URL":
                url = str(val).strip()
                if url:
                    table_html += (
                        f'<td class="small-col">'
                        f'<a class="open-link" href="{html.escape(url)}" target="_blank">Open Image</a>'
                        f'</td>'
                    )
                else:
                    table_html += '<td class="small-col">-</td>'

            else:
                table_html += f'<td class="small-col">{html.escape(str(val))}</td>'

        table_html += "</tr>"

    table_html += """
        </tbody>
    </table>
    </div>
    """

    return table_html


st.title("AI CCTV Monitoring Dashboard")

try:
    df = load_data()

    st.sidebar.header("Filters")

    if "Section" in df.columns:
        section_options = sorted([x for x in df["Section"].astype(str).unique() if x != ""])
        selected_sections = st.sidebar.multiselect("Section", section_options, default=section_options)
    else:
        selected_sections = []

    if "Event_Type" in df.columns:
        event_options = sorted([x for x in df["Event_Type"].astype(str).unique() if x != ""])
        selected_events = st.sidebar.multiselect("Event Type", event_options, default=event_options)
    else:
        selected_events = []

    if "Severity" in df.columns:
        severity_options = sorted([x for x in df["Severity"].astype(str).unique() if x != ""])
        selected_severity = st.sidebar.multiselect("Severity", severity_options, default=severity_options)
    else:
        selected_severity = []

    if "Violation_Status" in df.columns:
        status_options = sorted([x for x in df["Violation_Status"].astype(str).unique() if x != ""])
        selected_status = st.sidebar.multiselect("Violation Status", status_options, default=status_options)
    else:
        selected_status = []

    search_text = st.sidebar.text_input("Search")

    filtered_df = df.copy()

    if selected_sections and "Section" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["Section"].isin(selected_sections)]

    if selected_events and "Event_Type" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["Event_Type"].isin(selected_events)]

    if selected_severity and "Severity" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["Severity"].isin(selected_severity)]

    if selected_status and "Violation_Status" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["Violation_Status"].isin(selected_status)]

    if search_text:
        mask = pd.Series(False, index=filtered_df.index)

        for col in ["Camera_ID", "Description", "Specific_Violations", "Section", "Event_Type"]:
            if col in filtered_df.columns:
                mask = mask | filtered_df[col].astype(str).str.contains(search_text, case=False, na=False)

        filtered_df = filtered_df[mask]

    filtered_df = filtered_df.sort_values(by="Timestamp", ascending=False, na_position="last")

    c1, c2, c3, c4 = st.columns(4)

    total_records = len(filtered_df)

    total_violations = 0
    if "Violation_Status" in filtered_df.columns:
        total_violations = (filtered_df["Violation_Status"].astype(str).str.upper() == "VIOLATION").sum()

    critical_count = 0
    if "Severity" in filtered_df.columns:
        critical_count = (filtered_df["Severity"].astype(str).str.upper() == "CRITICAL").sum()

    high_count = 0
    if "Severity" in filtered_df.columns:
        high_count = (filtered_df["Severity"].astype(str).str.upper() == "HIGH").sum()

    c1.metric("Total Records", total_records)
    c2.metric("Violations", total_violations)
    c3.metric("Critical", critical_count)
    c4.metric("High", high_count)

    st.markdown("### Violation Log")
    st.markdown(build_html_table(filtered_df), unsafe_allow_html=True)

    st.download_button(
        "Download Filtered CSV",
        filtered_df.to_csv(index=False).encode("utf-8"),
        file_name="filtered_violation_log.csv",
        mime="text/csv"
    )

except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("Check the Google Sheet sharing setting and sheet name.")
