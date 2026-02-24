"""
Course Grade Percentile Ranker — Streamlit web app.

Upload a CSV file with columns: id, letter_grade[, score]
Download a CSV with percentile ranks added.
"""
import csv
import io
import warnings

import streamlit as st

from rank_to_percentile import rank_to_percentile

st.set_page_config(
    page_title="Course Grade Percentile Ranker",
    layout="centered",
)

st.title("Course Grade Percentile Ranker")

st.markdown("""
Upload a CSV file (**no header**) with columns: `id, letter_grade[, score]`

- Valid grades: `A  A-  B+  B  B-  C+  C  C-  D+  D  D-  E  FL  PA`
- `score` is optional; higher is better; omit for all rows or provide for all
- `PA` students are excluded from ranking and receive `NA` as their percentile
- `FL` students rank equally with `E`, sorted by score within that group
- Lines starting with `#` are treated as comments and ignored
""")

st.warning(
    "**Privacy notice:** uploaded files are processed on Streamlit's servers. "
    "Do not upload files containing real student IDs or other identifying "
    "information. To process sensitive data locally, download the code and "
    "use the command-line tool instead — see the "
    "[course\\_percentile repository](https://github.com/shieber/course_percentile) "
    "for instructions."
)

uploaded = st.file_uploader("Choose a CSV file", type=["csv", "txt"])

if uploaded is not None:
    text = uploaded.read().decode("utf-8")
    records = [row for row in csv.reader(io.StringIO(text))
               if row and not row[0].strip().startswith('#')]

    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            results = rank_to_percentile(records)

        for w in caught:
            st.warning(str(w.message))

        # Build output CSV in memory
        out = io.StringIO()
        writer = csv.writer(out)
        for id_, grade, pct in results:
            writer.writerow([id_, grade,
                             f"{pct:.1f}" if pct is not None else "NA"])

        n_ranked = sum(1 for r in results if r[2] is not None)
        n_pa = sum(1 for r in results if r[2] is None)
        st.success(
            f"Processed {len(results)} rows "
            f"({n_ranked} ranked, {n_pa} PA)."
        )

        st.download_button(
            label="Download percentile ranks CSV",
            data=out.getvalue(),
            file_name="percentile_ranks.csv",
            mime="text/csv",
        )

        with st.expander("Preview output"):
            st.code(out.getvalue(), language="text")

    except ValueError as e:
        st.error(str(e))
