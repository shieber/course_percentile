"""
Course Grade Percentile Ranker — main page content.
"""
import csv
import io
import warnings

import streamlit as st

from rank_to_percentile import rank_to_percentile

st.title("Course Grade Percentile Ranker")

st.caption(
    "For the full methodology and worked examples, see "
    "[Background](/Background)."
)

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

# --- session state for reset and prefill ---
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0


def _reset():
    st.session_state.uploader_key += 1


# Transfer one-shot prefill into a persistent key so it survives reruns
# (e.g. triggered by the download button) until explicitly cleared.
if "prefill_csv" in st.session_state:
    st.session_state["current_prefill"] = st.session_state.pop("prefill_csv")

if "current_prefill" in st.session_state:
    text = st.session_state["current_prefill"]
    col1, col2 = st.columns([4, 1], vertical_alignment="center")
    with col1:
        st.info("Example loaded from Background. Click **Reset** to upload a different file.")
    with col2:
        if st.button("Reset", use_container_width=True):
            del st.session_state["current_prefill"]
            st.rerun()
else:
    col1, col2 = st.columns([4, 1])
    with col1:
        uploaded = st.file_uploader(
            "Choose a CSV file",
            type=["csv", "txt"],
            key=f"uploader_{st.session_state.uploader_key}",
        )
    with col2:
        st.write("")   # vertical alignment spacer
        st.write("")
        st.button("Reset", on_click=_reset, use_container_width=True)
    text = uploaded.read().decode("utf-8") if uploaded is not None else None

if text is not None:
    records = [row for row in csv.reader(io.StringIO(text))
               if row and not row[0].strip().startswith('#')]

    with st.expander("Preview input"):
        st.code(text, language="text")

    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            results = rank_to_percentile(records)

        for w in caught:
            msg_lines = str(w.message).split('\n')
            header = msg_lines[0]
            items = '\n'.join(
                f"- {l.strip()}" for l in msg_lines[1:] if l.strip()
            )
            st.warning(header + ('\n\n' + items if items else ''))

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
