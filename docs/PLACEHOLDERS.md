# Placeholders

Templates in this kit use `{{NAME}}` placeholders. `tools/dinnertime_kit.py render` fills all of them from `settings.json`; this list is for filling them by hand.

| Placeholder | Meaning |
|---|---|
| `APP_TITLE`, `HOUSEHOLD`, `FOLDER_NAME` | from settings: app title, greeting name, Drive folder name |
| `TZ`, `TZ_STD`, `TZ_DST`, `TZ_STD_OFFSET` | IANA zone; labels like `EST (UTC-05:00)` / `EDT (UTC-04:00)`; the standard offset alone, like `-05:00` |
| `PEOPLE_NAMES`, `PEOPLE_IDS`, `OWNER_NAME`, `ROLE_NAME_MAP` | "A and B"; "a, b"; the owner's name; `person id "a" = "A", …` |
| `GROCERY_TAB`, `EXTRA_TAB` | the two list names (also the tab names in 01 Shopping List) |
| `AGENTS` | the assistants that edit data, e.g. "Claude and ChatGPT" |
| `INSTALL_DATE`, `KIT_VERSION` | YYYY-MM-DD; this kit's version |
| `FREEZER_LOCATIONS`, `AISLES` | comma-separated lists from settings |
| `COOK_LINE`, `COOK_GUIDE_LINE` | one sentence describing the cook chart (or that there is none), for assistants / for the guide |
| `PICK_DAY_RULE`, `PICK_DAY_GUIDE`, `PICK_DAY_GUIDE_LINE` | one sentence each about the pick day (or that there is none) |
| `IDEA_COUNT` | number of people + 2 |
| `IDEA_TABLE`, `IDEA_PERSON_LINES`, `IDEA_TAGS`, `IDEA_CATEGORIES` | the freezer-idea kinds: Our Recipes, one "For <Name>" per person (tag `For<Name>`), Adventure |
| `ARCHIVE_LINE`, `REFRESH_LINE`, `SYNC_LINE`, `REFRESH_USAGE_LINE` | one sentence each, depending on the refresh setting |
| `TRUSTED_ACCOUNTS` | comma-separated Google account emails allowed to hand in app changes |
| `PANTRY_TITLE` | "<next number> Pantry Staples" (12 for two people) |
| `PREF_DOC_NAMES`, `PREF_DOC_NAMES_PLAIN`, `PREF_DOC_LINES`, `PREF_DOCS_INLINE` | the preference docs' titles (and IDs) in four layouts |
| `PERSON_NAME` | the person a preferences doc is for |
| `*_ID` | the Google file or folder ID created during install: `ROOT_FOLDER_ID`, `SHOPPING_ID`, `FREEZER_ID`, `RECIPES_ID`, `GEAR_ID`, `BUGS_ID`, `RECIPE_IMAGES_ID`, `GEAR_IMAGES_ID`, `GEAR_FILES_ID`, `MAINT_IMAGES_ID`, `SITE_FILES_ID`, `APP_CHANGES_ID`, `INBOX_ID`, `APPLIED_ID`, `HELD_ID`, `DRAFTS_ID`, `RULES_DOC_ID`, `PANTRY_DOC_ID`, `GUIDE_DOC_ID`, `CHANGE_RULES_DOC_ID` |
| `APP_URL` | the published artifact's link |

The app's own settings are the JSON block between `/*DT_CONFIG_START*/` and `/*DT_CONFIG_END*/` in `app/dinner-time.html`: `appTitle`, `household`, `tz`, `people` (id, name, color), `owner`, `cook`, `pickDay`, `lists`, `sheets` (five spreadsheet IDs), `folders` (five folder IDs), `freezerLocations`, `aisles`, `bridge` (leave empty), `build`.
