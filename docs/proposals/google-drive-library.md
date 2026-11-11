# Proposal: a Library on Google Drive

Draft for issue #1. Notion stays the default; Setup offers Google Drive as a choice. `references/library.md` stays the single contract: this proposal only adds a "Google Drive" column to it.

## 1. Shape

The Library is one Drive folder, named by the user in Setup (default "Graveyard Killer"). The memory line points to the folder. It holds:

- one Google Sheet, `Library`, with two tabs:
  - **Entries**: one row per Entry. Row 1 holds the Library's field names in the Settings language, so the header plays the role of Notion's property names. Frozen header.
  - **Settings**: one table with three columns, `Section | Key | Value`, holding the same sections as the Notion Settings page (Language, Fields, Statuses, Categories, Schedule, Graveyard). One row per field name, Status label, Category and setting.
- one Google Doc per Digest, `Digest YYYY-MM-DD`, in the same folder.

Field types:

| Notion type | On Drive |
| --- | --- |
| title, text, URL | plain text cell |
| select (Platform, Category, Status) | cell with a dropdown (data validation, list of values from the Settings) |
| multi-select (Tags) | text cell, Tags separated by commas. No option list to keep in sync, so the "send every option back" risk of Notion goes away; the rule "reuse an existing Tag where one fits" stays, reading the column first |
| date | date cell, ISO `YYYY-MM-DD` |

The Entry's page body has no place in a row, so it becomes three extra columns at the end: **Transcript**, **On-screen text** and **Captures** (one dated line per extra Capture). A Sheets cell holds up to 50,000 characters, which covers reels and short videos; for a longer transcript the Worker writes it to a Google Doc in a `Bodies` subfolder and puts the Doc's link in the Transcript cell. The full caption fits in the Caption cell, so the 2,000-character split is not needed.

## 2. Saving from the phone

Open point: I still have to read `docs/adr/0004` in 0.4.0 to see what Notion's share sheet gives that the Claude app does not. What I tested on 11/11/2026 from the Claude app on Android: I pasted a reel link into the chat and Claude wrote the row into a Google Sheet through the Google Sheets connector, which runs on Claude's side and does not need the computer. I have not yet tried the share sheet from Instagram to the Claude app, nor the full Capture flow of the skill on Drive. Google has no share target that writes straight into a Sheet, so on Drive the phone path is the Claude app chat. If 0.4.0 moved away from it for a reason that also applies here, I'll say so in this section.

## 3. Each operation of `library.md` on Drive

All through Claude's own Google Drive and Google Sheets connectors: no API key, no server (ADR 0001).

| Operation | Notion today | Google Drive |
| --- | --- | --- |
| Create the Library (Setup) | page + database + Settings page | create the folder, the Sheet, the two tabs, header row, dropdowns, frozen row |
| Read the Settings | read the Settings page | read the Settings tab |
| Create an Entry (Capture) | new database row | append one row to Entries |
| Find an Entry by its link | query Link equals | read the Link column, exact match; when the post id is known, also "contains id" |
| Update an Entry (Worker) | update properties | update the cells of that row, with the same "After Capture" rules |
| List the Inbox | query Status | read the Status and Captured columns, filter, sort by Captured then by row order |
| Write transcript and on-screen text | page body blocks | Transcript and On-screen text cells (or a linked Doc, see above) |
| Write the Digest | child page | new Google Doc in the folder |
| Duplicates | trash after the user agrees | delete the row after the user agrees; the "Duplicate of" Note and the rule stay the same |
| Add a Tag | add to the options first | nothing to do |

Writing rules that change on Drive:

- **No Markdown escaping**: cells are plain text. In its place, a value from the post that starts with `=`, `+`, `-` or `@` gets a leading apostrophe, so Sheets does not read it as a formula.
- **Long text**: 50,000 characters per cell instead of 2,000 per block.
- **Links**: same rule, no query string.
- Song lyrics, Statuses, Categories, the fallback Category and the Graveyard settings: unchanged.

## What I would test before a PR

Setup end to end on Drive, one Capture from the phone, one Worker run on Windows, one Digest, and the duplicate path, with a Library of at least a few hundred rows to check that reading whole columns stays fast.
