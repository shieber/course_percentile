#!/usr/bin/env python3
"""
Usage: python cli.py <input.csv> <output.csv>

Reads a CSV file (no header): id, letter_grade[, score]
Writes a CSV file (no header): id, letter_grade, percentile_rank

Lines starting with # are treated as comments and ignored.
PA students receive NA as percentile rank.
See rank_to_percentile.py for full documentation.
"""
import csv
import sys
import warnings

from rank_to_percentile import rank_to_percentile, strip_header


def main():
    if len(sys.argv) != 3:
        sys.exit(f"Usage: {sys.argv[0]} <input.csv> <output.csv>")

    with open(sys.argv[1], newline='') as f:
        records = [row for row in csv.reader(f)
                   if row and not row[0].strip().startswith('#')]
    records, had_header = strip_header(records)
    if had_header:
        print("Note: header row detected and skipped.", file=sys.stderr)

    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            results = rank_to_percentile(records)
        for w in caught:
            print(str(w.message), file=sys.stderr, flush=True)
    except ValueError as e:
        sys.exit(f"Error: {e}")

    with open(sys.argv[2], 'w', newline='') as f:
        writer = csv.writer(f)
        for id_, grade, pct in results:
            writer.writerow([id_, grade,
                             f"{pct:.1f}" if pct is not None else "NA"])


if __name__ == '__main__':
    main()
