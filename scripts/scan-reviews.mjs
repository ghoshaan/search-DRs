#!/usr/bin/env node
// Deep scan: walks every path in each row, collecting any field name that
// matches /review/i or /workflow/i (Labelbox sometimes uses "workflow" for
// review states). Prints a report of where review-ish data actually lives,
// so we can decide what to parse.
//
// Usage: node scripts/scan-reviews.mjs path/to/file.ndjson

import fs from 'node:fs';
import readline from 'node:readline';

const INPUT = process.argv[2] || 'input.ndjson';
if (!fs.existsSync(INPUT)) { console.error(`✗ Not found: ${INPUT}`); process.exit(1); }

// Map of "path pattern" -> { count, sampleValues: Set }
// Path is dotted with array indices flattened to [], e.g.
//   projects.[].labels.[].label_details.reviews
const findings = new Map();

function walk(node, path) {
  if (node === null || node === undefined) return;
  if (Array.isArray(node)) {
    for (const v of node) walk(v, path + '.[]');
    return;
  }
  if (typeof node !== 'object') return;
  for (const [k, v] of Object.entries(node)) {
    const p = path ? `${path}.${k}` : k;
    if (/review|workflow/i.test(k)) {
      if (!findings.has(p)) findings.set(p, { count: 0, samples: new Set(), nonEmpty: 0 });
      const e = findings.get(p);
      e.count++;
      // Track whether the value is "non-empty" (truthy + not [] + not {}).
      const empty =
        v === null || v === undefined || v === '' || v === false ||
        (Array.isArray(v) && v.length === 0) ||
        (typeof v === 'object' && !Array.isArray(v) && Object.keys(v).length === 0);
      if (!empty) {
        e.nonEmpty++;
        // Keep up to 3 distinct serialized samples for inspection.
        if (e.samples.size < 3) {
          const s = JSON.stringify(v);
          // Truncate huge values
          e.samples.add(s.length > 400 ? s.slice(0, 400) + '…' : s);
        }
      }
    }
    walk(v, p);
  }
}

const rl = readline.createInterface({
  input: fs.createReadStream(INPUT, { encoding: 'utf8' }),
  crlfDelay: Infinity,
});

let total = 0;
console.log(`→ Scanning ${INPUT} for review/workflow fields anywhere in each row…`);
for await (const line of rl) {
  const trimmed = line.trim();
  if (!trimmed) continue;
  total++;
  try {
    walk(JSON.parse(trimmed), '');
  } catch {}
  if (total % 5000 === 0) process.stdout.write(`  ${total} rows\r`);
}

console.log(`\nScanned ${total.toLocaleString()} rows.\n`);

// Sort findings by non-empty count (most interesting first).
const sorted = [...findings.entries()].sort((a, b) => b[1].nonEmpty - a[1].nonEmpty);

if (!sorted.length) {
  console.log('No fields matching /review|workflow/ found ANYWHERE in the data.');
  console.log('That means review status is either:');
  console.log('  • Stored under a different name (e.g. "issues", "approval", "status")');
  console.log('  • Only available via Labelbox API, not the export');
  console.log('  • Filtered out at export time');
  process.exit(0);
}

console.log('━'.repeat(80));
console.log('Path'.padEnd(60), 'seen'.padStart(8), 'non-empty'.padStart(11));
console.log('━'.repeat(80));
for (const [path, e] of sorted) {
  console.log(path.padEnd(60), String(e.count).padStart(8), String(e.nonEmpty).padStart(11));
}
console.log('━'.repeat(80));

console.log('\nSample non-empty values:\n');
for (const [path, e] of sorted) {
  if (!e.samples.size) continue;
  console.log(`▸ ${path}`);
  for (const s of e.samples) {
    console.log(`    ${s}`);
  }
  console.log();
}

if (sorted.every(([, e]) => e.nonEmpty === 0)) {
  console.log('All review/workflow fields exist but are empty in every row.');
  console.log('This typically means reviews are NOT included in your Labelbox export.');
  console.log('Check the export settings in Labelbox — there is usually a checkbox for');
  console.log('"Include performance details" or "Include review history" that needs to be');
  console.log('on. If you only have the standard export, reviews may need to be fetched');
  console.log('via the API separately.');
}
