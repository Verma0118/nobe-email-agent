/**
 * NOBE outreach brain: a Google Sheet behind a tiny web API.
 * The owner deploys this once (see server/SETUP.md). Exec members never need a
 * Google or GitHub account: the agent calls this URL with the shared key.
 *
 * Every write runs under LockService.getScriptLock(), so two people claiming
 * the same contact at the same moment are handled one after the other and the
 * second one is told the contact is taken.
 */
const SHEET_NAME = 'Contacts';
const HEADERS = ['email', 'name', 'role', 'company', 'domain', 'committee', 'sender', 'status',
                 'claimed_at', 'updated_at', 'gmail_draft_id', 'notes', 'history'];
const STATUSES = ['claimed', 'drafted', 'sent', 'replied', 'call', 'client', 'dead', 'released'];

/** Run once from the editor: creates the sheet and prints the shared key. */
function setup() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(SHEET_NAME);
  if (!sh) sh = ss.insertSheet(SHEET_NAME);
  sh.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]).setFontWeight('bold');
  sh.setFrozenRows(1);
  const props = PropertiesService.getScriptProperties();
  if (!props.getProperty('KEY')) props.setProperty('KEY', Utilities.getUuid());
  Logger.log('Shared key (send this privately to exec): ' + props.getProperty('KEY'));
}

function doPost(e) {
  let req;
  try { req = JSON.parse(e.postData.contents); } catch (err) { return out({ ok: false, error: 'bad json' }); }
  if (!req.key || req.key !== PropertiesService.getScriptProperties().getProperty('KEY')) {
    return out({ ok: false, error: 'bad key' });
  }
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(20000)) return out({ ok: false, error: 'busy, try again' });
  try {
    if (req.action === 'list') return out({ ok: true, rows: readAll().map(r => r.row) });
    if (req.action === 'claim') return out(claim(req.row));
    if (req.action === 'set') return out(setStatus(req));
    return out({ ok: false, error: 'unknown action' });
  } finally {
    lock.releaseLock();
  }
}

function sheet() { return SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME); }

function readAll() {
  const values = sheet().getDataRange().getValues();
  return values.slice(1).map((v, i) => {
    const row = {};
    HEADERS.forEach((h, j) => { row[h] = v[j] === undefined ? '' : String(v[j]); });
    try { row.history = JSON.parse(row.history || '[]'); } catch (err) { row.history = []; }
    return { index: i + 2, row: row };
  });
}

function write(index, row) {
  const vals = HEADERS.map(h => h === 'history' ? JSON.stringify(row.history || []) : (row[h] || ''));
  sheet().getRange(index, 1, 1, HEADERS.length).setValues([vals]);
}

function find(email) {
  email = String(email || '').trim().toLowerCase();
  return readAll().find(r => r.row.email === email);
}

function claim(row) {
  if (!row || !row.email) return { ok: false, error: 'missing email' };
  row.email = row.email.trim().toLowerCase();
  const existing = find(row.email);
  if (existing && existing.row.status !== 'released') {
    return { ok: false, blocked: true, row: existing.row };
  }
  if (existing) {
    row.history = (existing.row.history || []).concat(row.history || []);
    write(existing.index, row);
  } else {
    write(sheet().getLastRow() + 1, row);
  }
  return { ok: true, row: row };
}

function setStatus(req) {
  if (STATUSES.indexOf(req.status) < 0) return { ok: false, error: 'bad status' };
  const hit = find(req.email);
  if (!hit) return { ok: false, error: 'not in brain' };
  const row = hit.row;
  if (req.status === 'released' && ['claimed', 'drafted'].indexOf(row.status) < 0) {
    return { ok: false, error: 'already ' + row.status + ', cannot release' };
  }
  row.status = req.status;
  row.updated_at = req.at;
  if (req.draft_id) row.gmail_draft_id = req.draft_id;
  if (req.note) row.notes = ((row.notes || '') + '\n' + req.at.slice(0, 10) + ' ' + req.by + ': ' + req.note).trim();
  row.history.push({ at: req.at, by: req.by, status: req.status, note: req.note || '' });
  write(hit.index, row);
  return { ok: true, row: row };
}

function out(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
