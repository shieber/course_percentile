# course_percentile

Computes percentile ranks for students from letter grades and optional scores.

## Usage

### Command line

Clone or download the repository, then:

```bash
# install dependencies (only needed once)
pip install -r requirements.txt

# run
python cli.py <input.csv> <output.csv>
```

Warnings about score inconsistencies are printed to stderr; errors cause
a non-zero exit with a message. No data leaves your machine.

### Local web app

```bash
streamlit run app.py
```

Runs entirely on your machine. No data leaves your machine.

### Hosted web app

A hosted version is available at
[course-percentile.streamlit.app](https://course-percentile.streamlit.app).
Uploaded files are processed on Streamlit's servers, so **do not upload
files containing real student IDs or other identifying information**.

To use the hosted app with sensitive data, you can anonymize locally first:

```bash
# 1. Anonymize — replaces IDs with random tokens, shuffles rows
python anon.py grades.csv          # → grades_anon.csv + mapping.csv

# 2. Upload grades_anon.csv to the hosted app, download percentile_ranks.csv

# 3. Restore real IDs locally (mode auto-detected from mapping.csv)
python anon.py percentile_ranks.csv   # → percentile_ranks_deanon.csv
```

`mapping.csv` is the only link between tokens and real IDs — keep it private.
Use `-m` to specify a non-default mapping file, `-o` for a non-default output.
Deanonymized output is restored to the original input row order.

## Input format

CSV, no header: `id, letter_grade[, score]`

- `score` is optional; higher is better; defaults to GPA points
- Valid grades: `A A- B+ B B- C+ C C- D+ D D- E FL PA`
- `PA` (pass): excluded from ranking; receives `NA` as percentile
- `FL` (fail): ranked equally with `E`; both have GPA value 0
- Lines starting with `#` are treated as comments and ignored

## Output format

CSV, no header: `id, letter_grade, percentile_rank`

- Rows appear in original input order
- Percentile rank is 0–100 (float), or `NA` for PA students

## Ranking method

Within each grade, students are sorted by score descending, then grade
groups are concatenated from best (A) to worst (E/FL). Ranks run from
1 (worst) to N (best). Percentile = (r−1)/(N−1)×100. Tied students
share the average mid-rank. E and FL are ranked together by score.

## Running tests

```bash
pytest
```
