# A Library on Google Drive, as a second backend (draft)

Draft for issue #11, not accepted yet.

Some users keep their life in Google Drive and have no Notion account. Asking them to open one only for Graveyard Killer loses them at Setup. So Setup offers a second Library backend, Google Drive, and Notion stays the default. Both backends follow one contract, [library.md](../../plugin/skills/graveyard-killer/references/library.md): it names each operation once and gives the Notion and the Drive way side by side. Every job reads the backend from the memory line and never mixes the two.

The Drive Library is one folder: a Google Sheet `Library` with an Entries tab (one row per Entry, the Library's field names in a frozen first row) and a Settings tab (`Section | Key | Value`), an `Inbox` folder for phone shares and an `Adopted` folder for the Inbox files the Worker has read. It is read and written only through Claude's own Google Drive and Google Sheets connectors, which need no API key ([ADR-0001](0001-no-server-no-api-keys.md)). The phone saves by sharing into `Inbox` from the Google Drive app, the same role Notion's share sheet has in [ADR-0004](0004-notion-share-sheet-captures.md).

## Considered Options

- **Notion only.** Simplest to maintain, but it shuts out Drive-only users.
- **A Google Doc per Entry.** Closest to a Notion page, but listing the Inbox or finding a link means opening every Doc. Rejected.
- **A Sheet with an Apps Script** to find rows and keep dropdowns. Scripts need the user to authorise them, and the agent cannot install one through the connectors. Rejected.
- **Pick the backend per job.** Rejected: one Library, one backend, read from the memory line.

## Consequences

- The connector writes values as if typed. A value from the post that starts with `=`, `+`, `-` or `@` gets a leading apostrophe, or Sheets reads it as a formula (tested: `=1+1` became 2, `+39 333 ...` became an error).
- A row is found by its Link every time, never by a remembered row number, since users sort and filter. The Worker reads the Link column, then reads that row again right before writing and checks the Link (tested after a sort).
- A strict dropdown does not stop the connector from writing another value (tested: `Processed` was accepted in a list of Italian labels). Labels always come from the Settings.
- Rows added with the connector's append are inserted rows and carry no dropdown (tested). A new Entry is written into the first empty row, which keeps the column's dropdown.
- The Worker cannot trash an Inbox file without asking, but it can move it. It moves each adopted file into `Adopted` (tested), so `Inbox` only holds what is still to read. The user can empty `Adopted` whenever they like.
- A Sheets cell holds 50,000 characters, so the 2,000-character splits of Notion are not needed. Transcripts longer than that go to a Google Doc in a `Bodies` folder, linked from the cell.
- The evals need a Drive test Library too (see the proposal).
- iOS is untested: neither of us has an iPhone. Chat Capture stays the route that works everywhere.
