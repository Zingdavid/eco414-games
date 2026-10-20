/**
 * ECO 414 Classroom Games: Google Sheet backend.
 *
 * Paste this into Extensions > Apps Script of a Google Sheet, change LECTURER_KEY, and deploy as a web app
 * (Execute as: Me; Who has access: Anyone). See SETUP.md. Students' apps send results here; only someone
 * with LECTURER_KEY can read them. Students can read only their own pairing result.
 */
const LECTURER_KEY = "CHANGE-ME-to-a-long-secret";

const HEAD = {
  Sessions: ["created", "code", "stake", "step", "currency", "title"],
  Responses: ["received", "uid", "session", "mode", "name", "student_no", "partner", "stake", "ug_offer", "ug_min_accept",
    "ug_response", "dg_gift", "guess_avg_offer", "client_time", "token"],
  Outcomes: ["paired_at", "session", "uid", "name", "offer_made", "offer_made_result", "offer_received", "offer_received_result",
    "ug_earnings", "dg_given", "dg_received", "dg_earnings", "total"],
};

function sheet_(name) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(name);
  if (!sh) {
    sh = ss.insertSheet(name);
    sh.appendRow(HEAD[name]);
    sh.setFrozenRows(1);
  }
  return sh;
}

function rows_(name) {
  const v = sheet_(name).getDataRange().getValues();
  const h = v.shift() || [];
  return v.map((r) => {
    const o = {};
    h.forEach((k, i) => (o[k] = r[i] instanceof Date ? r[i].toISOString() : r[i]));
    return o;
  });
}

function out_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

const str_ = (v, n) => String(v == null ? "" : v).slice(0, n);
const num_ = (v) => (v === "" || v == null || isNaN(Number(v)) ? "" : Math.max(0, Math.round(Number(v))));
const code_ = (v) => String(v || "").toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 8);

function doGet(e) {
  try {
    const p = (e && e.parameter) || {};
    if (p.action === "ping") return out_({ ok: true });
    if (p.action === "session") {
      const s = rows_("Sessions").filter((r) => String(r.code) === code_(p.code)).pop();
      return out_(s ? { ok: true, session: s } : { ok: false, error: "no such session" });
    }
    if (p.action === "outcome") {
      // a student may read only their own result: uid and the device token must match
      const mine = rows_("Responses").some((r) => String(r.uid) === String(p.uid) && String(r.token) === String(p.token) && p.token);
      if (!mine) return out_({ ok: false, error: "not found" });
      const o = rows_("Outcomes").filter((r) => String(r.uid) === String(p.uid)).pop();
      return out_({ ok: true, outcome: o || null });
    }
    if (p.key !== LECTURER_KEY) return out_({ ok: false, error: "key" });
    if (p.action === "check") return out_({ ok: true });
    if (p.action === "results") {
      const responses = rows_("Responses").map((r) => { delete r.token; return r; });
      return out_({ ok: true, responses: responses, sessions: rows_("Sessions") });
    }
    return out_({ ok: false, error: "unknown action" });
  } catch (err) {
    return out_({ ok: false, error: String(err) });
  }
}

function doPost(e) {
  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const b = JSON.parse((e && e.postData && e.postData.contents) || "{}");
    if (b.action === "submit") {
      const items = (b.items || []).slice(0, 50);
      const sh = sheet_("Responses");
      const n = sh.getLastRow() - 1;
      const seen = new Set(n > 0 ? sh.getRange(2, 2, n, 1).getValues().map((r) => String(r[0])) : []);
      const now = new Date();
      const add = [], done = [];
      items.forEach((x) => {
        if (!x || !x.uid) return;
        const uid = str_(x.uid, 40);
        if (!seen.has(uid)) {
          const mode = x.mode === "P" ? "P" : "S";
          add.push([now, uid, code_(x.session), mode, str_(x.name, 40), str_(x.sno, 20), str_(x.partner, 40), num_(x.stake),
            num_(x.o), num_(x.m), x.r === "A" ? "accept" : x.r === "R" ? "reject" : "", num_(x.g), num_(x.b), str_(x.t, 30), str_(x.token, 40)]);
          seen.add(uid);
        }
        done.push(uid);
      });
      if (add.length) sh.getRange(sh.getLastRow() + 1, 1, add.length, add[0].length).setValues(add);
      return out_({ ok: true, done: done });
    }
    if (b.key !== LECTURER_KEY) return out_({ ok: false, error: "key" });
    if (b.action === "createSession") {
      const code = code_(b.code);
      if (!rows_("Sessions").some((r) => String(r.code) === code)) {
        sheet_("Sessions").appendRow([new Date(), code, num_(b.stake), num_(b.step), str_(b.cur, 6), str_(b.title, 60)]);
      }
      return out_({ ok: true });
    }
    if (b.action === "saveOutcomes") {
      // replace this session's outcomes with the new pairing
      const session = code_(b.session);
      const sh = sheet_("Outcomes");
      const keep = rows_("Outcomes").filter((r) => String(r.session) !== session).map((r) => HEAD.Outcomes.map((k) => r[k]));
      const now = new Date();
      const fresh = (b.rows || []).map((r) => [now, session, str_(r.uid, 40), str_(r.name, 40), num_(r.offer_made), str_(r.offer_made_result, 10),
        num_(r.offer_received), str_(r.offer_received_result, 10), num_(r.ug_earnings), num_(r.dg_given), num_(r.dg_received), num_(r.dg_earnings), num_(r.total)]);
      const all = keep.concat(fresh);
      if (sh.getLastRow() > 1) sh.getRange(2, 1, sh.getLastRow() - 1, HEAD.Outcomes.length).clearContent();
      if (all.length) sh.getRange(2, 1, all.length, HEAD.Outcomes.length).setValues(all);
      return out_({ ok: true, saved: fresh.length });
    }
    return out_({ ok: false, error: "unknown action" });
  } catch (err) {
    return out_({ ok: false, error: String(err) });
  } finally {
    lock.releaseLock();
  }
}
