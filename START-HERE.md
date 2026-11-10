# START HERE: install Dinner Time! for a household

You are an AI agent installing a complete system into **this person's own** Google Drive and AI accounts. Build only from the files in this kit and the person's answers. The kit holds no real household's data; never invent names, preferences, inventory or recipes for them.

Work through the phases in order. Keep a task list. Never report a step done without reading its result back. Paths are relative to this kit folder.

## What gets built

| Piece | Where |
|---|---|
| A folder (default name **Dinner Time**) with 5 spreadsheets: 01 Shopping List, 02 Freezer Inventory, 03 Recipes and Menu, 04 Gear and Maintenance, 05 Bug Report | their Google Drive |
| Folders 20 Recipe Images, 21 Gear Images, 22 Gear Files, 23 Maintenance Images, 29 Site Files, 30 App Changes (with 31 Inbox, 32 Applied, 33 Held, 34 Drafts), 90 Setup Records | same folder |
| Docs: 00 Agent Rules, one Recipe Preferences doc per person, Pantry Staples, 19 Site Guide, 30 App Change Rules | same folder |
| The **app**, a private Claude artifact | their Claude account |
| A scheduled **refresh** task | their Claude account |
| The **dinner-time-data** skill for Claude, and Project instructions for ChatGPT if they use it | their AI accounts |

## Phase 0: tell them how it works (one short message)

- It builds everything in their own Google Drive and Claude account, takes about 15 minutes, and asks a handful of questions.
- Everything runs on their own AI plan: every request, every set of freezer recipe ideas and each scheduled refresh counts toward their usage. The refresh can be made less frequent or turned off.
- At the end they pick a home photo and fill in their recipe preferences and pantry staples.

## Phase 1: check your tools

You need, in this session: Google Drive tools (create files and folders, read, move), Google Sheets tools (read values, read spreadsheet metadata, batch update), a way to publish an HTML page as a Claude artifact and declare its capabilities, and a way to create a scheduled task. If a connector is missing, say which one and wait. If you cannot publish artifacts or schedule tasks from here, do every other phase and give the person the exact files and steps for those two.

## Phase 2: interview → `settings.json`

Copy `settings.example.json` to `settings.json` in your working folder and replace every example value with the person's answers. Ask; never guess.

1. Who is in the household (1 to 6 first names)? What should greetings call it (for example "the Rivera household")? Who owns and publishes the app (normally the person you're talking to)? Give each person a lowercase `id` (their first name without spaces) and a color from: navy, turquoise, coral, violet, gold, green.
2. The Google account email of each household member who may hand in app changes (`trusted_accounts`). This stays in their own scheduled task; it is never shared.
3. Time zone as an IANA name (confirm from their city), plus its standard and daylight labels in the form `EST (UTC-05:00)` / `EDT (UTC-04:00)`.
4. The two list names (defaults: Grocery, Hardware). The second list is for another store they shop at regularly.
5. Optional cook chart (who usually cooks which weekday; `{}` if none) and optional pick day (a weekday when the app suggests the oldest proteins; `""` if none). Freezer locations (defaults: Kitchen freezer, Chest freezer).
6. Which assistants will edit the data (`agents`, for example `["Claude"]` or `["Claude", "ChatGPT"]`).
7. Refresh: `hourly` (default), `every 3 hours` or `off`. Explain that it keeps phones without the Google Sheets connector in sync and runs on the owner's plan.

Set `install_date` to today. Leave every value under `ids` empty for now. Then:

```
python3 tools/dinnertime_kit.py validate settings.json
python3 tools/dinnertime_kit.py plan settings.json build
```

Fix and re-ask anything `validate` reports. `build/manifest.json` now lists what to create. (No shell? Follow `backend/schema.json` and `docs/PLACEHOLDERS.md` by hand; the steps below are the same.)

## Phase 3: create the Drive layout

Ask where to put the folder (My Drive root unless they name a place). Record every ID in `settings.json` under `ids` as you go.

1. Create the root folder → `ids.root_folder`.
2. Create each folder in `backend/schema.json` → `folders` (the four `children` go inside 30 App Changes) → `ids.folders.<key>`.
3. For each of the five spreadsheets in the manifest: create an empty Google Sheet with that title in the root folder → `ids.sheets.<key>`. Then send one Sheets batch update with the `requests` from `build/sheet-requests/<key>.json` exactly as written (it renames the first tab, adds the others with fixed sheet IDs 1, 2, 3…, freezes and writes the bold header rows and the starter categories and gear types). If a call fails part-way, read the spreadsheet's tabs and continue from where it stopped; never create a second copy.
4. **Verify structure**: read row 1 of every tab and compare it, cell for cell, with `backend/schema.json`. Every tab and every header must match exactly before you go on.

## Phase 4: documents

Run `python3 tools/dinnertime_kit.py render settings.json build` before each step; it is safe to repeat and fills in whatever IDs you have so far.

1. Create each `build/docs/1N <Name> Recipe Preferences.md` and the `Pantry Staples.md` as Google Docs in the root folder (title = file name without `.md`) → `ids.docs.prefs.<person id>`, `ids.docs.pantry`. They are blank templates with italic examples; never write real preferences for anyone.
2. Render again. Create `30 App Change Rules – read first` as a Google Doc inside 30 App Changes → `ids.docs.changeRules`, and `_TEMPLATE CHANGE.md` as a plain text file inside 34 Drafts.
3. Render again. Create `00 Agent Rules – read first` as a Google Doc in the root folder → `ids.docs.rules`.
4. Render again. Write the guide tabs: for each entry in `build/guide-requests.json` send its `requests` as one batch update to that spreadsheet (How to Use in 01, Workflow in 02, Rules in 03).

## Phase 5: the app

1. Render. `build/app/dinner-time.html` is the tested app with this household's settings in its DT block. Publish it exactly as written: do not rewrite, restyle or shorten it. Title = the app title. Keep it private.
2. Declare the artifact's capabilities from `build/app/capabilities.json` exactly (shared database, user identity, a live room with the "cheer" topic, uploaded assets, and the viewer's Google Sheets `get_values` / `get_spreadsheet` / `update_spreadsheet` and Google Drive `create_file` / `download_file_content`).
3. Record the artifact link as `ids.app_url`. Confirm the app's database answers (list the `people` and `settings` collections; empty is fine).

## Phase 6: the scheduled refresh

Skip if `refresh` is `off`. Render, then create a scheduled task named "<app title> refresh" with the full text of `build/automation/refresh-task.md` as its prompt and the schedule in `build/automation/schedule.txt`, with the Google Sheets and Google Drive connectors and the artifact tools available to it. Tell the person which approval setting the task got; it needs to run without waiting for approval.

## Phase 7: assistant skills

Render (now with the app link).
- **Claude**: offer `build/skills/dinner-time-data/SKILL.md` as a new skill named `dinner-time-data` for each household member's Claude account.
- **ChatGPT** (if used): give them `build/skills/chatgpt-project-instructions.md`; its first section is the setup steps.
- Create `build/docs/19 Site Guide.md` as a Google Doc in the root folder → `ids.docs.guide`.

## Phase 8: verify and hand off

1. `python3 tools/dinnertime_kit.py check build` must print `files OK` (nothing unfilled).
2. Save into **90 Setup Records**, as plain text files: `settings.json`, the refresh prompt, the schedule, both skill files, and a copy of the published app file.
3. Live check: ask the person to open the app, allow Google Sheets and Google Drive when it asks, and add one test item to the first list. Read that tab and the Activity Log and confirm the row and its Add event; then have them remove it and confirm the History row. Ask them to send one note with the Bug Report button and confirm the row in 05 Bug Report.
4. If the refresh is on, after its first run confirm it succeeded.
5. Tell the person, briefly: the app link; the three first steps (home photo, recipe preferences, pantry staples); how to share (invite each person to the artifact as an Editor and share the Drive folder with them as an Editor; each person installs the skill in their own account); what to say to the assistant; and the usage note.

## Rules for you, the installer

- Build only what this runbook lists. Don't add features, restyle the app or change the sheet layout.
- Never put anything in the person's Drive outside the folder you created.
- If something in the kit seems wrong or a step can't be done with your tools, stop and tell the person rather than improvising.
- To change settings later: edit `settings.json` (saved in 90 Setup Records), render, republish the app to the **same** artifact, and update the rules doc, skills and refresh prompt together. Renaming a list also means renaming that tab in 01 Shopping List. Never change column order.
