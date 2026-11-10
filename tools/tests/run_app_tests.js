// Headless-Chrome tests for a rendered Dinner Time! app against an in-page Google Sheets emulator.
// usage: npm i puppeteer-core && node run_app_tests.js <rendered build dir> <private terms file or "-">   (set CHROME to your Chrome path)
const puppeteer = require("puppeteer-core");
const fs = require("fs"), path = require("path");
const build = path.resolve(process.argv[2]);
const denyFile = process.argv[3];
const deny = denyFile && denyFile !== "-" ? fs.readFileSync(denyFile, "utf8").split("\n").map(s => s.trim()).filter(s => s && !s.startsWith("#")) : [];
const appFile = path.join(build, "app", "dinner-time.html");
const html = fs.readFileSync(appFile, "utf8");
const cfg = JSON.parse(html.slice(html.indexOf("/*DT_CONFIG_START*/") + 19, html.indexOf("/*DT_CONFIG_END*/")));
const reqs = {};
for (const k of ["shopping", "freezer", "recipes", "gear", "bugs"]) reqs[cfg.sheets[k]] = JSON.parse(fs.readFileSync(path.join(build, "sheet-requests", k + ".json"), "utf8")).requests;

// ---- runs inside the page before the app's script ----
function installRuntime(opts) {
  const colIdx = L => { let n = 0; for (const c of L) n = n * 26 + (c.charCodeAt(0) - 64); return n - 1; };
  const books = {};   // id -> {rev, sheets:[{id,title,rows:[[]]}]}
  const cellText = c => { const v = c && c.userEnteredValue; if (!v) return ""; if (v.stringValue != null) return String(v.stringValue);
    if (v.numberValue != null) { const f = c.userEnteredFormat && c.userEnteredFormat.numberFormat; if (f && f.type === "DATE") { const d = new Date(Math.round((v.numberValue - 25569) * 86400000)); return String(d.getUTCMonth() + 1).padStart(2, "0") + "/" + String(d.getUTCDate()).padStart(2, "0") + "/" + d.getUTCFullYear(); } return String(v.numberValue); }
    return ""; };
  function apply(id, requests, wc) {
    const b = books[id] || (books[id] = { rev: 1, sheets: [{ id: 0, title: "Sheet1", rows: [] }] });
    if (wc && wc.requiredRevisionId && String(wc.requiredRevisionId) !== String(b.rev)) throw { code: "tool_error", message: "revision mismatch" };
    const sh = sid => { const s = b.sheets.find(x => x.id === sid); if (!s) throw { code: "tool_error", message: "no sheet " + sid }; return s; };
    for (const r of requests) {
      if (r.updateSheetProperties) { const p = r.updateSheetProperties.properties; sh(p.sheetId).title = p.title; }
      else if (r.addSheet) { const p = r.addSheet.properties; if (b.sheets.some(x => x.id === p.sheetId || x.title === p.title)) throw { code: "tool_error", message: "duplicate sheet" }; b.sheets.push({ id: p.sheetId, title: p.title, rows: [] }); }
      else if (r.updateCells) { const u = r.updateCells, s = sh(u.start.sheetId); (u.rows || []).forEach((row, i) => { const ri = u.start.rowIndex + i; while (s.rows.length <= ri) s.rows.push([]); (row.values || []).forEach((c, j) => { const ci = (u.start.columnIndex || 0) + j; while (s.rows[ri].length <= ci) s.rows[ri].push(""); s.rows[ri][ci] = cellText(c); }); }); }
      else if (r.appendCells) { const u = r.appendCells, s = sh(u.sheetId); let last = s.rows.length; while (last > 0 && s.rows[last - 1].every(v => v === "")) last--; s.rows.length = last; for (const row of u.rows || []) s.rows.push((row.values || []).map(cellText)); }
      else if (r.deleteDimension) { const g = r.deleteDimension.range, s = sh(g.sheetId); if (g.dimension !== "ROWS") throw { code: "tool_error", message: "only ROWS" }; s.rows.splice(g.startIndex, g.endIndex - g.startIndex); }
      else throw { code: "tool_error", message: "unsupported request " + Object.keys(r)[0] };
    }
    b.rev++;
  }
  for (const [id, rq] of Object.entries(opts.reqs)) apply(id, rq);
  function values(id, range) {
    const b = books[id]; if (!b) throw { code: "tool_error", message: "Requested entity was not found" };
    const m = /^'?([^'!]+)'?!([A-Z]+)(\d*):([A-Z]+)(\d*)$/.exec(range); if (!m) throw { code: "tool_error", message: "bad range " + range };
    const s = b.sheets.find(x => x.title === m[1]); if (!s) throw { code: "tool_error", message: "Unable to parse range: " + range };
    const a = colIdx(m[2]), z = colIdx(m[4]);
    const out = s.rows.map(r => { const x = r.slice(a, z + 1); while (x.length && x[x.length - 1] === "") x.pop(); return x; });
    while (out.length && !out[out.length - 1].length) out.pop();
    return { range, values: out };
  }
  const watchers = [];
  const emit = w => { try { w.cb({ type: "data", result: { payload: values(w.input.spreadsheetId, w.input.range), cache: { storedAt: Date.now() } } }); } catch (e) { w.cb({ type: "error", error: e }); } };
  const mcp = {
    async callTool(server, tool, input) {
      if (server !== "Google Sheets") throw { code: "not_in_manifest" };
      if (tool === "get_values") return { payload: values(input.spreadsheetId, input.range) };
      if (tool === "get_spreadsheet") { const b = books[input.spreadsheetId]; if (!b) throw { code: "tool_error", message: "not found" }; return { payload: { spreadsheetId: input.spreadsheetId, revisionId: String(b.rev), sheets: b.sheets.map(s => ({ properties: { sheetId: s.id, title: s.title } })) } }; }
      if (tool === "update_spreadsheet") { apply(input.spreadsheetId, input.requests, input.writeControl); setTimeout(() => watchers.forEach(emit), 0); return { payload: {} }; }
      throw { code: "not_in_manifest" };
    },
    watchTool(server, tool, input, cb) { const w = { input, cb }; watchers.push(w); setTimeout(() => emit(w), 0); return () => {}; },
    async invalidate() { setTimeout(() => watchers.forEach(emit), 0); },
    async listTools() { return { fileArgs: false }; },
  };
  const docs = {}; const subs = [];
  const collOf = p => p.split("/").slice(0, -1).join("/");
  const fire = c => subs.filter(s => s.c === c).forEach(s => s.cb({ docs: Object.keys(docs).filter(p => collOf(p) === c).map(p => ({ id: p.split("/").pop(), data: () => JSON.parse(JSON.stringify(docs[p])) })), metadata: { fromCache: false } }));
  const db = {
    collection(c) { const q = { orderBy() { return q; }, limit() { return q; }, onSnapshot(cb) { const s = { c, cb }; subs.push(s); setTimeout(() => fire(c), 0); return () => {}; } }; return q; },
    doc(p) { return {
      async set(d) { docs[p] = JSON.parse(JSON.stringify(d)); setTimeout(() => fire(collOf(p)), 0); },
      async update(d) { docs[p] = Object.assign(docs[p] || {}, JSON.parse(JSON.stringify(d))); setTimeout(() => fire(collOf(p)), 0); },
      async delete() { delete docs[p]; setTimeout(() => fire(collOf(p)), 0); },
      async get() { return { exists: p in docs, data: () => docs[p] }; },
      async acquire() { return { acquired: true }; },
    }; },
  };
  const user = { async isOwner() { return !!opts.owner; }, async id() { return opts.uid; }, async can() { return true; } };
  const room = { on() {}, onPeers() {}, async presence() {}, async emit() {} };
  const parts = { db, user, mcp: opts.mcp ? mcp : null, room, permissions: { async manage() {} } };
  window.__emu = { books, docs, tab: (id, t) => books[id].sheets.find(s => s.title === t).rows };
  if (opts.runtime) window.claude = { use: n => (n in parts && parts[n]) ? Promise.resolve(parts[n]) : Promise.reject({ code: "capability_disabled" }) };
}

const results = []; let failed = 0;
const ok = (name, cond, detail) => { results.push((cond ? "PASS " : "FAIL ") + name + (cond ? "" : "  -> " + (detail || ""))); if (!cond) failed++; };
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function open(browser, opts, width) {
  const page = await browser.newPage();
  await page.setViewport({ width: width || 390, height: 844, isMobile: true, hasTouch: true });
  const errors = [], hosts = new Set();
  page.on("pageerror", e => errors.push(String(e)));
  await page.setRequestInterception(true);
  page.on("request", r => { const u = new URL(r.url()); if (u.protocol === "file:") return r.continue(); hosts.add(u.host); r.abort(); });
  await page.evaluateOnNewDocument(installRuntime, Object.assign({ reqs }, opts));
  await page.goto("file://" + appFile);
  await sleep(1500);
  return { page, errors, hosts };
}
const waitFor = async (page, fn, arg, ms) => { const t = Date.now(); for (;;) { const v = await page.evaluate(fn, arg); if (v) return v; if (Date.now() - t > (ms || 8000)) return null; await sleep(150); } };

(async () => {
  const browser = await puppeteer.launch({ executablePath: process.env.CHROME || "/usr/bin/google-chrome", args: ["--no-sandbox", "--disable-gpu"] });
  const P = cfg.people, p0 = P[0], S_ = cfg.sheets;

  // 1. owner with Sheets access
  let { page, errors, hosts } = await open(browser, { runtime: true, mcp: true, owner: true, uid: "u-owner" });
  ok("loads with no page errors (owner)", errors.length === 0, errors.join(" | "));
  ok("sheets connected", await waitFor(page, () => S.access === "ok"));
  ok("owner is recognised as the settings owner", await waitFor(page, o => S.role === o, cfg.owner));
  ok("version line shows title and build", await page.evaluate(c => document.getElementById("appver").textContent === `${c.appTitle} · version ${c.build}`, cfg));
  const ownerName = P.find(p => p.id === cfg.owner).name;

  await page.evaluate(async (who, role) => { await runSave({ list: "shopping", batchId: "T-SHOP-1", person: who, role, note: "", adds: [{ item: "Milk", notes: "2%", addedBy: who, tempId: "t1" }], removes: [] }); }, ownerName, cfg.owner);
  let rows = await page.evaluate((id, t) => __emu.tab(id, t), S_.shopping, cfg.lists.shopping.tab);
  ok("grocery add writes the list row", rows.length === 2 && rows[1][0] === "Milk" && rows[1][3] === ownerName && /^SHOP-[0-9a-f-]{36}$/.test(rows[1][4]), JSON.stringify(rows));
  let log = await page.evaluate(id => __emu.tab(id, "Activity Log"), S_.shopping);
  ok("grocery add writes an Activity Log event", log.length === 2 && log[1][2] === "Add" && log[1][19] === rows[1][4] && /^EVT-/.test(log[1][20]), JSON.stringify(log[1]));
  await page.evaluate(async (who, role) => { await runSave({ list: "extra", batchId: "T-X-1", person: who, role, note: "", adds: [{ item: "Furnace filter", notes: "", addedBy: who, tempId: "t2" }], removes: [] }); }, ownerName, cfg.owner);
  rows = await page.evaluate((id, t) => __emu.tab(id, t), S_.shopping, cfg.lists.extra.tab);
  ok("second list add uses its own tab and prefix", rows.length === 2 && /^STORE2-/.test(rows[1][4]), JSON.stringify(rows));
  const uid = rows[1][4];
  await page.evaluate(async (who, role, uid) => { await runSave({ list: "extra", batchId: "T-X-2", person: who, role, note: "bought", adds: [], removes: [{ key: uid, seen: { a: "Furnace filter", b: __emu.tab(DT.sheets.shopping, DT.lists.extra.tab)[1][1], c: "", d: who } }] }); }, ownerName, cfg.owner, uid);
  rows = await page.evaluate((id, t) => __emu.tab(id, t), S_.shopping, cfg.lists.extra.tab);
  const hist = await page.evaluate(id => __emu.tab(id, "History"), S_.shopping);
  ok("removing an item deletes the row and writes History", rows.length === 1 && hist.length === 2 && hist[1][11] === uid, JSON.stringify([rows, hist]));

  const put = (coll, id, doc) => page.evaluate((c, i, d) => dbWrite(c + "/" + i, "set", d), coll, id, doc);
  await put("fzQueue", "add-a1", { op: "add", id: "a1", ids: ["1"], by: cfg.owner, at: Date.now(), f: { item: "Chicken thighs", pickday: "Yes", label: "01/05/2030", qty: "1", unit: "package", weight: "2", loc: cfg.freezerLocations[0], dtype: "freezer_date", prep: "raw", notes: "" } });
  ok("freezer add reaches Inventory", await waitFor(page, id => __emu.tab(id, "Inventory").length === 2, S_.freezer));
  let inv = await page.evaluate(id => __emu.tab(id, "Inventory"), S_.freezer), cl = await page.evaluate(id => __emu.tab(id, "Change Log"), S_.freezer);
  ok("freezer add row is complete and credited to the person", inv[1][0] === "1" && inv[1][1] === "Chicken thighs" && inv[1][3] === "In freezer" && inv[1][4] === "01/05/2030" && inv[1][12] === ownerName && cl[1][2] === "Added" && cl[1][5] === ownerName, JSON.stringify([inv[1], cl[1]]));
  ok("freezer queue doc cleared", await waitFor(page, () => !Object.keys(__emu.docs).some(k => k.startsWith("fzQueue/"))));
  await put("fzQueue", "pull-THAW-20300106-080000", { op: "pull", id: "THAW-20300106-080000", by: cfg.owner, at: Date.now(), person: ownerName, pulls: [{ id: "1", item: "Chicken thighs", label: "01/05/2030" }] });
  ok("freezer pull writes Confirmed Withdrawals as pending", await waitFor(page, id => { const r = __emu.tab(id, "Confirmed Withdrawals"); return r.length === 2 && r[1][0] === "THAW-20300106-080000" && r[1][8] === "pending" && __emu.tab(id, "Inventory")[1][3] === "Removed to thaw"; }, S_.freezer));

  await put("rxEditQueue", "ab12cd34", { op: "create", id: "ab12cd34", name: "Test Tacos", text: "1 lb beef\n1. Brown the beef.", cats: ["Beef"], by: cfg.owner, at: Date.now() });
  ok("recipe create writes Recipes and RecipeCategories", await waitFor(page, id => { const r = __emu.tab(id, "Recipes"), l = __emu.tab(id, "RecipeCategories"); return r.length === 2 && r[1][0] === "ab12cd34" && r[1][1] === "Test Tacos" && l.length === 2 && l[1][0] === "ab12cd34_Beef"; }, S_.recipes));
  ok("category seeds are present", await page.evaluate(id => __emu.tab(id, "Categories").length > 10 && __emu.tab(id, "Categories")[1][0] === "Beef", S_.recipes));
  await put("rxRateQueue", "r1", { id: "ab12cd34", role: cfg.owner, stars: 5, note: "great", at: Date.now() });
  ok("rating writes one Ratings row with a number", await waitFor(page, id => { const r = __emu.tab(id, "Ratings"); return r.length === 2 && r[1][3] === "5"; }, S_.recipes));
  const rat = await page.evaluate(id => __emu.tab(id, "Ratings"), S_.recipes);
  ok("rating id uses the person id", rat.length === 2 && rat[1][0] === "RATE-ab12cd34-" + cfg.owner && rat[1][2] === ownerName, JSON.stringify(rat));

  const today = await page.evaluate(() => { const p = new Intl.DateTimeFormat("en-CA", { timeZone: TZ }).format(new Date()); return p; });
  await put("menuQueue", "m1", { op: "add", mid: "M-" + today + "-abcde", date: today, role: "Main", src: "Recipe", rid: "ab12cd34", name: "Test Tacos", by: cfg.owner, at: Date.now() });
  ok("menu add writes Menu and Menu Log", await waitFor(page, id => { const m = __emu.tab(id, "Menu"), l = __emu.tab(id, "Menu Log"); return m.length === 2 && m[1][6] === "Test Tacos" && m[1][8] === "App" && l.length === 2 && l[1][3] === "Added"; }, S_.recipes));

  await put("gearQueue", "gsave-9f8e7d6c", { op: "gsave", id: "9f8e7d6c", gearId: "9f8e7d6c", typeId: "Appliance", name: "Dishwasher", make: "Acme", model: "D1", year: "2029", vin: "", pdate: "", price: "", notes: "", parts: "", by: cfg.owner, at: Date.now() });
  ok("gear save writes the Gear row", await waitFor(page, id => { const g = __emu.tab(id, "Gear"); return g.length === 2 && g[1][0] === "9f8e7d6c" && g[1][2] === "Dishwasher" && g[1][5] === "2029"; }, S_.gear));
  await put("gearQueue", "log-1a2b3c4d", { op: "log", id: "1a2b3c4d", gearId: "9f8e7d6c", date: "01/06/2030", reading: "", work: "Cleaned the filter", tasks: ["filter"], notes: "", doneRem: [], newRem: null, by: cfg.owner, at: Date.now() });
  ok("maintenance log writes the Maintenance row", await waitFor(page, id => { const g = __emu.tab(id, "Maintenance"); return g.length === 2 && g[1][2] === "Cleaned the filter"; }, S_.gear));

  // bug report through the real button
  ok("bug report button is on the page", await waitFor(page, () => !!document.querySelector("#bugHost .dt-bug-btn")));
  ok("bug report link points at this household's bug sheet", await page.evaluate(id => { const a = document.querySelector("#bugHost a"); return a && a.href === "https://docs.google.com/spreadsheets/d/" + id + "/edit"; }, S_.bugs));
  await page.click("#bugHost .dt-bug-btn"); await page.type("#bugHost textarea", "The freezer count looks wrong. Second sentence."); await page.click("#bugHost .dt-bug-send");
  ok("bug report writes BUG-001 to the Bugs tab", await waitFor(page, id => { const b = __emu.tab(id, "Bugs"); return b.length === 2 && b[1][0] === "BUG-001" && b[1][3] === "App page: Home" && b[1][4] === "The freezer count looks wrong." && b[1][9] === "Open"; }, S_.bugs), await page.evaluate(id => JSON.stringify(__emu.tab(id, "Bugs")), S_.bugs));
  const bug = (await page.evaluate(id => __emu.tab(id, "Bugs"), S_.bugs))[1] || [];
  ok("bug row names the reporter and has 12 columns", bug[2] === ownerName && bug.length === 12 && /^\d\d\/\d\d\/\d{4}$/.test(bug[1]), JSON.stringify(bug));
  ok("still no page errors after every write", errors.length === 0, errors.join(" | "));
  const allowed = ["fonts.googleapis.com", "fonts.gstatic.com", "cdnjs.cloudflare.com", "cdn.jsdelivr.net"];
  ok("only allowed outside hosts are requested", [...hosts].every(h => allowed.includes(h)), [...hosts].join(","));
  for (const v of ["home", "shopping", "extra", "freezer", "recipes", "menu", "gear"]) {
    await page.evaluate(x => go(x), v); await sleep(250);
    const over = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    ok(`page ${v}: no sideways scroll at 390px`, over <= 1, "overflow " + over);
  }
  ok("no page errors after visiting every page", errors.length === 0, errors.join(" | "));
  const text = await page.evaluate(() => document.documentElement.outerHTML);
  const hit = deny.filter(t => text.toLowerCase().includes(t.toLowerCase()));
  ok("rendered pages contain no denylisted term", hit.length === 0, hit.length + " term(s)");
  await page.close();

  // 2. a second person without the Sheets connector: welcome, then queueing
  ({ page, errors, hosts } = await open(browser, { runtime: true, mcp: false, owner: false, uid: "u-two" }));
  ok("loads with no page errors (no connector)", errors.length === 0, errors.join(" | "));
  const btns = await waitFor(page, () => { const b = [...document.querySelectorAll("[data-wpick]")].map(x => x.textContent); return b.length ? b : null; });
  ok("welcome asks who this is, with the settings' names", !!btns && btns.every(n => P.some(p => p.name === n)), JSON.stringify(btns));
  if (btns) { await page.click("[data-wpick]"); await sleep(400); }
  ok("picking a person sets the role", await page.evaluate(() => !!S.role && !!PERSON[S.role]));
  await page.click("#bugHost .dt-bug-btn"); await page.type("#bugHost textarea", "Queued note"); await page.click("#bugHost .dt-bug-send");
  ok("without the connector a bug note waits in bugQueue", await waitFor(page, () => { const k = Object.keys(__emu.docs).find(x => x.startsWith("bugQueue/")); return k && __emu.docs[k].row[0] === "" && __emu.docs[k].row.length === 12 && __emu.docs[k].row[5] === "Queued note"; }));
  ok("no page errors (no connector)", errors.length === 0, errors.join(" | "));
  await page.close();

  // 3. opened as a plain file with no Claude runtime
  ({ page, errors, hosts } = await open(browser, { runtime: false }));
  ok("opens as a plain file with no errors", errors.length === 0, errors.join(" | "));
  ok("plain file shows the version line", await page.evaluate(() => /version/.test(document.getElementById("appver").textContent)));
  await page.close();
  await browser.close();
  console.log(results.join("\n")); console.log(`\n${results.length - failed}/${results.length} passed`);
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error("HARNESS ERROR", e); process.exit(2); });
