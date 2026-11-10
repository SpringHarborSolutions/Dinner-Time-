# {{APP_TITLE}} Site Guide

Set up for {{HOUSEHOLD}}. Installed {{INSTALL_DATE}} (handoff kit {{KIT_VERSION}}).

# What {{APP_TITLE}} is

{{APP_TITLE}} is a phone-and-tablet app for the household's shopping lists, freezer, recipes, weekly menu and gear maintenance. It is a private Claude artifact published from {{OWNER_NAME}}'s Claude account. All of its data lives in Google Sheets in the **{{FOLDER_NAME}}** folder in Google Drive, so nothing is locked inside the app.

Most day-to-day updates can happen by talking to your AI assistant ({{AGENTS}}), which is connected to the same sheets. The app is the place to look at everything and make quick changes by hand.

App link: {{APP_URL}}

# Things to do first

1. **Pick your home photo.** Open the app, tap **Choose a photo** on the picture at the top of Home, and pick any photo. Everyone sees the same one, and you can change it any time with the camera button.
2. **Fill in your recipe preferences.** Each person has a doc: {{PREF_DOC_NAMES}}. Write what you love, avoid, can't eat, and how you like to cook. Your assistant reads these before suggesting meals or writing recipe ideas.
3. **List your pantry staples.** The **{{PANTRY_TITLE}}** doc tells your assistant what you always have, so recipe ideas only list what you'd need to buy.
4. **Tell the app who you are.** The first time each person opens the app it asks who they are, so every change is credited to the right person.

# Your AI assistant does the heavy lifting, on your plan

{{AGENTS}} can add and remove list items, log freezer packages, write recipe ideas for anything you pull from the freezer, plan the menu, rate recipes and log maintenance. Just ask in plain words. These skills run on **your own** AI account, so they count toward your plan's usage limits like any other chat. {{REFRESH_USAGE_LINE}}

Things to try:
- "Add milk, eggs and coffee to {{GROCERY_TAB}}."
- "We pulled the chicken thighs out of the freezer." (logs it and writes recipe ideas)
- "Plan tacos for Thursday and add a side salad."
- "Rate the lasagna 5 stars."
- "Changed the furnace filter today; remind me in 3 months."

# Pages

A bottom bar on the phone (a side rail on wide screens) switches between pages. Every section uses the same list, form and edit layout. The build number shows in small text at the bottom of every page, with a **Bug Report** button under it.

## Home
- Your home photo with a greeting for whoever is using the app.
- A tile for each section with a live count: open {{GROCERY_TAB}} and {{EXTRA_TAB}} items, oldest freezer item, recipes, tonight's menu and gear reminders due.

## Shopping
- One page with a {{GROCERY_TAB}} / {{EXTRA_TAB}} switch at the top.
- {{GROCERY_TAB}} items are grouped by store section in this order: {{AISLES}}, then Not sorted. The app guesses the section from the item name; tap the section chip to change it and it remembers.
- {{EXTRA_TAB}} shows oldest items first.
- Checking an item off is shared live, so everyone sees the basket at the store. Items can be added, edited and removed here.

## Freezer
- Identical packages show as one row with a count; an age badge goes from green to amber to red.
- Filter chips by category, by location and for undated items, plus search.
- Add, edit, mark used up, delete a mistaken entry or put an item back.
- Pick items to thaw and pull them in one go; recipe ideas for what you pulled are written by your assistant or the scheduled refresh.
{{PICK_DAY_GUIDE_LINE}}

## Recipes
- Photo cards with star averages, category chips and search.
- Each person rates a recipe 1–5 stars with an optional note.
- Freezer ideas show on their own and can be saved to your recipes.
- Every recipe has an **Add to shopping list** pill: tick the ingredients you need and they go to {{GROCERY_TAB}}.

## Menu
- The next 7 nights, each with a main and sides, styled like a printed menu.
- {{COOK_GUIDE_LINE}}
- Plan a night by typing a new dish or searching saved recipes and freezer ideas. Mark a night Made or Skipped.

## Gear and Maintenance
- Each piece of gear (vehicles, appliances, equipment) has details, photos, manuals and files.
- Free-text maintenance log with a Mileage / Hours reading; reminders by date, reading or both. Reminders more than 6 months out stay hidden.
- Manuals open in a built-in PDF viewer.

# Files in the {{FOLDER_NAME}} folder

- **00 Agent Rules – read first**: the rulebook your assistants follow. Leave it as is unless you're changing how the system works.
- **01 Shopping List**, **02 Freezer Inventory**, **03 Recipes and Menu**, **04 Gear and Maintenance**: the data. Tab names and column order must not change.
- **05 Bug Report**: notes sent from the app's Bug Report button, and anything you ask your assistant to log.
- {{PREF_DOC_NAMES}}, **{{PANTRY_TITLE}}**: yours to write.
- **19 Site Guide**: this document.
- **20 Recipe Images**, **21 Gear Images**, **22 Gear Files**, **23 Maintenance Images**, **29 Site Files**: photos and files.
- **30 App Changes**: where changes to the app itself are handed in (see its rules doc).
- **90 Setup Records**: the settings and prompts this install was built from.

# How changes reach the sheets

Anyone who opens the app with the Google Sheets connector allowed writes straight to the sheets. Everyone else's changes wait in the app's shared database, and {{SYNC_LINE}} Changes your assistant makes in the sheets show in the app the same way.

# Sharing with the household

{{OWNER_NAME}} shares the app from its page in Claude (invite each person as an Editor) and shares the **{{FOLDER_NAME}}** Drive folder with each person as an Editor. Each person opens the link and picks who they are.

# Maintaining the app

- The app's settings (people, colors, cook chart, list names, sheet IDs) are in the DT block near the top of its code. To change them, edit the block and republish to the same link.
- Changes to how the app looks or behaves go through **30 App Changes**.
- If you ever change the sheet layout, the app, the scheduled refresh, the 00 Agent Rules doc and every assistant's skill must change together.
