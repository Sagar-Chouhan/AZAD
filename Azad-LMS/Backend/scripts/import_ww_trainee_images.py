from __future__ import annotations

import csv
import re
import shutil
from pathlib import Path


IMAGE_PATTERN = re.compile(
    r"^www_trainee_(?P<trainee_id>\d+)_[^/]+(?P<extension>\.jpg|\.jpeg|\.png)$",
    re.IGNORECASE,
)
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png"}

BACKEND_DIR = Path(__file__).resolve().parents[1]
SOURCE_DIR = BACKEND_DIR / "app" / "storage" / "uploads" / "participants" / "2025"
DESTINATION_DIR = BACKEND_DIR / "uploads" / "participants"
REPORT_PATH = BACKEND_DIR / "participant_image_import_report.csv"


def import_images() -> list[dict[str, str]]:
    DESTINATION_DIR.mkdir(parents=True, exist_ok=True)
    report: list[dict[str, str]] = []

    for source_path in sorted(SOURCE_DIR.iterdir()):
        match = IMAGE_PATTERN.fullmatch(source_path.name)
        if not source_path.is_file() or not match:
            continue

        destination_path = DESTINATION_DIR / source_path.name
        status = "IMPORTED"
        detail = ""

        try:
            if destination_path.exists():
                status = "ALREADY_EXISTS"
            else:
                shutil.copy2(source_path, destination_path)
        except OSError as error:
            status = "FAILED"
            detail = str(error)

        report.append(
            {
                "filename": source_path.name,
                "trainee_id": match.group("trainee_id"),
                "destination_path": str(destination_path.relative_to(BACKEND_DIR)),
                "import_status": status,
                "detail": detail,
            }
        )

    with REPORT_PATH.open("w", newline="", encoding="utf-8") as report_file:
        writer = csv.DictWriter(
            report_file,
            fieldnames=[
                "filename",
                "trainee_id",
                "destination_path",
                "import_status",
                "detail",
            ],
        )
        writer.writeheader()
        writer.writerows(report)

    return report


if __name__ == "__main__":
    results = import_images()
    counts: dict[str, int] = {}
    for result in results:
        counts[result["import_status"]] = counts.get(result["import_status"], 0) + 1

    print(f"Processed {len(results)} images.")
    for status, count in sorted(counts.items()):
        print(f"{status}: {count}")
    print(f"Report: {REPORT_PATH}")
