# Background and Methodology

## What this tool does

This tool assigns each student in a course a **percentile rank** based on
their letter grade and, optionally, a numerical score (such as a final exam
score, a composite score, or a score representing rank within letter grade).
The percentile rank is a number from 0 to 100 indicating where the student
stands relative to everyone else in the course: a student at the 80th
percentile performed better than 80% of their peers.

## Why percentile rank?

Raw letter grades and GPAs are useful but inherently *absolute* measures:
they don't account for differences in grading standards across courses,
instructors, or departments. A 3.7 earned in a course that gives mostly A's
carries different information than a 3.7 earned in a course with a broader
grade distribution.

Percentile rank *normalizes* across courses. A student at the 80th percentile
of their course is in the top fifth of that course, regardless of whether the
course gives mostly A's or mostly B's. This makes percentile ranks more
comparable across courses than raw grades, more robust against outliers, and
more informative for distinguishing students within a course.

---

## Ranking method

Students are ranked using a two-level sort:

1. **Letter grade (primary):** Students with higher grades always rank above
   students with lower grades. The grade order, from best to worst, is:
   A, A−, B+, B, B−, C+, C, C−, D+, D, D−, E/FL.

2. **Score within grade (secondary, optional):** Among students with the
   *same* letter grade, those with higher scores rank higher. If no scores are
   provided, GPA point values are used as a proxy (A = 4.00, A− = 3.67,
   B+ = 3.33, down to D− = 0.67, and E = FL = 0).

This hybrid approach respects the letter grade as the primary signal of
performance. An A student *always* outranks a B student, even if the A
student's numerical score happens to be lower — a situation that can arise
when scores are inconsistent with grades or when scores represent
[within-grade rankings](#two-ways-to-use-the-score-field). In these cases the
tool issues a warning but continues.

---

## The percentile formula

Once students are given a rank *r* from 1 (worst) to N (best), the percentile
rank is:

$$PR = \frac{r - 1}{N - 1} \times 100$$

This formula maps the top student exactly to **100.0** and the bottom to
**0.0**, with all others distributed evenly in between.

> Note: if only one student is in the course (N = 1), they receive **50.0** —
> consistent with the mean of the percentile distribution, which is always
> exactly 50.

### Worked example

| Student  | Grade | Score | Rank | Percentile |
|----------|-------|-------|------|------------|
| Antigone | A     | 92    | 5    | 100.0      |
| Beatrice | A     | 85    | 4    | 75.0       |
| Candide  | B+    | 91    | 3    | 50.0       |
| Dorothea | B     | 78    | 2    | 25.0       |
| Emma     | B     | 64    | 1    | 0.0        |

Note that Candide (B+, 91) ranks *below* Beatrice (A, 85) despite having a
higher score, because letter grade takes priority.

<button class="try-btn" onclick="tryExample('Antigone,A,92\nBeatrice,A,85\nCandide,B+,91\nDorothea,B,78\nEmma,B,64')">Try it in the app</button>

---

## Tie handling

Students with the **same letter grade and the same score** are considered
tied. Tied students share the **average mid-rank** of the positions they
collectively occupy.

### Example

Four students, two tied for ranks 2 and 3:

| Student  | Grade | Score | Positions | Mid-rank | Percentile |
|----------|-------|-------|-----------|----------|------------|
| Antigone | A     | 90    | 4         | 4.0      | 100.0      |
| Beatrice | A     | 80    | 2–3       | 2.5      | 50.0       |
| Candide  | A     | 80    | 2–3       | 2.5      | 50.0       |
| Dorothea | B     | 75    | 1         | 1.0      | 0.0        |

Beatrice and Candide each receive (2 + 3) / 2 = 2.5, giving
(2.5 − 1) / (4 − 1) × 100 = **50.0%**.

<button class="try-btn" onclick="tryExample('Antigone,A,90\nBeatrice,A,80\nCandide,A,80\nDorothea,B,75')">Try it in the app</button>

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

| Student  | Grade | Score | Rank | Percentile |
|----------|-------|-------|------|------------|
| Antigone | A     | 90    | 5    | 100.0      |
| Beatrice | B     | 75    | 4    | 75.0       |
| Candide  | PA    | 80    | —    | NA         |
| Dorothea | C     | 60    | 3    | 50.0       |
| Emma     | E     | 50    | 2    | 25.0       |
| Fanny    | FL    | 40    | 1    | 0.0        |

Candide (PA) is excluded: N = 5, not 6. His score has no effect on anyone
else's rank. Fanny (FL) participates in the ranking and, because her score is
lower than Emma's, lands at the bottom.

<button class="try-btn" onclick="tryExample('Antigone,A,90\nBeatrice,B,75\nCandide,PA,80\nDorothea,C,60\nEmma,E,50\nFanny,FL,40')">Try it in the app</button>

---

## Two ways to use the score field

The optional score field supports two distinct workflows:

**1. Actual numerical scores** (e.g., final exam scores, composite scores).
Here the score provides genuine performance information *across* grade
boundaries. If a lower-graded student scores higher than a higher-graded
student, the tool issues a **warning** but continues — the ranking still
respects grade order, but the inconsistency may reflect a data error.

**2. Intra-grade ranking** (ranks within each letter grade). Here the
instructor can make finer distinctions *within* each grade without having a
single numerical score. For example:

| Student  | Grade | Score |
|----------|-------|-------|
| Antigone | A     | 3     |
| Beatrice | A     | 2     |
| Candide  | A     | 1     |
| Dorothea | A−    | 2     |
| Emma     | A−    | 1     |
| Fanny    | B+    | 3     |
| Gregor   | B+    | 2     |
| Huck     | B+    | 1     |

The scores here mean "best in the A group", "second best", etc. They are never
compared *across* grade boundaries. In this workflow the tool will typically
issue a score inconsistency warning (since score values are reused across grade
groups) — these warnings are expected and can be safely ignored.

<button class="try-btn" onclick="tryExample('Antigone,A,3\nBeatrice,A,2\nCandide,A,1\nDorothea,A-,2\nEmma,A-,1\nFanny,B+,3\nGregor,B+,2\nHuck,B+,1')">Try it in the app</button>

---

## Idempotency

The output is a *fixed point* of the ranking algorithm: if you feed the output
file back as input (treating percentile ranks as scores), you get the same
output again. Percentile rank is a rank-preserving transformation — it encodes
exactly the ordering needed to reproduce itself.

> Note: idempotency holds only when there are no PA students. PA rows receive
> `NA` as their percentile, and `NA` cannot be parsed as a numeric score, so
> re-ingesting an output file with PA rows will produce an error.

---

## Privacy

This web app runs entirely in your browser using
[Pyodide](https://pyodide.org). **No data is sent to any server.**
