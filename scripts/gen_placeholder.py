#!/usr/bin/env python3
"""Generate realistic-looking placeholder ATC transcript data for demo builds.

Writes batch-*.ndjson files to ndjson/ using the same structure as real
Labelbox exports so the full build pipeline runs end-to-end.

Usage:
  python3 scripts/gen_placeholder.py
  SEARCH_PASSWORD=... bash scripts/build.sh   # picks up generated files automatically
"""
import json, os, random, uuid

AIRPORTS = ['YSSY', 'YMML', 'YBBN', 'YPPH', 'NZAA', 'EGLL', 'EHAM', 'LSZH']
POSITIONS = ['Ground', 'Tower', 'Approach', 'Departure', 'Center']
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May']

CONVERSATIONS = [
    [("pilot", "Sydney Ground Qantas seven four two request push and start"),
     ("atco",  "Qantas seven four two push and start approved face south QNH one zero one three"),
     ("pilot", "Push and start approved facing south Qantas seven four two")],

    [("pilot", "Cleared for takeoff runway one six right"),
     ("atco",  "Affirmative runway one six right cleared for takeoff wind one eight zero at twelve"),
     ("pilot", "Runway one six right cleared for takeoff")],

    [("atco",  "Speedbird two one contact Melbourne Center one three two decimal four"),
     ("pilot", "One three two decimal four so long Speedbird two one"),
     ("atco",  "Good day")],

    [("pilot", "Request descent flight level two four zero"),
     ("atco",  "Descend flight level two four zero report leaving three six zero"),
     ("pilot", "Leaving three six zero for two four zero"),
     ("atco",  "Roger report established ILS runway three four left")],

    [("pilot", "On final three four left fully established"),
     ("atco",  "Cleared to land runway three four left wind three three zero at eight"),
     ("pilot", "Cleared to land three four left")],

    [("atco",  "Emirates four one six reduce speed to two one zero"),
     ("pilot", "Two one zero Emirates four one six"),
     ("atco",  "Expect ILS runway two three traffic eleven o clock five miles"),
     ("pilot", "Traffic in sight Emirates four one six")],

    [("pilot", "Mayday mayday mayday engine failure requesting immediate return"),
     ("atco",  "Emergency acknowledged turn left heading one eight zero descend four thousand feet"),
     ("pilot", "Left heading one eight zero descending four thousand"),
     ("atco",  "All traffic this frequency emergency in progress standby")],

    [("pilot", "Request shortcut direct RIVET"),
     ("atco",  "Proceed direct RIVET report overhead"),
     ("pilot", "Direct RIVET wilco"),
     ("atco",  "Amended clearance expect runway two eight on arrival weather improving")],

    [("pilot", "Holding at YAKKA low fuel declaring emergency"),
     ("atco",  "Emergency acknowledged cleared direct airport descend immediately"),
     ("pilot", "Cleared direct descending out of one one thousand")],

    [("atco",  "Air New Zealand six zero three taxi holding point alpha runway two three"),
     ("pilot", "Holding point alpha runway two three Air New Zealand six zero three"),
     ("atco",  "Line up and wait runway two three"),
     ("pilot", "Line up and wait two three Air New Zealand six zero three")],

    [("pilot", "Request traffic information"),
     ("atco",  "Traffic twelve o clock ten miles opposite direction altitude unknown"),
     ("pilot", "Looking traffic in sight"),
     ("atco",  "Pass behind maintain separation")],

    [("atco",  "Qantas four five squawk seven seven zero one"),
     ("pilot", "Seven seven zero one Qantas four five"),
     ("atco",  "Radar contact climb flight level three five zero"),
     ("pilot", "Climbing flight level three five zero Qantas four five")],

    [("pilot", "Passing through one eight thousand on climb"),
     ("atco",  "Roger continue climb flight level three seven zero direct MAPLE"),
     ("pilot", "Flight level three seven zero direct MAPLE")],

    [("atco",  "Virgin Australia eight zero two you are number two follow the A380 on short final"),
     ("pilot", "Traffic in sight number two Virgin Australia eight zero two"),
     ("atco",  "Cleared to land runway one six left wind variable five knots")],

    [("pilot", "Request frequency change"),
     ("atco",  "Approved contact Auckland Radio one two seven decimal three"),
     ("pilot", "One two seven three Auckland Radio")],
]

ANNOTATORS = [f"annot{i:02d}" for i in range(1, 9)]
REVIEWERS  = [f"revwr{i:02d}" for i in range(1, 4)]


def _make_row(project_id, index, reviewed):
    airport  = random.choice(AIRPORTS)
    position = random.choice(POSITIONS)
    month    = random.choice(MONTHS)
    day      = random.randint(1, 28)
    hour     = random.randint(0, 23)
    gk = f"{airport}-{position}-{month}-{day}-2026-{hour:02d}00Z_{index:03d}_VAD_v1.wav"
    row_id   = uuid.uuid4().hex[:20]
    duration = round(random.uniform(18, 110), 1)

    convo = random.choice(CONVERSATIONS)

    # Unique feature ID per speaker role
    role_fid = {}
    for role, _ in convo:
        if role not in role_fid:
            role_fid[role] = uuid.uuid4().hex[:8]

    # Speaker number → role mapping for classification block
    spk_cls = []
    for i, (role, fid) in enumerate(role_fid.items(), 1):
        spk_cls.append({"value": f"speaker_{i}", "radio_answer": {"value": role}})
    role_to_spkname = {r: f"Speaker {i}" for i, r in enumerate(role_fid.keys(), 1)}

    classifications = [{"value": "how_many_speakers_are_there",
                        "radio_answer": {"classifications": spk_cls}}]

    segments   = {fid: [] for fid in role_fid.values()}
    timestamps = {}
    cur_ms = random.randint(300, 1500)
    for role, text in convo:
        fid      = role_fid[role]
        start_ms = cur_ms
        end_ms   = start_ms + int(len(text.split()) * 370 + random.randint(-80, 150))
        segments[fid].append([start_ms, end_ms])
        timestamps[str(start_ms)] = {"classifications": [{
            "feature_id": fid,
            "name": role_to_spkname[role],
            "text_answer": {"content": text}
        }]}
        cur_ms = end_ms + random.randint(150, 700)

    workflow_history = []
    if reviewed:
        reviewer = random.choice(REVIEWERS)
        workflow_history.append({
            "action":     "Approve",
            "created_at": f"2026-04-{random.randint(1,28):02d}T{random.randint(8,18):02d}:00:00Z",
            "created_by": f"usr.email.{reviewer}@internal.labelbox.com",
        })

    annotator = random.choice(ANNOTATORS)
    return {
        "data_row":        {"id": row_id, "global_key": gk},
        "media_attributes": {"duration": duration},
        "projects": {
            project_id: {
                "project_details": {"workflow_history": workflow_history},
                "labels": [{
                    "label_details": {"created_by": f"usr.email.{annotator}@internal.labelbox.com"},
                    "annotations": {
                        "classifications": classifications,
                        "segments":        segments,
                        "timestamp":       timestamps,
                    }
                }]
            }
        }
    }


def generate(filename, project_id, n_rows, reviewed_pct=0.45):
    os.makedirs('ndjson', exist_ok=True)
    path = os.path.join('ndjson', filename)
    with open(path, 'w', encoding='utf-8') as f:
        for i in range(n_rows):
            row = _make_row(project_id, i + 1, random.random() < reviewed_pct)
            f.write(json.dumps(row) + '\n')
    print(f"✓ {path}: {n_rows} rows")


if __name__ == '__main__':
    random.seed(42)
    generate('batch-NeutralKoala-2026-04-27.ndjson',    'placeholder_nk', 45, reviewed_pct=0.60)
    generate('batch-CoastalLatency-2026-05-03.ndjson',  'placeholder_cl', 28, reviewed_pct=0.40)
    generate('batch-CoastalLatency-2026-05-04.ndjson',  'placeholder_cl', 28, reviewed_pct=0.50)
    print("\nDone. Run:  SEARCH_PASSWORD=... bash scripts/build.sh")
