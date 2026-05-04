#!/usr/bin/env python3
"""Export NDJSON from Labelbox projects and write BUILD_ARGS to $GITHUB_ENV.

Reads env vars:
  LABELBOX_API_KEY   — Labelbox API key
  LABELBOX_PROJECTS  — comma-separated PROJECT_ID:BATCH_NAME[:YYYY-MM-DD[-HH]]
  GITHUB_ENV         — path to GitHub Actions env file (set automatically by runner)
"""
import labelbox as lb
import json, os, sys


def main():
    api_key  = os.environ.get('LABELBOX_API_KEY', '')
    spec     = os.environ.get('LABELBOX_PROJECTS', '')
    env_file = os.environ.get('GITHUB_ENV', '')

    if not api_key:
        print('✗ LABELBOX_API_KEY is not set.', file=sys.stderr)
        sys.exit(1)
    if not spec:
        print('✗ LABELBOX_PROJECTS is not set.', file=sys.stderr)
        sys.exit(1)

    client = lb.Client(api_key=api_key)
    build_args = []

    for raw in spec.split(','):
        entry = raw.strip()
        if not entry:
            continue
        parts = entry.split(':')
        if len(parts) < 2:
            print(f"✗ '{entry}': expected PROJECT_ID:BATCH_NAME[:YYYY-MM-DD[-HH]]", file=sys.stderr)
            sys.exit(1)
        project_id = parts[0]
        batch      = parts[1]
        date       = parts[2] if len(parts) > 2 else None

        print(f"→ Exporting '{batch}' from project {project_id}…")
        project = client.get_project(project_id)

        # export_v2 is the stable name across SDK 3.x and 4.x
        task = project.export_v2(params={
            'performance_details': True,
            'label_details': True,
        })
        task.wait_till_done(timeout_seconds=300)

        if task.errors:
            print(f"✗ Export errors: {task.errors}", file=sys.stderr)
            sys.exit(1)

        outfile = f"batch-{batch}-{date}.ndjson" if date else f"batch-{batch}.ndjson"
        count = 0
        with open(outfile, 'w', encoding='utf-8') as f:
            for row in task.get_buffered_stream():
                line = getattr(row, 'json_str', None) or json.dumps(row.json)
                f.write(line.rstrip('\n') + '\n')
                count += 1

        size = os.path.getsize(outfile)
        if size < 100:
            print(f"✗ {outfile}: output too small ({size} bytes) — export may have failed", file=sys.stderr)
            sys.exit(1)

        # Sanity-check: first line must be valid JSON, not an HTML error page
        with open(outfile, encoding='utf-8') as check:
            first = check.readline().strip()
        if first.startswith('<'):
            print(f"✗ {outfile}: first line looks like HTML, not NDJSON:\n  {first[:120]}", file=sys.stderr)
            sys.exit(1)
        try:
            json.loads(first)
        except json.JSONDecodeError as e:
            print(f"✗ {outfile}: first line is not valid JSON: {e}", file=sys.stderr)
            sys.exit(1)

        print(f"✓ {outfile}: {count} rows · {size:,} bytes")
        build_args.append(f"{outfile}:{batch}:{date}" if date else f"{outfile}:{batch}")

    if env_file:
        with open(env_file, 'a', encoding='utf-8') as f:
            f.write('BUILD_ARGS=' + ' '.join(build_args) + '\n')

    print(f"→ BUILD_ARGS: {' '.join(build_args)}")


if __name__ == '__main__':
    main()
