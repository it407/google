import streamlit as st
import psycopg2
import pandas as pd

st.title("📊 test_td table demo")

try:
    conn = psycopg2.connect(
        host=st.secrets["DB_HOST"],
        port=st.secrets["DB_PORT"],
        dbname=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"]
    )

    cur = conn.cursor()

    # INSERT (optional)
    if st.button("Insert value = 1"):
        cur.execute("INSERT INTO test_td (id) VALUES (%s)", (1,))
        conn.commit()
        st.success("✅ Inserted value 1")

    # FETCH
    df = pd.read_sql("SELECT * FROM test_td", conn)
    st.subheader("📥 Data from test_td")
    st.dataframe(df)

    cur.close()
    conn.close()

except Exception as e:
    st.error("❌ Error")
    st.code(str(e))
