"""Tests for rank_to_percentile core function."""
import pytest
import warnings

from rank_to_percentile import rank_to_percentile, strip_header


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


# ---------------------------------------------------------------------------
# Full grade ordering
# ---------------------------------------------------------------------------

def test_full_grade_ordering_without_scores():
    """All 13 grades rank in the correct order when no scores are given."""
    grades = ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-',
              'E', 'FL']
    csv_str = '\n'.join(f'{i},{g}' for i, g in enumerate(grades))
    result = rank_to_percentile([line.split(',') for line in csv_str.splitlines()])
    pct = {r[1] if r[1] != 'FL' else 'FL': r[2] for r in result}
    # Each grade must rank strictly above the next (FL ties with E)
    for better, worse in zip(grades[:-2], grades[1:-1]):
        assert pct[better] > pct[worse], f"{better} should outrank {worse}"
    assert pct['E'] == pct['FL']           # E and FL share bottom bucket


# ---------------------------------------------------------------------------
# Additional tie handling
# ---------------------------------------------------------------------------

def test_three_way_tie():
    """Three students with the same grade and score all share 50.0."""
    d = by_id(rows("1001,A,80\n1002,A,80\n1003,A,80"))
    assert d['1001'] == d['1002'] == d['1003'] == 50.0


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_all_pa_input():
    """All-PA input: N=0, everyone gets None, no error."""
    result = rows("1001,PA\n1002,PA\n1003,PA")
    assert all(r[2] is None for r in result)
    assert len(result) == 3


def test_whitespace_stripped_from_id_and_grade():
    """Leading/trailing whitespace in ID and grade fields is ignored."""
    result = rank_to_percentile([['  1001  ', '  A  ', '90'],
                                 ['  1002  ', '  B  ', '70']])
    ids = [r[0] for r in result]
    assert '1001' in ids
    assert '1002' in ids


# ---------------------------------------------------------------------------
# Warning message format
# ---------------------------------------------------------------------------

def test_warning_message_starts_with_Warning():
    with pytest.warns(UserWarning) as record:
        rows("1001,A,50\n1002,B,90")
    assert str(record[0].message).startswith("Warning:")


def test_warning_lists_all_violation_pairs():
    """Three grades with overlapping scores produce two violation pairs."""
    with pytest.warns(UserWarning) as record:
        rows("1001,A,50\n1002,B,70\n1003,C,90")
    msg = str(record[0].message)
    assert 'A' in msg and 'B' in msg and 'C' in msg


# ---------------------------------------------------------------------------
# strip_header
# ---------------------------------------------------------------------------

def parse(csv_str):
    """Parse a CSV string into a list of rows (no rank_to_percentile call)."""
    return [line.split(',') for line in csv_str.strip().splitlines()
            if line.strip()]


def test_strip_header_detects_text_header():
    records, had = strip_header(parse("id,grade,score\n1001,A,92"))
    assert had is True
    assert len(records) == 1
    assert records[0][0] == '1001'


def test_strip_header_no_header():
    records, had = strip_header(parse("1001,A,92\n1002,B,80"))
    assert had is False
    assert len(records) == 2


def test_strip_header_empty_input():
    records, had = strip_header([])
    assert had is False
    assert records == []


def test_strip_header_header_only():
    records, had = strip_header(parse("id,grade,score"))
    assert had is True
    assert records == []


def test_strip_header_preserves_data_values():
    records, had = strip_header(parse("id,grade\n1001,A\n1002,B"))
    assert had is True
    assert [r[1] for r in records] == ['A', 'B']


def test_strip_header_end_to_end():
    """rank_to_percentile on header-stripped input gives correct result."""
    records, _ = strip_header(parse("id,grade,score\n1001,A,90\n1002,B,70"))
    result = rank_to_percentile(records)
    d = {r[0]: r[2] for r in result}
    assert d['1001'] == 100.0
    assert d['1002'] == 0.0
