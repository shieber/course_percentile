"""Integration tests for cli.py.

Each test invokes cli.py as a subprocess so that the full I/O layer
(argument parsing, CSV reading/writing, header detection, stderr
messages, exit codes) is exercised in addition to the core logic.
"""
import csv
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

CLI = Path(__file__).parent.parent / "cli.py"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run_cli(input_text, tmp_path, *, input_name="input.csv"):
    """Write input_text to a temp file, run cli.py, return CompletedProcess."""
    in_path  = tmp_path / input_name
    out_path = tmp_path / "output.csv"
    in_path.write_text(textwrap.dedent(input_text))
    result = subprocess.run(
        [sys.executable, str(CLI), str(in_path), str(out_path)],
        capture_output=True, text=True,
    )
    return result, out_path


def read_output(out_path):
    """Return list of rows (each a list of strings) from the output CSV."""
    with open(out_path, newline='') as f:
        return list(csv.reader(f))


# ---------------------------------------------------------------------------
# Output format
# ---------------------------------------------------------------------------

def test_header_row_present(tmp_path):
    result, out_path = run_cli("""\
        1001,A
        1002,B
        """, tmp_path)
    assert result.returncode == 0
    rows = read_output(out_path)
    assert rows[0] == ['Student ID', 'Letter Grade', 'Percentile Rank']


def test_data_rows_follow_header(tmp_path):
    result, out_path = run_cli("""\
        1001,A
        1002,B
        """, tmp_path)
    assert result.returncode == 0
    rows = read_output(out_path)
    assert len(rows) == 3          # header + 2 data rows
    assert rows[1][0] == '1001'
    assert rows[2][0] == '1002'


# ---------------------------------------------------------------------------
# Basic ranking
# ---------------------------------------------------------------------------

def test_single_student_gets_50(tmp_path):
    _, out_path = run_cli("1001,A\n", tmp_path)
    rows = read_output(out_path)
    assert rows[1][2] == '50.0'


def test_two_students_ranked_correctly(tmp_path):
    _, out_path = run_cli("""\
        1001,A
        1002,B
        """, tmp_path)
    pcts = {r[0]: r[2] for r in read_output(out_path)[1:]}
    assert pcts['1001'] == '100.0'
    assert pcts['1002'] == '0.0'


def test_scores_used_for_intra_grade_ranking(tmp_path):
    _, out_path = run_cli("""\
        1001,B,90
        1002,B,70
        """, tmp_path)
    pcts = {r[0]: r[2] for r in read_output(out_path)[1:]}
    assert pcts['1001'] == '100.0'
    assert pcts['1002'] == '0.0'


def test_ties_share_average_rank(tmp_path):
    _, out_path = run_cli("""\
        1001,B,75
        1002,B,75
        1003,C,50
        """, tmp_path)
    pcts = {r[0]: r[2] for r in read_output(out_path)[1:]}
    # 1001 and 1002 tie for ranks 2 and 3 → average rank 2.5 → (2.5-1)/(3-1)*100 = 75.0
    assert pcts['1001'] == '75.0'
    assert pcts['1002'] == '75.0'
    assert pcts['1003'] == '0.0'


# ---------------------------------------------------------------------------
# PA / FL
# ---------------------------------------------------------------------------

def test_pa_student_gets_na(tmp_path):
    _, out_path = run_cli("""\
        1001,A
        1002,PA
        """, tmp_path)
    rows = read_output(out_path)
    pa_row = next(r for r in rows[1:] if r[0] == '1002')
    assert pa_row[2] == 'NA'


def test_pa_student_not_counted_in_n(tmp_path):
    # Without PA: 1001 vs 1002 → 100.0 and 0.0
    # PA 1003 must not shift those ranks
    _, out_path = run_cli("""\
        1001,A
        1002,B
        1003,PA
        """, tmp_path)
    pcts = {r[0]: r[2] for r in read_output(out_path)[1:]}
    assert pcts['1001'] == '100.0'
    assert pcts['1002'] == '0.0'


def test_fl_student_gets_rank(tmp_path):
    _, out_path = run_cli("""\
        1001,A
        1002,FL
        """, tmp_path)
    pcts = {r[0]: r[2] for r in read_output(out_path)[1:]}
    assert pcts['1002'] == '0.0'


# ---------------------------------------------------------------------------
# Comment lines
# ---------------------------------------------------------------------------

def test_comment_lines_ignored(tmp_path):
    _, out_path = run_cli("""\
        # this is a comment
        1001,A
        1002,B
        """, tmp_path)
    rows = read_output(out_path)
    assert len(rows) == 3          # header + 2 data rows (comment excluded)


# ---------------------------------------------------------------------------
# Input header detection
# ---------------------------------------------------------------------------

def test_input_header_skipped_silently(tmp_path):
    result, out_path = run_cli("""\
        Student ID,Letter Grade,Score
        1001,A,95
        1002,B,80
        """, tmp_path)
    assert result.returncode == 0
    rows = read_output(out_path)
    assert len(rows) == 3          # output header + 2 data rows


def test_input_header_notice_on_stderr(tmp_path):
    result, _ = run_cli("""\
        Student ID,Letter Grade
        1001,A
        1002,B
        """, tmp_path)
    assert "header row detected" in result.stderr.lower()


# ---------------------------------------------------------------------------
# Idempotency (no PA rows)
# ---------------------------------------------------------------------------

def test_idempotent_without_pa(tmp_path):
    result1, out1 = run_cli("""\
        1001,A,95
        1002,A-,88
        1003,B,75
        1004,FL,10
        """, tmp_path)
    assert result1.returncode == 0
    first_pass = read_output(out1)

    out2 = tmp_path / "output2.csv"
    result2 = subprocess.run(
        [sys.executable, str(CLI), str(out1), str(out2)],
        capture_output=True, text=True,
    )
    assert result2.returncode == 0
    second_pass = read_output(out2)
    assert first_pass == second_pass


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_mixed_scores_exits_nonzero(tmp_path):
    result, _ = run_cli("""\
        1001,A,95
        1002,B
        """, tmp_path)
    assert result.returncode != 0
    assert "scores must be provided" in result.stderr.lower()


def test_wrong_arg_count_exits_nonzero(tmp_path):
    result = subprocess.run(
        [sys.executable, str(CLI)],
        capture_output=True, text=True,
    )
    assert result.returncode != 0


def test_missing_input_file_exits_nonzero(tmp_path):
    out_path = tmp_path / "output.csv"
    result = subprocess.run(
        [sys.executable, str(CLI), str(tmp_path / "nonexistent.csv"), str(out_path)],
        capture_output=True, text=True,
    )
    assert result.returncode != 0


# ---------------------------------------------------------------------------
# Inconsistency warning
# ---------------------------------------------------------------------------

def test_inconsistent_scores_warns_on_stderr(tmp_path):
    # 1001 has grade A but lower score than 1002 with grade B
    result, out_path = run_cli("""\
        1001,A,50
        1002,B,90
        """, tmp_path)
    assert result.returncode == 0          # should not exit
    assert "Warning" in result.stderr


def test_inconsistent_scores_still_produces_output(tmp_path):
    result, out_path = run_cli("""\
        1001,A,50
        1002,B,90
        """, tmp_path)
    rows = read_output(out_path)
    assert len(rows) == 3                  # header + 2 data rows


# ---------------------------------------------------------------------------
# Output overwrites existing file
# ---------------------------------------------------------------------------

def test_output_overwrites_existing(tmp_path):
    out_path = tmp_path / "output.csv"
    out_path.write_text("old content\n")
    run_cli("1001,A\n", tmp_path)
    assert "old content" not in out_path.read_text()
