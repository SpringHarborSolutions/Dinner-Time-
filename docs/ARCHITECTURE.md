# How Dinner Time! fits together

```
 phones / tablets                      owner's Claude account                 household Google Drive
 ┌──────────────────┐   shared db    ┌─────────────────────────┐   Sheets   ┌──────────────────────────┐
 │  the app (one    │◄──────────────►│ artifact database       │            │ 01 Shopping List         │
 │  HTML page)      │                │ (queues + snapshots)    │            │ 02 Freezer Inventory     │
 │                  │── viewer's ───────────────────────────────────────────►│ 03 Recipes and Menu      │
 └──────────────────┘   own Sheets   │ scheduled refresh task  │───────────►│ 04 Gear and Maintenance  │
                        connector    └─────────────────────────┘            │ 05 Bug Report            │
 assistants (Claude, ChatGPT) ── skills + 00 Agent Rules ───────────────────►│ docs, images, 30 App Changes │
                                                                             └──────────────────────────┘
```

**The sheets are the source of truth.** The app is a view with quick edits; assistants edit the sheets directly under the 00 Agent Rules doc.

**Two ways an app change reaches the sheets.**
1. A viewer whose Claude account has the Google Sheets connector allowed writes straight to the sheet, in one batch with its log rows, guarded by the spreadsheet revision.
2. Any other viewer's change is saved as a small document in a queue collection of the artifact's shared database. The next device with Sheets access, or the scheduled refresh, applies it using the same logic and deletes the queue document. Every operation is written so that applying it twice is harmless.

**Snapshots.** So that viewers without the connector still see data, whoever reads a sheet also saves a copy of the rows to the database (`snapshots/*`, `rxsnap/*`, `gsnap/*`). The app shows the freshest of live data and snapshot.

**Database collections.** `people` (who each viewer is), `settings` (home photo), `lists/<list>/checks` and `lists/<list>/pending` (live check-offs and unsaved adds), `aisles`, `saves`, `locks`; queues `saveQueue`, `fzQueue`, `rxEditQueue`, `rxRateQueue`, `menuQueue`, `gearQueue`, `bugQueue`; snapshots as above; `gearImg`, `gearPdf` (uploaded file links). The exact document shapes are spelled out in `automation/refresh-task.md`.

**The scheduled refresh** (one prompt, run hourly by default) does, in order: apply queued recipe, rating, freezer, menu, gear and bug changes; extract ingredients from new or edited recipes; write recipe ideas for freezer pulls; refresh every snapshot; archive past menu nights after 3 a.m.; and install at most two approved app-change packages from 30 App Changes > 31 Inbox.

**Changing the app.** Only the owner's account publishes. Anyone else (or their assistant) drafts a change package in 34 Drafts, marks it Ready and moves it to 31 Inbox; the refresh merges it, bumps the build shown at the bottom of every page, and files the package under 32 Applied, or under 33 Held with the reason.

**Not included.** The app file still contains an unused "bridge" mode for hosting outside Claude; this kit does not ship or support the server side of it. Leave `bridge` empty.
