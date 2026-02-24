# course_percentile

Computes percentile ranks for students from letter grades and optional scores.

## Privacy

**For data containing real student IDs or other identifying information,
use the command-line tool locally** (see below). The web app processes files
on Streamlit's servers and should only be used with pseudonymized or
non-sensitive data.

## Usage

### Command line (recommended for real student data)

Clone or download the repository, then:

```bash
# install dependencies (only needed once)
pip install -r requirements.txt

# run
python cli.py <input.csv> <output.csv>
```

Warnings about score inconsistencies are printed to stderr; errors cause
a non-zero exit with a message. No data leaves your machine.

### Web app

```bash
streamlit run app.py
```

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
