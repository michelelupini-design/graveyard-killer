# Proposal: a Library on Google Drive

For issue #11. Notion stays the default; Setup offers Google Drive as a choice. `references/library.md` stays the single contract: this proposal only adds a "Google Drive" column to it. The decision is drafted as [ADR-0005](../adr/0005-google-drive-library.md).

## 1. Shape

The Library is one Drive folder, named by the user in Setup (default "Graveyard Killer"). The memory line points to the folder. It holds:

- one Google Sheet, `Library`, with two tabs:
  - **Entries**: one row per Entry. Row 1 holds the Library's field names in the Settings language, so the header plays the role of Notion's property names. Frozen header.
  - **Settings**: one table with three columns, `Section | Key | Value`, holding the same sections as the Notion Settings page, in the same order.
- a folder `Inbox`, where the phone shares land;
- a folder `Adopted`, where the Worker moves each Inbox file it has read.

There is no Digest file: since 0.4.0 the Digest is given in a chat.

Field types:

| Notion type | On Drive |
| --- | --- |
| title, text, URL | plain text cell |
| select (Platform, Category, Status) | cell with a dropdown (data validation, list of labels from the Settings) |
| multi-select (Tags) | text cell, Tags separated by commas. No option list to keep in sync; "reuse an existing Tag where one fits" stays, reading the column first |
| date | `YYYY-MM-DD`, which Sheets stores as a real date, so the column sorts |

The Entry's page body becomes three extra columns at the end: **Transcript**, **On-screen text** and **Captures** (one dated line per extra Capture). A cell holds up to 50,000 characters; a longer transcript goes to a Google Doc in a `Bodies` subfolder, linked from the Transcript cell.

## 2. Saving from the phone

Tested on Android on 2026-11-11: Instagram, YouTube and TikTok → Share → Drive → `Inbox` saves a small file whose content is the post's link (with a query string). From Instagram it is a `.txt` file named after the start of the link; from YouTube a file with no extension, named after the video's title. No agent, no tokens, no computer. Setup teaches this share first, as in ADR-0004, and the Worker adopts every file in `Inbox` that holds a link. Chat Capture stays the second route. Not tested: iOS.

## 3. Each operation on Drive, with the connector tool that does it

Tested on 2026-11-12 with Claude's Google Drive and Google Sheets connectors on a test Library. The same two connectors show as connected in Claude Code 2.1.301 on Windows (`claude mcp list`: `claude.ai Google Drive`, `claude.ai Google Sheets`), so the Worker needs no API key; on the phone, the Claude app writes rows through the same Sheets connector (tested 2026-11-11).

| Operation | Notion today | Google Drive | Connector tool |
| --- | --- | --- | --- |
| Create the Library (Setup) | page + database + Settings page | folders `Library`, `Inbox`, `Adopted`; the Sheet | Drive `create_file` |
| Name the tabs, freeze the header, add the Settings tab, set the dropdowns | | one batch | Sheets `update_spreadsheet` (`updateSheetProperties`, `addSheet`, `setDataValidation`) |
| Write the header and the Settings | Settings page | header row, Settings rows | Sheets `update_values` |
| Read the Settings | read the page | read the Settings tab | Sheets `get_values` |
| Create an Entry | new row | write into the first empty row (not append, see below) | Sheets `get_values` on the Link column, then `update_values` |
| Find an Entry by its link | query Link equals | read the Link column, exact match; when the post id is known, also "contains id"; read the row again and check the Link before writing | Sheets `get_values` |
| Update an Entry | update properties | update that row's cells, with the same "After Capture" rules | Sheets `update_values` |
| List the Inbox | query Status | read the Status and Captured columns, filter, sort by Captured | Sheets `get_values` |
| Adopt a shared file | row with no Status | list `Inbox`, read each file's link, write the Entry, move the file to `Adopted` | Drive `search_files`, `read_file_content`, `update_file` (`parentId`) |
| Duplicates | trash after the user agrees | delete the row after the user agrees | Sheets `update_spreadsheet` (`deleteDimension`) |
| Add a Tag | add to the options first | nothing to do | |

## 4. What the test showed

- **Formulas.** The connector writes values as if typed: `=1+1` became 2 and `+39 333 testo` became `#ERROR!`. With a leading apostrophe both stayed text. So a value from the post that starts with `=`, `+`, `-` or `@` gets an apostrophe; the cell shows the value without it.
- **Rows move.** After sorting by Captured, the test row moved from row 2 to row 5. Reading the Link column found it at row 5, and re-reading row 5 before writing confirmed the Link. A remembered row number would have written into the wrong Entry.
- **Dropdowns.** A strict dropdown did not stop the connector: `Processed` was written into a list of Italian labels. So labels always come from the Settings, never from memory.
- **Append.** Rows written with `append_values` are inserted rows and lost the column's dropdown; the dropdown stayed on the rows below. A row written with `update_values` into the first empty row kept it. So Capture and adoption write into the first empty row. Setup sets the dropdowns on the whole column, so new rows find them.
- **Inbox files.** Trashing an Inbox file needs the user's say-so, as Andrea expected. Renaming one and moving it into `Adopted` both worked with no prompt. Moving is cleaner: `Inbox` then only holds what is still to read.

## 5. Still open

- **iOS:** untested, as neither of us has an iPhone. Chat Capture stays the route that works everywhere.
- **Scale:** reading whole columns was not timed on a Library of a few hundred rows.
- **Evals on Drive:** keep `capture.json` and `worker.json` and add a backend placeholder: the memory line points to a Drive test Library built by Setup, and the seeds are written as rows or shared into `Inbox`. Expected outputs speak of Entries, fields and Statuses, so most carry over. Add Drive-only evals: an Inbox file adopted and moved, a caption starting with `=`, an Entry updated after the user sorted the Sheet, and a duplicate row deleted after the user agrees. I can run them on Windows in Claude Code.
