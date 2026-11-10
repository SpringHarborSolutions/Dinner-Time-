# Dinner Time! handoff kit (v2.0.0)

Everything an AI agent needs to build a complete **Dinner Time!** household system for a new household, in that household's own Google Drive and AI accounts:

- a phone-and-tablet **app** (a private Claude artifact) for shopping lists, freezer inventory, recipes and ratings, a 7-night menu, gear and maintenance, and bug reports
- the **Google Drive backend**: five spreadsheets, reference docs, image folders and an app-change pipeline
- **skills** so Claude and ChatGPT can keep the data up to date by voice or chat, under one shared rulebook
- a **scheduled automation** that syncs app changes to the sheets, writes recipe ideas for freezer pulls, archives past menu nights and installs approved app changes
- **documentation** for the household and for the agents

## How to use it

Give this whole folder to your AI agent and say: *"Read START-HERE.md and set up Dinner Time! for my household."* It will ask a few questions, then build everything in your accounts. Nothing is shared with, or copied from, anyone else's system.

You need: a Claude account that can publish artifacts and run scheduled tasks, with the Google Drive and Google Sheets connectors turned on. ChatGPT is optional (it can edit the data through its own Google Drive connector).

Everything runs on your own AI plan: each chat request, each set of recipe ideas and each scheduled refresh counts toward your usage like any other chat.

## What's inside

| Path | What it is |
|---|---|
| `START-HERE.md` | The step-by-step runbook for the installing agent |
| `settings.example.json` | The settings the agent fills in from its interview (made-up example values) |
| `app/dinner-time.html` | The app. One self-contained page; its household settings are one block near the top |
| `app/capabilities.json` | The runtime permissions the artifact declares |
| `backend/schema.json` | Every spreadsheet, tab, column, folder and doc, in exact order |
| `backend/sheet-guides.json` | The text for the read-only guide tabs inside the spreadsheets |
| `backend/doc-templates/` | The rulebook, site guide, app-change rules, preferences and pantry templates |
| `skills/dinner-time-data/` | The Claude skill (a header plus a copy of the rulebook) |
| `skills/chatgpt-project-instructions.md` | The matching ChatGPT Project instructions |
| `automation/refresh-task.md` | The prompt for the scheduled refresh task |
| `app-changes/_TEMPLATE CHANGE.md` | The form used to hand in a change to the app |
| `tools/dinnertime_kit.py` | Fills the templates and generates the spreadsheet-creation requests |
| `tools/privacy_check.py` | Scans any folder for emails, Google file IDs and private terms |
| `tools/tests/run_app_tests.js` | Browser tests for the app against a simulated Google Sheets |
| `docs/ARCHITECTURE.md`, `docs/PLACEHOLDERS.md` | How the pieces fit; what each placeholder means |

## Privacy

This kit contains no household's data: no names, email addresses, Google file IDs, links to anyone's files, recipes, inventory, gear or preferences. Template values look like `{{RECIPES_ID}}` or `PASTE_RECIPES_SPREADSHEET_ID`, and the only names are the made-up ones in `settings.example.json`. You can check for yourself: `python3 tools/privacy_check.py .` must report 0 findings.

Once an agent installs it for you, the files it creates in *your* Drive naturally contain *your* names and IDs. Don't pass those installed copies on; pass on this kit.

## What has and hasn't been tested

See `docs/TESTING.md`.
