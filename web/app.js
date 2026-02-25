// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
let pyodide     = null;
let outputCsv   = null;
let pendingData = new URLSearchParams(window.location.search).get('data');

// ---------------------------------------------------------------------------
// Initialise Pyodide and load rank_to_percentile.py
// ---------------------------------------------------------------------------
async function initPyodide() {
  pyodide = await loadPyodide();

  // Fetch the core module from the parent directory
  const resp = await fetch('../rank_to_percentile.py');
  if (!resp.ok) throw new Error('Could not load rank_to_percentile.py');
  const code = await resp.text();
  pyodide.runPython(code);

  document.getElementById('pyodide-status').style.display = 'none';
  document.getElementById('file-input').disabled = false;

  // Pre-fill from ?data= URL parameter (e.g. from Background "Try it" buttons)
  if (pendingData) {
    const csv = decodeURIComponent(pendingData);
    pendingData = null;
    document.getElementById('file-name').textContent = '(example from Background)';
    showPreview('input-preview', 'input-pre', csv);
    processCSV(csv);
  }
}

initPyodide().catch(err => {
  document.getElementById('pyodide-status').textContent =
    'Failed to load Python runtime: ' + err.message;
});

// ---------------------------------------------------------------------------
// File upload handler
// ---------------------------------------------------------------------------
document.getElementById('file-input').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  document.getElementById('file-name').textContent = file.name;
  clearResults();

  const text = await file.text();
  showPreview('input-preview', 'input-pre', text);

  if (!pyodide) {
    showError('Python runtime is not ready yet. Please wait.');
    return;
  }

  processCSV(text);
});

// ---------------------------------------------------------------------------
// Core processing (calls Python via Pyodide)
// ---------------------------------------------------------------------------
function processCSV(text) {
  // Parse CSV in JS: split lines, skip blanks and # comments, split on comma
  const lines = text.split('\n')
    .map(l => l.trimEnd())
    .filter(l => l.length > 0 && !l.trimStart().startsWith('#'));

  const records = lines.map(l => l.split(',').map(f => f.trim()));

  // Strip header if first row's grade field is not a valid grade
  const { records: cleanRecords, hadHeader } = stripHeader(records);

  if (hadHeader) {
    show('header-notice', 'Header row detected and skipped.');
  }

  // Pass records into Python and call rank_to_percentile
  try {
    pyodide.globals.set('_records', pyodide.toPy(cleanRecords));

    const result = pyodide.runPython(`
import warnings as _warnings
_caught = []
with _warnings.catch_warnings(record=True) as _w:
    _warnings.simplefilter("always")
    _result = rank_to_percentile(_records)
for _wi in _w:
    _caught.append(str(_wi.message))
(_result, _caught)
`);

    const [pyResult, pyWarnings] = result.toJs({ depth: -1 });

    if (pyWarnings.length > 0) {
      showWarning(pyWarnings.join('\n\n'));
    }

    // Build output CSV
    const rows = ['Student ID,Letter Grade,Percentile Rank'];
    for (const row of pyResult) {
      const [id, grade, pct] = row;
      rows.push([id, grade, pct == null ? 'NA' : pct.toFixed(1)].join(','));
    }
    outputCsv = rows.join('\n') + '\n';

    const nRanked = [...pyResult].filter(r => r[2] != null).length;
    const nPA     = [...pyResult].filter(r => r[2] == null).length;
    const note    = hadHeader ? ' (header row skipped)' : '';
    show('success-box',
      `Processed ${pyResult.length} rows (${nRanked} ranked, ${nPA} PA)${note}.`);

    document.getElementById('download-btn').style.display = 'inline-block';
    showPreview('output-preview', 'output-pre', outputCsv);

  } catch (err) {
    // Extract the Python error message
    const msg = err.message.split('\n').filter(l => l.trim()).pop() || err.message;
    showError(msg.replace(/^.*?Error:\s*/, ''));
  }
}

// ---------------------------------------------------------------------------
// Header detection (mirrors rank_to_percentile.strip_header)
// ---------------------------------------------------------------------------
const VALID_GRADES = new Set([
  'A','A-','B+','B','B-','C+','C','C-','D+','D','D-','E','FL','PA'
]);

function stripHeader(records) {
  if (records.length > 0 &&
      (records[0].length < 2 || !VALID_GRADES.has(records[0][1]))) {
    return { records: records.slice(1), hadHeader: true };
  }
  return { records, hadHeader: false };
}

// ---------------------------------------------------------------------------
// UI helpers
// ---------------------------------------------------------------------------
function show(id, text) {
  const el = document.getElementById(id);
  el.textContent = text;
  el.style.display = 'block';
}

function showWarning(text) {
  const el = document.getElementById('warning-box');
  el.textContent = text;
  el.style.display = 'block';
}

function showError(text) {
  const el = document.getElementById('error-box');
  el.textContent = 'Error: ' + text;
  el.style.display = 'block';
}

function showPreview(detailsId, preId, text) {
  document.getElementById(detailsId).style.display = 'block';
  document.getElementById(preId).textContent = text;
}

function clearResults() {
  outputCsv = null;
  for (const id of ['header-notice','warning-box','error-box','success-box']) {
    const el = document.getElementById(id);
    el.textContent = '';
    el.style.display = 'none';
  }
  document.getElementById('download-btn').style.display = 'none';
  document.getElementById('input-preview').style.display  = 'none';
  document.getElementById('output-preview').style.display = 'none';
}

function resetApp() {
  const input = document.getElementById('file-input');
  input.value = '';
  document.getElementById('file-name').textContent = 'No file chosen';
  clearResults();
}

// ---------------------------------------------------------------------------
// Download
// ---------------------------------------------------------------------------
function downloadResult() {
  if (!outputCsv) return;
  const blob = new Blob([outputCsv], { type: 'text/csv' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = 'percentile_ranks.csv';
  a.click();
  URL.revokeObjectURL(url);
}
