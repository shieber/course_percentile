"""
rank_to_percentile: compute percentile ranks from letter grades and scores.

Public API
----------
rank_to_percentile(records) -> list of (id, grade, pct) tuples
    records : iterable of (id, grade) or (id, grade, score) sequences.
    pct is a float (0-100) or None for PA students.

strip_header(records) -> (records, had_header)
    Drop the first row if it looks like a header (grade field not a valid
    grade). Returns the (possibly trimmed) list and a boolean flag.

Raises ValueError for invalid input.
Warns (UserWarning) if scores are inconsistent with grade order.
"""
import warnings
from collections import defaultdict, namedtuple
from itertools import groupby

# --- constants ---
GRADES = ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-',
          'E', 'FL']
GPA    = {g: (12 - i) / 3 for i, g in enumerate(GRADES[:11])}  # A through D-
GPA['E'] = GPA['FL'] = 0       # both failing grades have GPA value 0
VALID_GRADES = set(GRADES) | {'PA'}
BOTTOM = {'E', 'FL'}            # merged into one bucket for ranking/consistency
Row    = namedtuple('Row', ['idx', 'id', 'grade', 'score'])


def strip_header(records):
    """Drop the first row if its grade field is not a valid grade.

    Returns (records, had_header). Intended for use in I/O layers before
    passing records to rank_to_percentile().
    """
    if records and (len(records[0]) < 2
                    or str(records[0][1]).strip() not in VALID_GRADES):
        return records[1:], True
    return list(records), False


def rank_to_percentile(records):
    """
    Compute percentile ranks from letter grades (and optional scores).

    Parameters
    ----------
    records : iterable of sequences
        Each record is (id, grade) or (id, grade, score).
        All values are strings. score is optional; higher is better.

    Returns
    -------
    list of (id, grade, pct) tuples
        pct is a float (0.0-100.0) or None for PA students.
        Output order matches the input order.

    Raises
    ------
    ValueError
        For malformed records, unknown grades, non-numeric scores,
        or mixed scored/unscored records.

    Warns
    -----
    UserWarning
        If explicit scores are inconsistent with grade order.
    """
    raw = [list(r) for r in records]
    has_score = [len(r) > 2 and bool(str(r[2]).strip()) for r in raw]

    # --- validate: syntax ---
    for i, r in enumerate(raw, 1):
        if len(r) < 2 or not str(r[0]).strip() or not str(r[1]).strip():
            raise ValueError(f"malformed row at line {i}: {r}")
        if str(r[1]).strip() not in VALID_GRADES:
            raise ValueError(
                f"unknown grade {str(r[1]).strip()!r} at line {i}")

    if any(has_score) and not all(has_score):
        raise ValueError(
            "scores must be provided for all rows or for none.")
    scored = all(has_score)

    if scored:
        for i, r in enumerate(raw, 1):
            try:
                float(str(r[2]).strip())
            except ValueError:
                raise ValueError(
                    f"non-numeric score {str(r[2]).strip()!r} at line {i}")

    # --- build ---
    rows = [Row(i, str(r[0]).strip(), str(r[1]).strip(),
                float(str(r[2]).strip()) if scored else
                (None if str(r[1]).strip() == 'PA' else GPA[str(r[1]).strip()]))
            for i, r in enumerate(raw)]

    by_grade = defaultdict(list)
    for row in rows:
        if row.grade == 'PA':
            continue                    # PA excluded from ranking
        bucket = 'E' if row.grade in BOTTOM else row.grade
        by_grade[bucket].append(row)

    # --- validate: semantics ---
    if scored:
        check = defaultdict(list)
        for row in rows:
            if row.grade == 'PA':
                continue                # PA excluded from consistency check
            key = 'E' if row.grade in BOTTOM else row.grade
            check[key].append(row.score)

        seen, present = set(), []
        for g in GRADES:
            key = 'E' if g in BOTTOM else g
            if key in check and key not in seen:
                present.append(key)
                seen.add(key)

        mins = {g: min(check[g]) for g in present}
        maxs = {g: max(check[g]) for g in present}
        violations = [(g1, mins[g1], g2, maxs[g2])
                      for i, g1 in enumerate(present)
                      for g2 in present[i + 1:]
                      if mins[g1] < maxs[g2]]
        if violations:
            lines = ["Warning: scores are inconsistent with letter grades:"]
            for g1, mn, g2, mx in violations:
                lines.append(f"  {g1} (min {mn}) < {g2} (max {mx})")
            warnings.warn("\n".join(lines), UserWarning, stacklevel=2)

    # --- rank ---
    ranked = [row for g in GRADES
                   for row in sorted(by_grade.get(g, []),
                                     key=lambda r: -r.score)]

    # --- compute percentiles ---
    N, results = len(ranked), {}
    for _, group in groupby(ranked,
                            key=lambda r: (
                                'E' if r.grade in BOTTOM else r.grade,
                                r.score)):
        group = list(group)
        avg_rank = N - len(results) - (len(group) - 1) / 2
        pct = (avg_rank - 1) / (N - 1) * 100 if N > 1 else 50.0
        for r in group:
            results[r.idx] = (r.id, r.grade, pct)

    for row in rows:
        if row.grade == 'PA':
            results[row.idx] = (row.id, row.grade, None)

    return [results[i] for i in sorted(results)]
