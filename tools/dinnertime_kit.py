#!/usr/bin/env python3
"""Dinner Time! handoff kit helper. Standard library only; reads and writes local files, never the network.

  python3 tools/dinnertime_kit.py validate settings.json
  python3 tools/dinnertime_kit.py plan     settings.json build     # sheet-creation requests + checklist
  python3 tools/dinnertime_kit.py render   settings.json build     # fill every template (repeat as IDs arrive)
  python3 tools/dinnertime_kit.py check    build                   # nothing unfilled is left

An agent without a shell can do the same by hand: every template uses {{NAME}} placeholders, listed in
docs/PLACEHOLDERS.md, and backend/schema.json gives the exact tabs and headers.
"""
import json, os, re, sys

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIT_VERSION = "2.0.0"
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
COLORS = ["navy", "turquoise", "coral", "violet", "gold", "green"]
ID_RE = re.compile(r"^[A-Za-z0-9_-]{20,}$")


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def read(rel):
    with open(os.path.join(KIT, rel), encoding="utf-8") as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def join_names(names):
    names = list(names)
    if len(names) <= 1:
        return "".join(names)
    return ", ".join(names[:-1]) + " and " + names[-1]


def tag_of(name):
    return "For" + re.sub(r"[^A-Za-z0-9]", "", name)


def validate(s):
    errs = []
    people = s.get("people") or []
    if not 1 <= len(people) <= 6:
        errs.append("people: list 1 to 6 people")
    ids = [p.get("id", "") for p in people]
    for p in people:
        if not re.fullmatch(r"[a-z][a-z0-9]{0,15}", p.get("id", "")):
            errs.append(f"people: id {p.get('id')!r} must be lowercase letters/digits, starting with a letter")
        if not p.get("name"):
            errs.append("people: every person needs a name")
        if p.get("color") not in COLORS:
            errs.append(f"people: color for {p.get('name')} must be one of {COLORS}")
    if len(set(ids)) != len(ids):
        errs.append("people: ids must be unique")
    if len({tag_of(p.get("name", "")) for p in people}) != len(people):
        errs.append("people: names must differ once punctuation and spaces are removed")
    if s.get("owner") not in ids:
        errs.append("owner: must be one of the people ids")
    for day, who in (s.get("cook") or {}).items():
        if day not in DAYS:
            errs.append(f"cook: {day!r} is not a weekday name")
        for w in who:
            if w not in ids:
                errs.append(f"cook: {w!r} on {day} is not a person id")
    if s.get("pick_day") and s["pick_day"] not in DAYS:
        errs.append("pick_day: a weekday name or empty")
    lists = s.get("lists") or {}
    for k in ("grocery", "extra"):
        v = lists.get(k, "")
        if not v or re.search(r"[\[\]\*\?:/\\']", v) or len(v) > 40:
            errs.append(f"lists.{k}: a short tab name without [ ] * ? : / \\ '")
    if lists.get("grocery") == lists.get("extra"):
        errs.append("lists: the two list names must differ")
    reserved = {"History", "Activity Log", "How to Use"}
    if set(lists.values()) & reserved:
        errs.append(f"lists: names can't be {sorted(reserved)}")
    if not re.fullmatch(r"[A-Za-z_]+/[A-Za-z_+\-/]+", s.get("time_zone", "")):
        errs.append("time_zone: an IANA name such as America/New_York")
    for k in ("tz_standard", "tz_daylight"):
        if not re.fullmatch(r"[A-Z0-9+\-]{2,6} \(UTC[+-]\d\d:\d\d\)", s.get(k, "")):
            errs.append(f"{k}: like 'EST (UTC-05:00)' (use the same value for both if the zone has no daylight time)")
    if s.get("refresh") not in ("hourly", "every 3 hours", "off"):
        errs.append("refresh: hourly, every 3 hours or off")
    if not re.fullmatch(r"\d{4}-\d\d-\d\d", s.get("install_date", "")):
        errs.append("install_date: YYYY-MM-DD")
    for k in ("app_title", "household", "folder_name"):
        if not s.get(k):
            errs.append(f"{k}: required")
    if not s.get("agents"):
        errs.append("agents: at least one assistant name")
    if not s.get("trusted_accounts"):
        errs.append("trusted_accounts: the Google account emails of the household members who may hand in app changes")
    if not s.get("freezer_locations"):
        errs.append("freezer_locations: at least one")
    return errs


def cell(v, bold=False):
    c = {"userEnteredValue": {"stringValue": str(v)}}
    if bold:
        c["userEnteredFormat"] = {"textFormat": {"bold": True}}
    return c


def tab_names(s, schema):
    """{spreadsheet key: [tab name, ...]} with the two list names filled in."""
    out = {}
    for sp in schema["spreadsheets"]:
        out[sp["key"]] = [t["name"].replace("{{GROCERY_TAB}}", s["lists"]["grocery"]).replace("{{EXTRA_TAB}}", s["lists"]["extra"]) for t in sp["tabs"]]
    return out


def sheet_requests(s, schema):
    """Sheets batchUpdate requests for each brand-new spreadsheet (whose only tab has sheetId 0)."""
    names = tab_names(s, schema)
    out = {}
    for sp in schema["spreadsheets"]:
        reqs = []
        for i, t in enumerate(sp["tabs"]):
            props = {"sheetId": i, "title": names[sp["key"]][i], "gridProperties": {"frozenRowCount": 1}}
            if i == 0:
                reqs.append({"updateSheetProperties": {"properties": props, "fields": "title,gridProperties.frozenRowCount"}})
            else:
                reqs.append({"addSheet": {"properties": props}})
        for i, t in enumerate(sp["tabs"]):
            rows = [{"values": [cell(h, True) for h in t["headers"]]}]
            for v in schema["seeds"].get(t.get("seed", ""), []):
                rows.append({"values": [cell(v), cell(v)]})
            reqs.append({"updateCells": {"start": {"sheetId": i, "rowIndex": 0, "columnIndex": 0}, "rows": rows,
                                         "fields": "userEnteredValue,userEnteredFormat.textFormat.bold"}})
        out[sp["key"]] = reqs
    return out


def idv(s, *path):
    cur = s.get("ids", {})
    for p in path:
        cur = cur.get(p, "") if isinstance(cur, dict) else ""
    return cur if isinstance(cur, str) and ID_RE.match(cur) else ""


def placeholders(s):
    people = s["people"]
    names = [p["name"] for p in people]
    by_id = {p["id"]: p["name"] for p in people}
    g, x = s["lists"]["grocery"], s["lists"]["extra"]
    n_ideas = len(people) + 2
    pref_titles = {p["id"]: f"{10 + i} {p['name']} Recipe Preferences" for i, p in enumerate(people)}
    pantry_title = f"{10 + len(people)} Pantry Staples"
    P = lambda v, name: v or f"PENDING_{name}"
    pref_ids = {p["id"]: P(idv(s, "docs", "prefs", p["id"]), "PREFS_DOC_ID_" + p["id"].upper()) for p in people}
    cook = s.get("cook") or {}
    if cook:
        parts = []
        for d in DAYS:
            who = cook.get(d) or []
            if who:
                parts.append(f"{d[:3]} {'everyone' if len(who) == len(people) and len(people) > 1 else join_names(by_id[w] for w in who)}")
        cook_line = "Whose night (favor the cook's preferences): " + " · ".join(parts) + "."
        cook_guide = "Each night shows whose turn it is to cook: " + " · ".join(parts) + "."
    else:
        cook_line = "No cook chart is set; consider everyone's preferences equally."
        cook_guide = "No cook chart is set for this household."
    pick = s.get("pick_day") or ""
    if pick:
        pick_rule = f"{pick} suggestions (the four oldest packages marked Pick-day protein = Yes) are suggestions only; they change nothing."
        pick_guide = f"Pick-day protein = Yes marks proteins the app may suggest on {pick}s (the four oldest). Use No for sides and anything that shouldn't be suggested, Review when unsure."
        pick_page = f"- On {pick}s the top card suggests the four oldest pick-day proteins."
    else:
        pick_rule = "This household has no pick day; set Pick-day protein to No unless told otherwise."
        pick_guide = "This household has no pick day. Set Pick-day protein to No unless told otherwise."
        pick_page = "- The top card suggests the oldest items to use first."
    idea_rows = ["   | Category (C) | Recipe option ID ends | What it is | Source (N) |", "   |---|---|---|---|",
                 "   | `Our Recipes` | `-OurRecipes` | Adapt the best-matching recipe already saved in Recipes to this protein; say what changed in Adaptation notes (O). | `<RecipeID> — <RecipeName>`; only if nothing fits, a close new substitute with `New substitute — no Our Recipes source found` |"]
    person_lines = []
    for p in people:
        idea_rows.append(f"   | `For {p['name']}` | `-{tag_of(p['name'])}` | Built on {pref_titles[p['id']]}. | `New recipe` |")
        person_lines.append(f"   - {tag_of(p['name'])} (Category \"For {p['name']}\"): built around the doc \"{pref_titles[p['id']]}\". N = \"New recipe\"; O = how it fits {p['name']}.")
    idea_rows.append("   | `Adventure` | `-Adventure` | The wildcard: a different cuisine or technique from the others and from earlier ideas for the same protein, still something everyone would eat. | `New recipe` |")
    tags = ["OurRecipes"] + [tag_of(n) for n in names] + ["Adventure"]
    cats = ["Our Recipes"] + [f"For {n}" for n in names] + ["Adventure"]
    refresh = s["refresh"]
    refresh_line = {"hourly": "runs at :02 past each hour", "every 3 hours": "runs at :02 past every third hour", "off": "currently turned off; changes sync when someone with the Google Sheets connector opens the app"}[refresh]
    sync_line = {"hourly": "the scheduled refresh (hourly, at :02) writes them to the sheets.", "every 3 hours": "the scheduled refresh (every 3 hours) writes them to the sheets.",
                 "off": "they are written the next time someone with the Google Sheets connector opens the app (the scheduled refresh is off)."}[refresh]
    usage = "The scheduled refresh also runs on the app owner's Claude plan each time it fires; it can be made less frequent or turned off." if refresh != "off" else "The scheduled refresh is off, so nothing runs in the background."
    off = re.search(r"\(UTC([+-]\d\d:\d\d)\)", s["tz_standard"]).group(1)
    d = {
        "KIT_VERSION": KIT_VERSION, "APP_TITLE": s["app_title"], "HOUSEHOLD": s["household"], "FOLDER_NAME": s["folder_name"],
        "TZ": s["time_zone"], "TZ_STD": s["tz_standard"], "TZ_DST": s["tz_daylight"], "TZ_STD_OFFSET": off,
        "PEOPLE_NAMES": join_names(names), "PEOPLE_IDS": ", ".join(p["id"] for p in people), "OWNER_NAME": by_id[s["owner"]],
        "ROLE_NAME_MAP": ", ".join(f'person id "{p["id"]}" = "{p["name"]}"' for p in people),
        "GROCERY_TAB": g, "EXTRA_TAB": x, "AGENTS": join_names(s["agents"]), "INSTALL_DATE": s["install_date"],
        "FREEZER_LOCATIONS": ", ".join(s["freezer_locations"]), "AISLES": ", ".join(s["aisles"]),
        "COOK_LINE": cook_line, "COOK_GUIDE_LINE": cook_guide, "PICK_DAY_RULE": pick_rule, "PICK_DAY_GUIDE": pick_guide, "PICK_DAY_GUIDE_LINE": pick_page,
        "IDEA_COUNT": str(n_ideas), "IDEA_TABLE": "\n".join(idea_rows), "IDEA_PERSON_LINES": "\n".join(person_lines),
        "IDEA_TAGS": ", ".join(tags), "IDEA_CATEGORIES": ", ".join(cats),
        "ARCHIVE_LINE": ("After 3 a.m. the scheduled refresh moves past nights from Menu to Menu Archive (Outcome 'Not marked' if blank) and logs it. Assistants never archive or delete past nights."
                         if refresh != "off" else "The scheduled refresh is off, so past nights stay in Menu until someone asks for them to be archived: append them to Menu Archive (Outcome 'Not marked' if blank), log it, then delete them from Menu."),
        "REFRESH_LINE": refresh_line, "SYNC_LINE": sync_line, "REFRESH_USAGE_LINE": usage,
        "TRUSTED_ACCOUNTS": ", ".join(s["trusted_accounts"]),
        "PANTRY_TITLE": pantry_title,
        "PREF_DOC_NAMES": ", ".join(f"**{pref_titles[p['id']]}**" for p in people),
        "PREF_DOC_NAMES_PLAIN": " · ".join(pref_titles[p["id"]] for p in people),
        "PREF_DOC_LINES": "\n".join(f"- {pref_titles[p['id']]} `{pref_ids[p['id']]}`" for p in people),
        "PREF_DOCS_INLINE": " · ".join(f"\"{pref_titles[p['id']]}\" ({pref_ids[p['id']]})" for p in people),
        "ROOT_FOLDER_ID": P(idv(s, "root_folder"), "ROOT_FOLDER_ID"),
        "SHOPPING_ID": P(idv(s, "sheets", "shopping"), "SHOPPING_ID"), "FREEZER_ID": P(idv(s, "sheets", "freezer"), "FREEZER_ID"),
        "RECIPES_ID": P(idv(s, "sheets", "recipes"), "RECIPES_ID"), "GEAR_ID": P(idv(s, "sheets", "gear"), "GEAR_ID"), "BUGS_ID": P(idv(s, "sheets", "bugs"), "BUGS_ID"),
        "RECIPE_IMAGES_ID": P(idv(s, "folders", "recipeImages"), "RECIPE_IMAGES_ID"), "GEAR_IMAGES_ID": P(idv(s, "folders", "gearImages"), "GEAR_IMAGES_ID"),
        "GEAR_FILES_ID": P(idv(s, "folders", "gearFiles"), "GEAR_FILES_ID"), "MAINT_IMAGES_ID": P(idv(s, "folders", "maintImages"), "MAINT_IMAGES_ID"),
        "SITE_FILES_ID": P(idv(s, "folders", "siteFiles"), "SITE_FILES_ID"), "APP_CHANGES_ID": P(idv(s, "folders", "appChanges"), "APP_CHANGES_ID"),
        "INBOX_ID": P(idv(s, "folders", "inbox"), "INBOX_ID"), "APPLIED_ID": P(idv(s, "folders", "applied"), "APPLIED_ID"),
        "HELD_ID": P(idv(s, "folders", "held"), "HELD_ID"), "DRAFTS_ID": P(idv(s, "folders", "drafts"), "DRAFTS_ID"),
        "RULES_DOC_ID": P(idv(s, "docs", "rules"), "RULES_DOC_ID"), "PANTRY_DOC_ID": P(idv(s, "docs", "pantry"), "PANTRY_DOC_ID"),
        "GUIDE_DOC_ID": P(idv(s, "docs", "guide"), "GUIDE_DOC_ID"), "CHANGE_RULES_DOC_ID": P(idv(s, "docs", "changeRules"), "CHANGE_RULES_DOC_ID"),
        "APP_URL": s.get("ids", {}).get("app_url") or "PENDING_APP_URL",
    }
    return d, pref_titles, pantry_title


def fill(text, d, extra=None):
    m = dict(d)
    m.update(extra or {})
    def rep(mo):
        k = mo.group(1)
        if k not in m:
            raise SystemExit(f"unknown placeholder {{{{{k}}}}}")
        return m[k]
    return re.sub(r"\{\{([A-Z0-9_]+)\}\}", rep, text)


def app_config(s):
    sid = lambda *p: idv(s, *p) or "PENDING"
    return {
        "appTitle": s["app_title"], "household": s["household"], "tz": s["time_zone"],
        "people": [{"id": p["id"], "name": p["name"], "color": p["color"]} for p in s["people"]],
        "owner": s["owner"], "cook": s.get("cook") or {}, "pickDay": s.get("pick_day") or "",
        "lists": {"shopping": {"tab": s["lists"]["grocery"], "nav": s["lists"]["grocery"]}, "extra": {"tab": s["lists"]["extra"], "nav": s["lists"]["extra"]}},
        "sheets": {k: sid("sheets", k) for k in ("shopping", "freezer", "recipes", "gear", "bugs")},
        "folders": {k: sid("folders", k) for k in ("recipeImages", "gearImages", "gearFiles", "maintImages", "siteFiles")},
        "freezerLocations": s["freezer_locations"], "aisles": s["aisles"],
        "bridge": {"url": "", "key": ""}, "build": s["install_date"] + ".1",
    }


def cmd_plan(s, out):
    schema = load(os.path.join(KIT, "backend/schema.json"))
    for key, reqs in sheet_requests(s, schema).items():
        write(os.path.join(out, "sheet-requests", key + ".json"), json.dumps({"requests": reqs}, ensure_ascii=False))
    d, pref_titles, pantry_title = placeholders(s)
    names = tab_names(s, schema)
    manifest = {
        "root_folder": s["folder_name"],
        "folders": schema["folders"],
        "spreadsheets": [{"key": sp["key"], "title": sp["title"], "tabs": names[sp["key"]], "requests_file": f"sheet-requests/{sp['key']}.json"} for sp in schema["spreadsheets"]],
        "docs": [{"key": "prefs." + pid, "title": t} for pid, t in pref_titles.items()] + [{"key": "pantry", "title": pantry_title},
                 {"key": "rules", "title": "00 Agent Rules – read first"}, {"key": "guide", "title": "19 Site Guide"},
                 {"key": "changeRules", "title": "30 App Change Rules – read first", "parent": "appChanges"}],
    }
    write(os.path.join(out, "manifest.json"), json.dumps(manifest, indent=2, ensure_ascii=False))
    print("plan written to", out)


def cmd_render(s, out):
    schema = load(os.path.join(KIT, "backend/schema.json"))
    d, pref_titles, pantry_title = placeholders(s)
    T = "backend/doc-templates/"
    rules = fill(read(T + "00-agent-rules.md"), d)
    write(os.path.join(out, "docs", "00 Agent Rules – read first.md"), rules)
    for p in s["people"]:
        write(os.path.join(out, "docs", pref_titles[p["id"]] + ".md"), fill(read(T + "recipe-preferences.md"), d, {"PERSON_NAME": p["name"]}))
    write(os.path.join(out, "docs", pantry_title + ".md"), fill(read(T + "pantry-staples.md"), d))
    write(os.path.join(out, "docs", "19 Site Guide.md"), fill(read(T + "19-site-guide.md"), d))
    write(os.path.join(out, "docs", "30 App Change Rules – read first.md"), fill(read(T + "30-app-change-rules.md"), d))
    write(os.path.join(out, "docs", "_TEMPLATE CHANGE.md"), read("app-changes/_TEMPLATE CHANGE.md"))
    body = rules.split("\n", 1)[1].lstrip("\n")
    write(os.path.join(out, "skills", "dinner-time-data", "SKILL.md"), fill(read("skills/dinner-time-data/SKILL.header.md"), d) + body)
    write(os.path.join(out, "skills", "chatgpt-project-instructions.md"), fill(read("skills/chatgpt-project-instructions.md"), d))
    write(os.path.join(out, "automation", "refresh-task.md"), fill(read("automation/refresh-task.md"), d))
    guides = json.loads(fill(read("backend/sheet-guides.json"), {k: json.dumps(v, ensure_ascii=False)[1:-1] for k, v in d.items()}))
    reqs = {}
    for sp in schema["spreadsheets"]:
        for i, t in enumerate(sp["tabs"]):
            if t.get("guide"):
                reqs[sp["key"]] = {"tab": t["name"], "requests": [{"updateCells": {"start": {"sheetId": i, "rowIndex": 1, "columnIndex": 0},
                                   "rows": [{"values": [cell(a), cell(b)]} for a, b in guides[t["guide"]]], "fields": "userEnteredValue"}}]}
    write(os.path.join(out, "guide-requests.json"), json.dumps(reqs, ensure_ascii=False))
    html = read("app/dinner-time.html")
    a = html.index("/*DT_CONFIG_START*/") + len("/*DT_CONFIG_START*/")
    b = html.index("/*DT_CONFIG_END*/")
    html = html[:a] + json.dumps(app_config(s), indent=2, ensure_ascii=False) + html[b:]
    write(os.path.join(out, "app", "dinner-time.html"), html)
    write(os.path.join(out, "app", "capabilities.json"), read("app/capabilities.json"))
    cron = {"hourly": "2 * * * *", "every 3 hours": "2 */3 * * *", "off": ""}[s["refresh"]]
    write(os.path.join(out, "automation", "schedule.txt"), (f"CRON_TZ={s['time_zone']} {cron}\n" if cron else "off\n"))
    print("rendered to", out)


def cmd_check(out):
    bad = []
    for root, _, files in os.walk(out):
        for fn in files:
            p = os.path.join(root, fn)
            t = open(p, encoding="utf-8", errors="replace").read()
            for pat, why in ((r"\{\{[A-Z0-9_]+\}\}", "unfilled placeholder"), (r"PENDING(_[A-Z0-9_]+)?", "ID not filled in yet"), (r"PASTE_[A-Z_]+", "template ID")):
                hits = sorted(set(m.group(0) for m in re.finditer(pat, t)))
                if hits:
                    bad.append(f"{os.path.relpath(p, out)}: {why}: {', '.join(hits[:6])}")
    if bad:
        print("\n".join(bad))
        raise SystemExit(f"{len(bad)} file(s) not ready")
    print("files OK")


def main(argv):
    if len(argv) < 3 or argv[1] not in ("validate", "plan", "render", "check"):
        raise SystemExit(__doc__)
    if argv[1] == "check":
        return cmd_check(argv[2])
    s = load(argv[2])
    errs = validate(s)
    if errs:
        print("\n".join(errs))
        raise SystemExit("settings need fixing")
    if argv[1] == "validate":
        print("settings OK")
    elif argv[1] == "plan":
        cmd_plan(s, argv[3])
    else:
        cmd_render(s, argv[3])


if __name__ == "__main__":
    main(sys.argv)
