"""Tests for rank_to_percentile core function."""
import pytest
import warnings

from rank_to_percentile import rank_to_percentile


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def rows(csv_str):
    """Parse a compact CSV string and run rank_to_percentile."""
    records = [line.split(',') for line in csv_str.strip().splitlines()
               if line.strip() and not line.startswith('#')]
    return rank_to_percentile(records)


def by_id(result):
    """Return {id: pct} dict from a result list."""
    return {r[0]: r[2] for r in result}


# ---------------------------------------------------------------------------
# Normal operation
# ---------------------------------------------------------------------------

def test_single_row():
    assert rows("1001,A,95")[0][2] == 50.0


def test_two_rows_same_grade():
    d = by_id(rows("1001,A,95\n1002,A,80"))
    assert d['1001'] == 100.0
    assert d['1002'] == 0.0


def test_percentile_formula():
    """(r-1)/(N-1)*100: best=100, middle=50, worst=0."""
    d = by_id(rows("1001,A,95\n1002,B,80\n1003,C,60"))
    assert d['1001'] == pytest.approx(100.0)
    assert d['1002'] == pytest.approx(50.0)
    assert d['1003'] == pytest.approx(0.0)


def test_grade_ordering():
    """A student outranks B student regardless of raw score."""
    with pytest.warns(UserWarning, match="inconsistent"):
        d = by_id(rows("1001,B,99\n1002,A,50"))
    assert d['1002'] > d['1001']


def test_ties_share_percentile():
    d = by_id(rows("1001,A,90\n1002,A,90\n1003,B,70"))
    assert d['1001'] == d['1002']


def test_output_in_input_order():
    result = rows("1001,B,70\n1002,A,95")
    assert result[0][0] == '1001'
    assert result[1][0] == '1002'


def test_comment_lines_ignored():
    result = rows("# comment\n1001,A,95\n# another\n1002,B,80")
    assert len(result) == 2
    assert by_id(result)['1001'] == 100.0


def test_no_scores_imputed_from_gpa():
    """Without scores, grade order is respected via GPA imputation."""
    d = by_id(rows("1001,A\n1002,B\n1003,E"))
    assert d['1001'] == 100.0
    assert d['1003'] == 0.0


# ---------------------------------------------------------------------------
# PA (pass) behaviour
# ---------------------------------------------------------------------------

def test_pa_excluded_from_ranking():
    """PA students are not counted in N and get no percentile."""
    d = {r[0]: r[2] for r in rows("1001,A,95\n1002,PA,80\n1003,B,70")}
    assert d['1002'] is None
    assert d['1001'] == 100.0   # N=2: A is top
    assert d['1003'] == 0.0    # N=2: B is bottom


def test_pa_interleaved_in_input_order():
    result = rows("1001,A,95\n1002,PA,80\n1003,B,70")
    assert [r[0] for r in result] == ['1001', '1002', '1003']


def test_pa_no_score_when_unscored():
    d = {r[0]: r[2] for r in rows("1001,A\n1002,PA\n1003,B")}
    assert d['1002'] is None


# ---------------------------------------------------------------------------
# FL (fail) behaviour
# ---------------------------------------------------------------------------

def test_fl_ranks_with_e_by_score():
    """FL student with higher score ranks above E student."""
    d = by_id(rows("1001,E,60\n1002,FL,70"))
    assert d['1002'] > d['1001']


def test_e_fl_same_score_share_percentile():
    result = rows("1001,E,60\n1002,FL,60")
    assert result[0][2] == result[1][2]


def test_fl_imputed_same_as_e():
    """FL and E both have GPA 0; they tie at the bottom when unscored."""
    d = by_id(rows("1001,A\n1002,E\n1003,FL"))
    assert d['1002'] == d['1003']


def test_fl_consistency_merged_with_e():
    """FL scores are merged with E for the consistency check."""
    with pytest.warns(UserWarning, match="inconsistent"):
        rows("1001,A,50\n1002,FL,90")


# ---------------------------------------------------------------------------
# Semantic validation
# ---------------------------------------------------------------------------

def test_inconsistency_warns_and_continues():
    with pytest.warns(UserWarning, match="inconsistent") as record:
        result = rows("1001,A,70\n1002,B,95")
    msg = str(record[0].message)
    assert 'A' in msg
    assert 'B' in msg
    assert len(result) == 2


def test_consistent_scores_no_warning():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        rows("1001,A,95\n1002,B,80")    # must not raise


# ---------------------------------------------------------------------------
# Syntax validation
# ---------------------------------------------------------------------------

def test_mixed_scores_raises():
    with pytest.raises(ValueError, match="all rows or for none"):
        rows("1001,A,95\n1002,B")


def test_malformed_row_raises():
    with pytest.raises(ValueError, match="malformed"):
        rows("1001\n1002,B,80")


def test_unknown_grade_raises():
    with pytest.raises(ValueError, match="unknown grade"):
        rows("1001,AB,95")


def test_non_numeric_score_raises():
    with pytest.raises(ValueError, match="non-numeric"):
        rows("1001,A,abc")
