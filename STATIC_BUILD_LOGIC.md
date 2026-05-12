# Static Site Build Logic Summary

This document summarizes the logic for building the static, encrypted transcript search tool. This process is used to generate the pre-packaged site (e.g., for deployment to Vercel) where data is baked into encrypted blobs.

## 1. Data Export (`scripts/lb_export.py`)
- **Source**: Labelbox API.
- **Trigger**: Reads `LABELBOX_PROJECTS` (format `PROJECT_ID:BATCH_NAME`) and `LABELBOX_API_KEY`.
- **Action**: Exports project data (V2 export) and saves it as NDJSON files in the `ndjson/` directory.
- **Naming**: Files are named `batch-{BATCH}-{DATE}.ndjson`.

## 2. Argument Preparation (`scripts/build_args.py`)
- Scans the `ndjson/` directory for files.
- Merges automated exports with manual uploads defined in `ndjson/manifest.json`.
- Extracts "snapshot dates" from filenames to track version history.
- Prints a list of formatted arguments (`path:batch:date`) for the main builder.

## 3. Core Builder (`scripts/build.mjs`)
The primary data processing and encryption engine.

### Data Processing
- **Parsing**:
  - Extracts **Airport**, **Position**, **Date**, and **Time** from the `global_key` (data row key).
  - Extracts **Speaker Roles** and **Transcript Segments** from Labelbox annotations.
  - Identifies **Review Status** and the most recent reviewer from workflow history.
- **Versioning**:
  - Groups occurrences by Data Row ID.
  - Sorts by snapshot date and collapses identical consecutive entries.
  - Detects changes between snapshots (e.g., "transcript revised", "approved").

### Indexing & Search
- Uses **MiniSearch** to build a client-side search index.
- Fields indexed: `transcript`, `key`, `drId`.

### Security & Encryption
- **Key Derivation**: Uses PBKDF2 (SHA-256) with 600,000 iterations to derive a 256-bit key from the `SEARCH_PASSWORD`.
- **Compression**: Gzip-compresses the data and index JSON before encryption to reduce size.
- **Encryption**: Uses AES-256-GCM.
- **Outputs**:
  - `public/data.enc`: Encrypted full document data.
  - `public/index.enc`: Encrypted search index.
  - `public/meta.json`: Publicly visible metadata (salt, iterations, counts, and pre-calculated facet lists for filters).

## 4. Deployment Wrapper (`scripts/build.sh`)
- Handles Git LFS authentication and pulling.
- Orchestrates the Python and Node.js scripts to perform a full build.

## Client-Side Loading (`public/index.html` - Old Logic)
The static site's `index.html` (when used in this build mode) would:
1. Prompt for a passphrase.
2. Derive the key using the salt from `meta.json`.
3. Fetch and decrypt `data.enc` and `index.enc`.
4. Decompress the decrypted payloads.
5. Initialize the UI and search engine.
