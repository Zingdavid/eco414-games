// Test harness: runs backend/Code.gs under Node with an in-memory spreadsheet and serves it over HTTP,
// so the app can be tested against the real Apps Script code. Usage: node mock_gas.js <port>
const fs = require("fs"), http = require("http"), path = require("path"), vm = require("vm");

const sheets = {};
function Sheet(name) {
  const rows = [];
  return {
    rows,
    appendRow(r) { rows.push(r.slice()); },
    setFrozenRows() {},
    getLastRow() { return rows.length; },
    getDataRange() { return { getValues: () => rows.map((r) => r.slice()) }; },
    getRange(r, c, nr, nc) {
      return {
        getValues: () => Array.from({ length: nr }, (_, i) => (rows[r - 1 + i] || []).slice(c - 1, c - 1 + nc)),
        setValues: (v) => v.forEach((row, i) => { rows[r - 1 + i] = rows[r - 1 + i] || []; row.forEach((x, j) => (rows[r - 1 + i][c - 1 + j] = x)); }),
        clearContent: () => { for (let i = 0; i < nr; i++) if (rows[r - 1 + i]) for (let j = 0; j < nc; j++) rows[r - 1 + i][c - 1 + j] = ""; while (rows.length > 1 && rows[rows.length - 1].every((x) => x === "")) rows.pop(); },
      };
    },
  };
}
const ctx = {
  SpreadsheetApp: { getActiveSpreadsheet: () => ({ getSheetByName: (n) => sheets[n] || null, insertSheet: (n) => (sheets[n] = Sheet(n)) }) },
  ContentService: { MimeType: { JSON: "json" }, createTextOutput: (s) => ({ s, setMimeType() { return this; } }) },
  LockService: { getScriptLock: () => ({ waitLock() {}, releaseLock() {} }) },
  JSON, Date, String, Number, Math, Set, isNaN, console,
};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(__dirname, "Code.gs"), "utf8").replace('"CHANGE-ME-to-a-long-secret"', '"testkey"'), ctx);

http.createServer((req, res) => {
  const u = new URL(req.url, "http://x");
  const send = (o) => { res.writeHead(200, { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" }); res.end(o.s); };
  if (req.method === "OPTIONS") { res.writeHead(204, { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "*" }); return res.end(); }
  if (u.pathname === "/dump") { res.writeHead(200, { "Content-Type": "application/json" }); return res.end(JSON.stringify(Object.fromEntries(Object.entries(sheets).map(([k, v]) => [k, v.rows])))); }
  if (req.method === "GET") return send(ctx.doGet({ parameter: Object.fromEntries(u.searchParams) }));
  let body = ""; req.on("data", (d) => (body += d)); req.on("end", () => send(ctx.doPost({ postData: { contents: body } })));
}).listen(+process.argv[2] || 8790, () => console.log("mock Apps Script on", +process.argv[2] || 8790));
