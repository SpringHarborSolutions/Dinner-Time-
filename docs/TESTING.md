# What was tested, and what wasn't

## Tested

**The app, in a real browser against simulated Google Sheets** (`tools/tests/run_app_tests.js`, headless Chrome, 41 checks, run for two made-up households: a two-person default and a three-person household with renamed lists, a different time zone, no cook chart, no pick day and the refresh off). The simulated spreadsheets are built from this kit's own `backend/schema.json` through the same creation requests an installer sends, so the test also proves the schema and the app agree.

- Loads with no errors for the owner, for a second person without the Google Sheets connector, and as a plain file.
- Lists: add writes the list row and an Activity Log event; remove deletes the row and writes History; the second list uses its own tab and ID prefix.
- Freezer: add writes Inventory and Change Log credited to the person; a pull writes Confirmed Withdrawals as pending.
- Recipes: create writes Recipes and RecipeCategories; a rating writes one Ratings row keyed by person.
- Menu: add writes Menu and Menu Log. Gear: save writes Gear; a maintenance log writes Maintenance.
- Bug Report: the button writes BUG-001 to the Bugs tab; without the connector the note waits in the queue.
- First-run welcome shows the household's own names. No sideways scrolling on any page at phone width. Only font and library hosts are requested.

**Against the real services** (a small, throwaway test with made-up data):
- Two of the five spreadsheets were created in Google Sheets from the generated requests and their headers read back correctly. The other three use the same three request types.
- The app file was accepted by Claude's artifact publisher, its capabilities were declared, and its database answered.

**The kit helper**: `validate`, `plan`, `render` and `check` run clean for both made-up households; `check` fails, as it should, while any ID is still missing.

**Privacy**: `tools/privacy_check.py` reports 0 findings on this kit.

## Not tested

- A complete install by a fresh agent in a fresh account, start to finish. The pieces are tested; the full runbook has not been walked end to end for this version.
- The scheduled refresh prompt running as a real scheduled task for this version. Its logic mirrors the app's own write logic line for line and an earlier version of the same prompt was run live, but treat the first few runs as a test: check the task's run history and the sheets.
- The app-change pipeline (31 Inbox → 32 Applied) installing a real package.
- Tapping through the app on a real phone with real Google Sheets behind it. Phase 8 of START-HERE.md is that test.
- ChatGPT following its Project instructions; what its Google connectors can do varies by plan.

If something doesn't work, the first places to look are the scheduled task's run history and the 05 Bug Report sheet.
