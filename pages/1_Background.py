import streamlit as st

st.title("Background and Methodology")

st.markdown("""
## What this tool does

This tool assigns each student in a course a **percentile rank** based on
their letter grade and, optionally, a numerical score (such as a final exam
score, a composite score, or a score representing rank within letter grade). 
The percentile rank is a number from 0 to 100 indicating where the student stands
relative to everyone else in the course: a student at the 80th percentile performed
better than 80% of their peers.

## Why percentile rank?

Raw letter grades and GPAs are useful but inherently *absolute* measures:
they don't account for differences in grading standards across courses,
instructors, or departments. A 3.7 earned in a course that gives mostly A's
carries different information than a 3.7 earned in a course with a broader
grade distribution.

Percentile rank *normalizes* across courses. A student at the 80th percentile
of their course is in the top fifth of that course, regardless of whether the
course gives mostly A's or mostly B's. This makes percentile ranks more
comparable across courses than raw grades, more robust against outliers, 
and more informative for distinguishing students within a course.

---

## Ranking method

Students are ranked using a two-level sort:

1. **Letter grade (primary):** Students with higher grades always rank above
   students with lower grades. The grade order, from best to worst, is:
   A, A−, B+, B, B−, C+, C, C−, D+, D, D−, E/FL.

2. **Score within grade (secondary):** Among students with the *same* letter
   grade, those with higher scores rank higher. If no scores are provided,
   GPA point values are used as a proxy (A = 4.00, A− = 3.67, B+ = 3.33,
   down to D− = 0.67, and E = FL = 0).

This hybrid approach respects the letter grade as the primary signal of
performance. An A student *always* outranks a B student, even if the A
student's numerical score happens to be lower — a situation that can arise
when scores are inconsistent with grades or when the scores are used to 
represent within grade rankings. In these cases, the tool issues a warning
but continues.

---

## The percentile formula

Once students are ranked from 1 (worst) to N (best), the percentile rank is:

$$PR = \\frac{r - 1}{N - 1} \\times 100$$

This formula maps the top student exactly to **100.0** and the bottom to
**0.0**, with all others distributed evenly in between.

> Note: If only one student is in the course (N = 1), they receive **50.0** —
consistent with the mid-rank convention for a single tied group.

### Worked example

| Student | Grade | Score | Rank | Percentile |
|---------|-------|-------|------|-----------|
| Alice   | A     | 92    | 5    | 100.0     |
| Bob     | A     | 85    | 4    | 75.0      |
| Carol   | B+    | 91    | 3    | 50.0      |
| Dave    | B     | 78    | 2    | 25.0      |
| Eve     | B     | 64    | 1    | 0.0       |

Note that Carol (B+, 91) ranks *below* Bob (A, 85) despite having a higher
score, because letter grade takes priority.
""")

if st.button("Try it in the app", key="ex_main"):
    st.session_state["prefill_csv"] = (
        "Alice,A,92\nBob,A,85\nCarol,B+,91\nDave,B,78\nEve,B,64"
    )
    st.switch_page("pages/Ranker.py")

st.markdown("""
---

## Tie handling

Students with the **same letter grade and the same score** are considered
tied. Tied students share the **average mid-rank** of the positions they
collectively occupy.

### Example

Four students, two tied for ranks 2 and 3:

| Student | Grade | Score | Positions | Mid-rank | Percentile |
|---------|-------|-------|-----------|----------|-----------|
| Alice   | A     | 90    | 4         | 4.0      | 100.0     |
| Bob     | A     | 80    | 2–3       | 2.5      | 50.0      |
| Carol   | A     | 80    | 2–3       | 2.5      | 50.0      |
| Dave    | B     | 75    | 1         | 1.0      | 0.0       |

Bob and Carol each receive (2 + 3) / 2 = 2.5, giving
(2.5 − 1) / (4 − 1) × 100 = **50.0%**.
""")

if st.button("Try it in the app", key="ex_ties"):
    st.session_state["prefill_csv"] = (
        "Alice,A,90\nBob,A,80\nCarol,A,80\nDave,B,75"
    )
    st.switch_page("pages/Ranker.py")

st.markdown("""
---

## Pass/Fail grades

Courses may include students enrolled on a Pass/Fail basis.

- **PA (Pass):** The student is excluded from the ranking entirely. They are
  not counted in N, and their percentile rank is reported as `NA`. PA students
  do not affect the percentile ranks of letter-graded students.

- **FL (Fail):** The student *is* included in the ranking. FL is treated as
  equivalent to E for ranking purposes — both have GPA value 0, and FL and E
  students are sorted together by score within the bottom bucket.

### Example

Six students, one PA and one FL:

| Student | Grade | Score | Rank | Percentile |
|---------|-------|-------|------|-----------|
| Alice   | A     | 90    | 5    | 100.0     |
| Bob     | B     | 75    | 4    | 75.0      |
| Carol   | PA    | 80    | —    | NA        |
| Dave    | C     | 60    | 3    | 50.0      |
| Eve     | E     | 50    | 2    | 25.0      |
| Frank   | FL    | 40    | 1    | 0.0       |

Carol (PA) is excluded: N = 5, not 6. Her score has no effect on anyone
else's rank. Frank (FL) participates in the ranking and, because his score
is lower than Eve's, lands at the bottom. If Frank and Eve had the same
score they would share a tied percentile.
""")

if st.button("Try it in the app", key="ex_pafl"):
    st.session_state["prefill_csv"] = (
        "Alice,A,90\nBob,B,75\nCarol,PA,80\nDave,C,60\nEve,E,50\nFrank,FL,40"
    )
    st.switch_page("pages/Ranker.py")

st.markdown("""
---

## Two ways to use the score field

The optional score field supports two distinct workflows:

**1. Actual numerical scores** (e.g., final exam scores, composite scores).
Here the score provides genuine performance information *across* grade
boundaries. An A student with a score of 92 and a B+ student with a score of
88 are genuinely separated by both grade and score.

If a lower-graded student scores higher than a higher-graded student (e.g.,
a B+ student scores 91 while an A− student scores 88), the tool issues a
**warning** but continues. The ranking still respects grade order — the A−
student outranks the B+ student — but the inconsistency may warrant a closer
look at the scores, as it could reflect a data error.

**2. Intra-grade ranking** (e.g., ranks within each letter grade).
Here the instructor doesn't have a single numerical score but can make finer
distinctions *within* each grade. For example:

| Student | Grade | Score |
|---------|-------|-------|
| Alice   | A     | 3     |
| Bob     | A     | 2     |
| Carol   | A     | 1     |
| Dave    | A−    | 2     |
| Eve     | A−    | 1     |
| Frank   | B+    | 3     |
| Grace   | B+    | 2     |
| Henry   | B+    | 1     |

The scores here simply mean "best in the A group", "second best in the A
group", etc. They are never compared *across* grade boundaries — an A/1
student still outranks an A−/2 student because grade takes priority. This
is a lightweight way to inject more information than the letter grade alone
without requiring a full numerical score.

In this workflow, the tool will typically issue a score inconsistency warning
— since the same score values are reused across grade groups (e.g., both the
A group and the B+ group have a student with score 3), higher-graded students
will often have lower scores than lower-graded ones numerically. These
warnings are expected and can be safely ignored; they do not indicate a data
error in this context.
""")

if st.button("Try it in the app", key="ex_intra"):
    st.session_state["prefill_csv"] = (
        "Alice,A,3\nBob,A,2\nCarol,A,1\n"
        "Dave,A-,2\nEve,A-,1\n"
        "Frank,B+,3\nGrace,B+,2\nHenry,B+,1"
    )
    st.switch_page("pages/Ranker.py")

st.markdown("""
---

## Idempotency

The output is a *fixed point* of the ranking algorithm: if you feed the
output file back as input (treating the percentile ranks as scores), you get
the same output again. This follows from the fact that percentile rank is
a rank-preserving transformation — it encodes exactly the ordering
information needed to reproduce itself, and no inconsistencies remain after
the first pass.

> Note: idempotency holds only when there are no PA students. PA rows receive
`NA` as their percentile, and `NA` cannot be parsed as a numeric score, so
re-ingesting an output file that contains PA rows will produce an error.

---

## Privacy

Uploaded files are processed on Streamlit's servers. **Do not upload files
containing real student IDs or other identifying information.** To process
sensitive data locally without any data leaving your machine, use the
command-line tool — see the
[course\\_percentile repository](https://github.com/shieber/course_percentile)
for instructions.
""")
