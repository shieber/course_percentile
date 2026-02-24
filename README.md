# course_percentile

Computes percentile ranks for students from letter grades and optional scores.

## Usage

### Command line

```bash
python cli.py <input.csv> <output.csv>
```

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
