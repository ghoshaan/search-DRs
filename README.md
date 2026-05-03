# ATC Transcript Search

Static, password-gated, full-text search over ATC transcript NDJSON.

- **Search**: [MiniSearch](https://lucaong.github.io/minisearch/) with fuzzy + prefix matching
- **Filters**: role, batch, airport, position, date, annotator
- **Privacy**: AES-256-GCM with PBKDF2-SHA256 (600k iterations)
- **Hosting**: GitHub Pages, deployed by GitHub Actions

## Adding new batches

Each NDJSON you upload becomes a "batch" — a tag stamped onto every row from
that file, so you can filter by it later.

To add a new batch:

1. Upload the new NDJSON to Google Drive, set sharing to "Anyone with the
   link"
2. Grab the file ID (the bit between `/d/` and `/view`)
3. On GitHub: **Settings → Secrets and variables → Actions → GDRIVE_FILES**
   (the multi-file secret). Edit it to add a new comma-separated entry of the
   form `FILE_ID:batch_name`. Example:

   ```
   1abc...XYZ:january, 2def...UVW:february, 3ghi...RST:march
   ```

   Batch names must be filename-safe (letters, digits, dot, dash, underscore).
4. **Actions tab → build-and-deploy → Run workflow**

The build script automatically dedupes by row `id` across batches, so if a
recording appears in two files only the first wins.

### Backwards compat

If you set `GDRIVE_FILE_ID` (the original single-file secret) instead of
`GDRIVE_FILES`, the workflow treats it as a single batch named `input`.
You can keep using it that way — `GDRIVE_FILES` is only needed for multiple
batches.

## Local development

```bash
npm install

# Single file
SEARCH_PASSWORD="..." npm run build -- input.ndjson

# Multiple files with batch names
SEARCH_PASSWORD="..." npm run build -- jan.ndjson:january feb.ndjson:february

# Preview
npx serve public
```

On Windows Command Prompt, set the env var separately first:

```cmd
set SEARCH_PASSWORD=yourpassphrase
npm run build -- jan.ndjson:january feb.ndjson:february
```

## How privacy works

There is no server. The flow is:

1. **Build time** — `scripts/build.mjs` reads NDJSONs, flattens rows, builds
   the MiniSearch index, then encrypts `data.json` and `index.json` with a
   key derived from your passphrase (PBKDF2 / 600k iters / SHA-256). It
   writes three files into `public/`:
   - `data.enc` — encrypted records
   - `index.enc` — encrypted MiniSearch index
   - `meta.json` — public: KDF salt + iterations + facet lists + counts
2. **Page load** — visitor sees a passphrase prompt. The browser derives the
   AES key, fetches the `.enc` blobs, decrypts them in-memory using
   WebCrypto.
3. **Wrong passphrase** — AES-GCM authentication fails and the page shows
   "wrong passphrase".

The passphrase is cached in `sessionStorage` for the tab, so reloads don't
re-prompt. The "lock" button or closing the tab clears it.

### What this protects against

- Search engines, scrapers, anyone without the passphrase
- Casual snooping — real ciphertext, not a `if (password === ...)` check
- Brute force, given a strong passphrase. ~0.5s per guess on a fast CPU.

### What it does not protect against

- Passphrase leaks. To rotate, change the GitHub secret + re-run workflow.
- Weak passphrases.
- The facet lists in `meta.json` are public (airport codes, batch names,
  annotator IDs, etc.). If those are sensitive, see "tightening" below.

## Filename parsing

Filenames like `YPJT2-Center-Jan-25-2026-0100Z_25_VAD_v2.wav` get parsed into:
- `airport` → `YPJT2`
- `position` → `Center`
- `date` → `Jan-25-2026`
- `time` → `0100Z`

The regex is `KEY_RE` in `scripts/build.mjs`. Adjust if your filename
convention differs.

## Annotator parsing

`label.label_details.created_by` looks like:
`usr.email.cmnpwy74k0xdt07080m2ca04e@internal.labelbox.com`

The middle part (the bit between `usr.email.` and `@`) is extracted as the
`annotator` field. Regex is `ANNOTATOR_RE` in the build script.

## Tunable knobs

The MiniSearch options live in `scripts/build.mjs` and `index.html` and
**must match**:

| Knob | Effect |
|------|--------|
| `fuzzy: 0.2` | typo tolerance. Higher = more forgiving |
| `prefix: true` | "depart" matches "departure" |
| `boost: { key: 2 }` | filename matches rank above transcript-only |
| `combineWith: 'AND'` (in `index.html`) | multi-word queries require all terms |
| `ITERATIONS = 600_000` | PBKDF2 cost. Higher = slower brute force *and* slower unlock |

## Tightening

By default `meta.json` (with facet lists) is public. To hide it:

1. In `build.mjs`, move `facets` into the encrypted `data` blob and out of
   `meta.json`
2. In `index.html`, populate the facet UI *after* decryption instead of from
   `meta.json`

You'd lose the lock-screen recording/hours counters but reveal nothing.

## File layout

```
.
├── .github/workflows/deploy.yml
├── scripts/build.mjs
├── public/
│   ├── index.html
│   ├── data.enc       (generated, encrypted)
│   ├── index.enc      (generated, encrypted)
│   └── meta.json      (generated, public)
├── package.json
└── README.md
```
