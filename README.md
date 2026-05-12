# ATC Transcript Audit Tool

Client-side tool for comparing transcript snapshots and auditing edit history.

- **Compare**: Upload "Before" and "After" Labelbox NDJSON snapshots to see exact changes.
- **Search**: [MiniSearch](https://lucaong.github.io/minisearch/) with fuzzy + prefix matching.
- **Audit**: Highlights transcript revisions, role flips, and time shifts between versions.
- **Export**: Generate audit reports (PDF) for selected recordings.
- **Privacy**: All processing happens in your browser. Files are never uploaded to a server.

## Usage

1. Open the tool (`public/index.html`).
2. Select your "Before" snapshot (NDJSON export from Labelbox).
3. Select your "After" snapshot (NDJSON export from Labelbox).
4. Click **Compare Snapshots**.
5. Use the search and filters to audit changes.

## Development

The tool is a static web application.

```bash
# Install dependencies
npm install

# Open public/index.html in a browser
```

No build step is required for data processing as all parsing and indexing happens client-side.
