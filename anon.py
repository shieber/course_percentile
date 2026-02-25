#!/usr/bin/env python3
"""
Anonymize or deanonymize a student grade CSV.

Usage
-----
    python anon.py <input.csv>       # anonymize
    python anon.py <ranked.csv>      # deanonymize  (auto-detected)

Mode is auto-detected: if the mapping file exists and the first student ID
in the input is a known token, the script deanonymizes; otherwise it
anonymizes.

Anonymize
    Replaces each student ID with a random 8-character hex token, shuffles
    rows, writes <stem>_anon.csv and mapping.csv (default).

Deanonymize
    Reads mapping.csv, restores real IDs, writes <stem>_deanon.csv.

Options
    -m, --mapping   mapping file  (default: mapping.csv)
    -o, --output    output file   (default: derived from input stem)

Typical workflow
    python anon.py  grades.csv              # → grades_anon.csv + mapping.csv
    python cli.py   grades_anon.csv ranked.csv   # or upload to web app
    python anon.py  ranked.csv              # → ranked_deanon.csv
"""
import argparse
import csv
import random
import secrets
import sys
from pathlib import Path

from rank_to_percentile import strip_header


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _stem(path, suffix):
    """Return path with suffix appended to stem, e.g. foo.csv → foo_anon.csv."""
    return path.parent / (path.stem + suffix + path.suffix)


def _first_id(path):
    """Return the first non-comment ID in a CSV file, or None."""
    with open(path, newline='') as f:
        for row in csv.reader(f):
            if row and not row[0].strip().startswith('#'):
                return row[0].strip()
    return None


def _load_mapping(path):
    """Return {token: (real_id, original_row)} from mapping file."""
    with open(path, newline='') as f:
        return {r[0]: (r[1], int(r[2])) for r in csv.reader(f) if r}


# ---------------------------------------------------------------------------
# core operations
# ---------------------------------------------------------------------------

def anonymize(input_path, output_path, mapping_path):
    with open(input_path, newline='') as f:
        rows = list(csv.reader(f))
    data = [r for r in rows if r and not r[0].strip().startswith('#')]
    data, had_header = strip_header(data)
    if had_header:
        print("Note: header row detected and skipped.")

    id_to_token = {}                        # real ID → token
    id_to_row   = {}                        # real ID → original row index
    for i, row in enumerate(data):
        id_ = row[0].strip()
        if id_ not in id_to_token:
            id_to_token[id_] = secrets.token_hex(4)
            id_to_row[id_]   = i

    anon = [[id_to_token[row[0].strip()]] + row[1:] for row in data]
    random.shuffle(anon)

    with open(output_path, 'w', newline='') as f:
        csv.writer(f).writerows(anon)
    with open(mapping_path, 'w', newline='') as f:
        writer = csv.writer(f)
        for id_, token in id_to_token.items():
            writer.writerow([token, id_, id_to_row[id_]])  # token first

    print(f"Anonymized   {len(data)} rows  → {output_path}")
    print(f"Mapping      {len(id_to_token)} IDs  → {mapping_path}")


def deanonymize(input_path, output_path, mapping_path):
    mapping = _load_mapping(mapping_path)   # token → real ID

    with open(input_path, newline='') as f:
        rows = [r for r in csv.reader(f)
                if r and not r[0].strip().startswith('#')]

    # Pass header row through unchanged if present
    header = None
    if rows and rows[0][0].strip() not in mapping:
        header, rows = rows[0], rows[1:]

    indexed = []
    for i, row in enumerate(rows, 1):
        token = row[0].strip()
        if token not in mapping:
            sys.exit(f"Error: unknown token {token!r} at row {i}")
        real_id, orig_row = mapping[token]
        indexed.append((orig_row, [real_id] + row[1:]))

    indexed.sort(key=lambda x: x[0])       # restore original input order
    output = [row for _, row in indexed]

    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        if header:
            writer.writerow(header)
        writer.writerows(output)
    print(f"Deanonymized {len(output)} rows → {output_path}")


# ---------------------------------------------------------------------------
# auto-detect and dispatch
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Anonymize or deanonymize a student grade CSV.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument('input',  help='input CSV file')
    ap.add_argument('-m', '--mapping', default='mapping.csv',
                    help='mapping file (default: mapping.csv)')
    ap.add_argument('-o', '--output',  default=None,
                    help='output file (default: derived from input stem)')
    args = ap.parse_args()

    input_path   = Path(args.input)
    mapping_path = Path(args.mapping)

    # Detect mode: deanonymize if mapping exists and first ID is a known token
    mode = 'anon'
    if mapping_path.exists():
        known = {r[0] for r in csv.reader(open(mapping_path, newline='')) if r}
        if _first_id(input_path) in known:
            mode = 'deanon'

    if mode == 'anon':
        out = Path(args.output) if args.output else _stem(input_path, '_anon')
        anonymize(input_path, out, mapping_path)
    else:
        out = Path(args.output) if args.output else _stem(input_path, '_deanon')
        deanonymize(input_path, out, mapping_path)


if __name__ == '__main__':
    main()
