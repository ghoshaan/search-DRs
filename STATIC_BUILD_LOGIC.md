# Static Site Build Logic Summary

This document summarizes the logic for building the static, encrypted transcript search tool. This process was used to generate the pre-packaged site where data was baked into encrypted blobs.

## 1. Data Export (`scripts/lb_export.py`)
- **Source**: Labelbox API.
- **Trigger**: Reads `LABELBOX_PROJECTS` (format `PROJECT_ID:BATCH_NAME`) and `LABELBOX_API_KEY`.
- **Action**: Exports project data (V2 export) and saves it as NDJSON files in the `ndjson/` directory.

## 2. Argument Preparation (`scripts/build_args.py`)
- Scans the `ndjson/` directory for files.
- Merges automated exports with manual uploads defined in `ndjson/manifest.json`.
- Extracts "snapshot dates" from filenames to track version history.

## 3. Core Builder (`scripts/build.mjs`)
The primary data processing and encryption engine.

### Data Processing
- **Parsing**: Extracts Airport, Position, Date, Time, Speaker Roles, and Transcript Segments from Labelbox annotations and keys.
- **Versioning**: Groups occurrences by Data Row ID, sorts by snapshot date, and detects changes (diffs) between versions.

### Indexing & Search
- Uses **MiniSearch** to build a client-side search index.

### Security & Encryption
- **Key Derivation**: PBKDF2 (SHA-256) with 600,000 iterations derived from a passphrase.
- **Compression**: Gzip-compresses data and index before encryption.
- **Encryption**: AES-256-GCM.
- **Outputs**: `public/data.enc` (data), `public/index.enc` (index), `public/meta.json` (salt and facets).

## 4. Deployment
- Handled via `scripts/build.sh` and GitHub Workflows (`deploy.yml`).

*Note: This entire workflow has been superseded by the direct browser-side NDJSON upload model.*
