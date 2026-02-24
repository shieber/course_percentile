"""
Course Grade Percentile Ranker — navigation entry point.
"""
import streamlit as st

st.set_page_config(
    page_title="Course Grade Percentile Ranker",
    layout="centered",
)

pg = st.navigation([
    st.Page("pages/Ranker.py",       title="App"),
    st.Page("pages/1_Background.py", title="Background"),
])
pg.run()
