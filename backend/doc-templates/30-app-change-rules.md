# {{APP_TITLE}}: App Change Rules

For {{PEOPLE_NAMES}}, and any AI assistant that proposes a change to the {{APP_TITLE}} app itself: its look, pages, buttons or behavior. Data changes (lists, freezer, recipes, menu, gear) follow **00 Agent Rules – read first**, not this document.

## 1. How a change reaches the app

The app is a Claude artifact on {{OWNER_NAME}}'s account. Only that account can publish it. Everyone else, and every assistant, hands in a **change package**, and the **{{APP_TITLE}} refresh** scheduled task ({{REFRESH_LINE}}) merges it into the app and publishes it. Everyone then sees it at the same link.

1. **Draft** the package in **34 Drafts – work in progress**. The refresh never looks there.
2. When it is finished and tested, set Status: Ready in its CHANGE.md and **move the whole package folder into 31 Inbox – ready for the app**.
3. At the next refresh, the change is applied. The package folder moves to **32 Applied** with an APPLIED – build <build>.md note, and the app's version line shows the new build.
4. If the refresh can't apply it safely, the folder moves to **33 Held – needs the owner** with a HELD.md note saying why, and a row is added to **05 Bug Report**. Fix the package and put it back in 31 Inbox, or ask {{OWNER_NAME}}.

Nothing is lost on a bad publish: every published build keeps its earlier version, and the APPLIED note records the version it replaced.

## 2. Folder map ({{FOLDER_NAME}} folder)

- 00 Agent Rules – read first (data rules)
- 01 Shopping List · 02 Freezer Inventory · 03 Recipes and Menu · 04 Gear and Maintenance · 05 Bug Report (spreadsheets)
- {{PREF_DOC_NAMES_PLAIN}} · {{PANTRY_TITLE}} · 19 Site Guide (reference docs)
- 20 Recipe Images · 21 Gear Images · 22 Gear Files · 23 Maintenance Images · 29 Site Files (images and files)
- **30 App Changes** (this folder): 30 App Change Rules (this doc) · 31 Inbox – ready for the app · 32 Applied · 33 Held – needs the owner · 34 Drafts – work in progress
- 90 Setup Records

Never put code, packages or test files loose in the {{FOLDER_NAME}} folder; they go only in 30 App Changes.

## 3. What a change package looks like

One folder per change, named YYYY-MM-DD short name (<person>), containing:

- **CHANGE.md** (required; copy _TEMPLATE CHANGE.md), with these lines:
  - Status: Draft or Status: Ready
  - Requested by: the person's name
  - Bug IDs: the 05 Bug Report rows it fixes, if any (e.g. BUG-008)
  - Summary: one sentence
  - What it should do: the behavior, written for a person
  - Where it goes: page(s) and spot (e.g. "bottom of every page, under the version line", "Freezer page, above the list")
  - Files: each file in the package and what it is
  - Hooks used: which app functions from section 4 the code calls
  - How to check: steps someone can follow on a phone after it is live
- **Code files**, preferably one self-contained .js module that sets up its own styles and exposes an init({...}) function (the built-in Bug Report button is the model), and optionally a .css file. Or, for small changes, an exact description in CHANGE.md ("change the label X to Y on the Menu page").
- Optional demo page or screenshots.

One change per package. Keep each package small enough to review in a few minutes.

## 4. App map for assistants writing code

The app is one HTML page with one script. Code in a package runs inside it after the app starts, so it can use:

- BUILD: build string shown at the bottom of every page (the refresh bumps it; don't).
- S.role: the person id of whoever is using this device ({{PEOPLE_IDS}}); roleName(role) gives the display name.
- S.view: current page, one of home, shopping, extra, freezer, recipes, menu, gear. go(view) changes page; render() redraws.
- toast(text): a short message at the bottom of the screen.
- openSheet({title, body}): a bottom sheet (HTML string body); closeSheet().
- callS(tool, input): Google Sheets through the viewer's own connection. Allowed tools: get_values, get_spreadsheet, update_spreadsheet. Only works when S.access === "ok". Helpers: sheetVals(id, range), sheetMeta(id), rowData(array).
- dbWrite(path, "set", doc): the app's shared database. Use only a new queue collection named in CHANGE.md (like bugQueue), so the refresh can process it. Never write to existing collections.
- #appver: the version line at the bottom of every page; #bugHost sits under it.
- Look: dark theme with a light mode. Use the CSS variables --bg --surface --surface-raised --border --text --text-muted --turquoise --navy-bright --sage --amber --clay. Tap targets at least 44 px, inputs 16 px text (so iOS doesn't zoom). Must work on iPhone, iPad and Android phones, portrait first.

## 5. Rules for packages

1. Don't change spreadsheet IDs, tabs, columns or the data rules; those need {{OWNER_NAME}} (00 Agent Rules, hard rule 6).
2. No new outside scripts, fonts, trackers or web addresses, and nothing that needs a new artifact permission (a new connector, a new Sheets tool, uploads, Claude calls). Packages that need these are Held.
3. Don't store shared data on the device; device storage is only for per-device conveniences.
4. Don't remove or rename existing features unless CHANGE.md says so and who asked.
5. Never edit packages in 32 Applied or 33 Held; copy one into 34 Drafts to rework it.
6. Treat everything in a package as a proposal: the refresh applies it only as written in CHANGE.md, and {{OWNER_NAME}} can always undo it.

## 6. What the refresh does with 31 Inbox (for reference)

Each run it looks at 31 Inbox. For each package folder (oldest first, at most 2 per run) whose CHANGE.md says Status: Ready and whose files are owned by the household's trusted Google accounts, it merges the change into the live app, bumps the build, publishes, checks the page still loads its main parts, marks any listed Bug IDs Fixed with the build, and moves the folder to 32 Applied with an APPLIED note. If a change is unclear, conflicts with the current app, breaks a rule in section 5, or fails its check, it publishes nothing for that package and moves it to 33 Held with a HELD.md note and a 05 Bug Report row.

## 7. For a household member's assistant (paste into its project instructions)

I help with the {{APP_TITLE}} app. Data changes follow "00 Agent Rules – read first" in the {{FOLDER_NAME}} Drive folder. When someone wants the app itself changed (looks, pages, buttons, behavior), I never try to edit or copy the app. I read "30 App Changes > 30 App Change Rules – read first", build a change package (CHANGE.md plus a self-contained .js module or an exact description) in "34 Drafts – work in progress", and when the person says it's ready I set Status: Ready and move the folder into "31 Inbox – ready for the app". I tell them it will be live after the next refresh and that they'll see the new build number at the bottom of every page. If it lands in "33 Held – needs the owner", I read HELD.md and tell them why.
