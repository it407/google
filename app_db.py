import streamlit as st
import psycopg2
import pandas as pd

st.title("🧪 PostgreSQL Connection Test")

try:
    conn = psycopg2.connect(
        host=st.secrets["DB_HOST"],
        port=st.secrets["DB_PORT"],
        dbname=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        connect_timeout=5
    )

    st.success("✅ Connected to PostgreSQL")

    df = pd.read_sql("SELECT current_database(), now()", conn)
    st.dataframe(df)

    conn.close()

except Exception as e:
    st.error("❌ Connection failed")
    st.code(str(e))
