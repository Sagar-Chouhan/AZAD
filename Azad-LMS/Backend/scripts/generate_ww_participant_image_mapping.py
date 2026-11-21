from __future__ import annotations

import csv
import re
from pathlib import Path

from app.database.database import SessionLocal
from app.modules.batch.model import BatchParticipant
from app.modules.users.model import ParticipantMaster


IMAGE_PATTERN = re.compile(
    r"^www_trainee_(?P<trainee_id>\d+)_[^/]+(?P<extension>\.jpg|\.jpeg|\.png)$",
    re.IGNORECASE,
)

BACKEND_DIR = Path(__file__).resolve().parents[1]
IMAGE_DIR = BACKEND_DIR / "uploads" / "participants"
REPORT_PATH = BACKEND_DIR / "ww_participant_image_mapping_report.csv"


def generate_report() -> list[dict[str, str]]:
    image_rows = []
    for image_path in sorted(IMAGE_DIR.glob("www_trainee_*")):
        match = IMAGE_PATTERN.fullmatch(image_path.name)
        if match:
            image_rows.append((int(match.group("trainee_id")), image_path.name))

    # This intentionally loads participant records only for reporting. It does
    # not infer a relationship from participant_id and does not write to DB.
    with SessionLocal() as db:
        participants = db.query(ParticipantMaster).order_by(
            ParticipantMaster.participant_id
        ).all()

    rows = [
        {
            "trainee_id": str(trainee_id),
            "image_filename": filename,
            "participant_id": "",
            "enrollment_no": "",
            "participant_name": "",
            "match_status": "UNMATCHED_NO_RELIABLE_MAPPING",
        }
        for trainee_id, filename in image_rows
    ]

    # Keep the query above as an explicit evidence check. The current schema
    # exposes no trustworthy trainee_id field or legacy mapping source.
    if not participants:
        raise RuntimeError("No participant records found; mapping report is invalid.")

    with REPORT_PATH.open("w", newline="", encoding="utf-8") as report_file:
        writer = csv.DictWriter(
            report_file,
            fieldnames=[
                "trainee_id",
                "image_filename",
                "participant_id",
                "enrollment_no",
                "participant_name",
                "match_status",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    return rows


if __name__ == "__main__":
    rows = generate_report()
    print(f"Generated {len(rows)} mapping rows.")
    print(f"Report: {REPORT_PATH}")
