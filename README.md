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

### Web app

No Python installation or `pip install` is needed — the app runs entirely
in the browser via Pyodide, which downloads automatically from a CDN.

Because the app fetches `rank_to_percentile.py` at startup, it must be
served over HTTP rather than opened as a local file. The simplest way
(Python is already on your machine for the CLI):

```bash
# from the repo root
python -m http.server 8000
```

Then open `http://localhost:8000/web/` in your browser. No data is
uploaded anywhere.

## Input format

CSV with columns: `id, letter_grade[, score]`

- A header row is optional and will be detected and skipped automatically
- `score` is optional; higher is better; defaults to GPA points
- Valid grades: `A A- B+ B B- C+ C C- D+ D D- E FL PA`
- `PA` (pass): excluded from ranking; receives `NA` as percentile
- `FL` (fail): ranked equally with `E`; both have GPA value 0
- Lines starting with `#` are treated as comments and ignored

## Output format

CSV with header `Student ID, Letter Grade, Percentile Rank`

- Rows appear in original input order
- Percentile rank is 0–100 (float), or `NA` for PA students
- Output can be fed back as input (idempotent), except for PA rows

## Ranking method

Within each grade, students are sorted by score descending, then grade
groups are concatenated from best (A) to worst (E/FL). Ranks run from
1 (worst) to N (best). Percentile = (r−1)/(N−1)×100. Tied students
share the average mid-rank. E and FL are ranked together by score.
Single-student courses receive a percentile rank of 50.

## Unit tests

The test suite covers the core ranking logic (`rank_to_percentile.py`)
and the CLI wrapper (`cli.py`). To run:

```bash
pytest
```

Or verbosely:

```bash
pytest -v
```

`tests/test_rank_to_percentile.py` tests the pure functional core: grade
ordering, score imputation, tie handling, PA/FL behavior, the consistency
warning, the `strip_header` utility, and edge cases (N=1, all-PA input,
whitespace stripping, etc.).

`tests/test_cli.py` tests the I/O layer end-to-end via subprocess: output
format (header row), comment and header skipping, idempotency, PA/FL
output, error exits (mixed scores, bad arguments), and the inconsistency
warning on stderr.
