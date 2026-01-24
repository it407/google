import streamlit as st
import psycopg2
import pandas as pd

st.set_page_config(page_title="PostgreSQL Connection Test", layout="centered")

st.title("🧪 PostgreSQL Connection Test")

DB_HOST = "103.84.129.38"
DB_PORT = 5433
DB_NAME = "test_db"
DB_USER = "postgres"
DB_PASSWORD = "Zoff@4321"

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=5
    )

    st.success("✅ Connected to PostgreSQL")

    df = pd.read_sql("SELECT current_database(), now()", conn)
    st.dataframe(df)

    conn.close()

except Exception as e:
    st.error("❌ Connection failed")
    st.code(str(e))
