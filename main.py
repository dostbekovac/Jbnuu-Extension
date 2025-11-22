import streamlit as st
import requests
import sqlite3
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("HEMIS_TOKEN")

BASE_URL = "https://student.jbnuu.uz/rest/v1/education/schedule"
HEADERS = {"accept": "application/json", "Authorization": f"Bearer {TOKEN}"}

DB_NAME = "schedule.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY,
            subject_name TEXT,
            subject_code TEXT,
            faculty_name TEXT,
            department_name TEXT,
            education_year TEXT,
            semester_name TEXT,
            group_name TEXT,
            auditorium_name TEXT,
            building_name TEXT,
            training_type TEXT,
            lesson_pair TEXT,
            start_time TEXT,
            end_time TEXT,
            teacher_name TEXT,
            lesson_date INTEGER,
            week INTEGER,
            week_start INTEGER,
            week_end INTEGER,
            fetched_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def prepare_data(item):
    return (
        item["id"],
        item["subject"]["name"],
        item["subject"]["code"],
        item["faculty"]["name"],
        item["department"]["name"],
        item["educationYear"]["name"],
        item["semester"]["name"],
        item["group"]["name"],
        item["auditorium"]["name"],
        item["auditorium"]["building"]["name"],
        item["trainingType"]["name"],
        item["lessonPair"]["name"],
        item["lessonPair"]["start_time"],
        item["lessonPair"]["end_time"],
        item["employee"]["name"],
        item["lesson_date"],
        item["_week"],
        item["weekStartTime"],
        item["weekEndTime"]
    )

def save_to_db(item):
    data = prepare_data(item)
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        INSERT INTO schedule (
            id, subject_name, subject_code, faculty_name, department_name,
            education_year, semester_name, group_name, auditorium_name,
            building_name, training_type, lesson_pair, start_time, end_time,
            teacher_name, lesson_date, week, week_start, week_end
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            subject_name=excluded.subject_name,
            teacher_name=excluded.teacher_name,
            lesson_date=excluded.lesson_date,
            fetched_at=CURRENT_TIMESTAMP
    """, data)

    conn.commit()
    conn.close()

def fetch_schedule(week, semester):
    resp = requests.get(
        BASE_URL,
        headers=HEADERS,
        params={"week": week, "semester": semester}
    )

    st.write("API javobi:", resp.json())  # DEBUG

    if resp.status_code == 200:
        return resp.json()["data"]
    return []

st.set_page_config(page_title="📚 Talaba dars jadvali", layout="wide")
st.title("📚 Talaba dars jadvali (HEMIS)")

init_db()

tab1, tab2, tab3 = st.tabs(["🔍 Jadval yuklash", "💾 Baza", "📥 Export"])

with tab1:
    week = st.number_input("Hafta raqami", value=2937)
    semester = st.number_input("Semestr", value=15)

    if st.button("Jadvalni yuklash", type="primary"):
        data = fetch_schedule(week, semester)

        for item in data:
            save_to_db(item)

        st.success(f"{len(data)} ta dars yuklandi!")

with tab2:
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM schedule", conn)
    conn.close()

    st.dataframe(df, use_container_width=True)

with tab3:
    if len(df) > 0:
        from io import BytesIO
        output = BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)

        st.download_button(
            "📥 Excelga yuklab olish",
            output.getvalue(),
            "schedule.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Bazadan maʼlumot topilmadi.")
