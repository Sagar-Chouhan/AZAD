import re
import sys
from pathlib import Path
from collections import Counter

import pandas as pd
from sqlalchemy import or_, func
from sqlalchemy.orm import Session


# ============================================================
# BACKEND PATH
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))


# ============================================================
# PROJECT IMPORTS
# ============================================================

from app.database.database import SessionLocal

from app.modules.Integration.schema import (
    WWWTraineeCreateRequest,
)

from app.modules.Integration.service import (
    WWWIntegrationService,
)

from app.modules.centres.model import CentreMaster
from app.modules.batch.model import BatchMaster
from app.modules.users.model import ParticipantMaster


# ============================================================
# CONFIG
# ============================================================

EXCEL_FILE = (
    BACKEND_DIR / "LMS_Trainee_Import_Data_CORRECTED.xlsx"
)

VALIDATION_REPORT = (
    BACKEND_DIR / "LMS_Trainee_Validation_Report.xlsx"
)

IMPORT_ERROR_REPORT = (
    BACKEND_DIR / "LMS_Trainee_Import_Errors.xlsx"
)


# ============================================================
# IMPORTANT
# ============================================================

# False = validation only
# True  = actual DB import

# ALWAYS RUN FALSE FIRST.
IMPORT_MODE = True


# ============================================================
# EXCEL COLUMN ALIASES
# ============================================================

COLUMN_ALIASES = {

    "participant_name": [
        "Trainee Name",
        "Participant Name",
        "Student Name",
        "Name",
        "Trainee",
        "Participant",
    ],

    "enrollment_no": [
        "Enrollment No",
        "Enrollment Number",
        "Enrollment",
        "Enrolment No",
        "Enrolment Number",
        "Registration No",
        "Registration Number",
        "Registration ID",
    ],

    "centre_code": [
        "Centre Code",
        "Center Code",
        "Centre ID",
        "Center ID",
        "Centre",
        "Center",
        "Centre No",
        "Center No",
        "Centre Number",
        "Center Number",
        "Centre Code / ID",
        "Centre Code/ID",
        "Select Centre",
        "Select Center",
    ],

    "batch_id": [
        "Batch ID",
        "Batch",
        "Batch No",
        "Batch Number",
        "Select Batch",
        "Batch Name",
        "Batch Code",
    ],

    "gender": [
        "Gender",
        "Sex",
    ],

    "age": [
        "Age",
    ],

    "email": [
        "Email",
        "Email ID",
        "Email Address",
    ],

    "mobile_no": [
        "Mobile No",
        "Mobile Number",
        "Mobile",
        "Phone",
        "Phone Number",
        "Contact No",
        "Contact Number",
    ],

    "pin": [
        "PIN Code",
        "Pin Code",
        "Pincode",
        "PIN",
        "Pin",
        "Postal Code",
    ],

    "location": [
        "Location",
        "Village",
        "Village Name",
        "Address Location",
    ],

    "address": [
        "Address",
        "Full Address",
        "Permanent Address",
        "Current Address",
    ],

    "username": [
        "Username",
        "User Name",
        "Login Username",
        "Login ID",
        "Login Id",
    ],

    "password": [
        "Password",
        "Login Password",
        "User Password",
    ],

    "images": [
        "Trainee Image",
        "Profile Image",
        "Image",
        "Profile Photo",
        "Photo",
    ],
}


# ============================================================
# HELPERS
# ============================================================

def clean(value):
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    value = str(value).strip()

    if not value:
        return None

    if value.lower() in {
        "nan",
        "none",
        "null",
        "n/a",
        "na",
        "-",
    }:
        return None

    # Excel 123.0 -> 123
    if re.fullmatch(r"-?\d+\.0", value):
        value = value[:-2]

    return value


def normalize_column_name(name):
    if name is None:
        return ""

    value = str(name).strip().lower()

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value,
    )

    return " ".join(value.split())


def normalize_value(value):
    value = clean(value)

    if not value:
        return None

    return value.strip().lower()


def normalize_match(value):
    value = clean(value)

    if not value:
        return ""

    value = value.lower().strip()

    value = value.replace("–", "-")
    value = value.replace("—", "-")
    value = value.replace("_", " ")

    value = re.sub(r"\s+", " ", value)

    return value


def simplify_name(value):
    """
    Converts:

        South Kolkata Center
        South Kolkata Centre

    into:

        south kolkata
    """

    value = normalize_match(value)

    value = re.sub(
        r"\s+(center|centre)$",
        "",
        value,
    )

    return value.strip()


def build_column_map(df):
    mapping = {}

    for column in df.columns:
        normalized = normalize_column_name(column)

        if normalized:
            mapping[normalized] = column

    return mapping


def find_column(column_map, aliases):
    for alias in aliases:
        normalized_alias = normalize_column_name(alias)

        if normalized_alias in column_map:
            return column_map[normalized_alias]

    return None


def get_value(row, column_map, aliases):
    actual_column = find_column(
        column_map,
        aliases,
    )

    if actual_column is None:
        return None

    return clean(row.get(actual_column))


def get_int(value, default=None):
    value = clean(value)

    if not value:
        return default

    try:
        return int(float(value))
    except Exception:
        return default


# ============================================================
# CENTRE MATCHING
# ============================================================

def split_centre_value(value):
    """
    Examples:

        West Bengal-South 24 Parganas-South Kolkata

    becomes:

        [
            "west bengal",
            "south 24 parganas",
            "south kolkata"
        ]
    """

    value = normalize_match(value)

    if not value:
        return []

    parts = re.split(
        r"\s*[-/|>]+\s*",
        value,
    )

    return [
        normalize_match(part)
        for part in parts
        if normalize_match(part)
    ]


def build_centre_index(db):
    """
    Load all active centres once.

    This avoids querying centre_masters
    for every Excel row.
    """

    centres = (
        db.query(CentreMaster)
        .filter(
            CentreMaster.deleted_at.is_(None)
        )
        .all()
    )

    index = {
        "exact": {},
        "simple": {},
        "tokens": {},
    }

    for centre in centres:

        values = [
            centre.mis_centre_id,
            centre.centre_name,
            centre.location,
        ]

        for raw in values:

            value = normalize_match(raw)

            if not value:
                continue

            index["exact"].setdefault(
                value,
                centre,
            )

            simple = simplify_name(value)

            if simple:
                index["simple"].setdefault(
                    simple,
                    centre,
                )

            for token in split_centre_value(value):

                if token:
                    index["tokens"].setdefault(
                        token,
                        [],
                    )

                    if centre not in index["tokens"][token]:
                        index["tokens"][token].append(
                            centre
                        )

    return index


def find_centre(
    centre_index,
    centre_value,
):
    """
    Robust centre resolver.

    Supported:

    1. Exact MIS centre ID
    2. Exact centre name
    3. Exact location
    4. Centre name without Center/Centre suffix
    5. Composite Excel centre values
    6. Last meaningful component matching

    Examples:

        South Kolkata
            -> South Kolkata Center

        West Bengal-Kolkata-South Kolkata
            -> South Kolkata Center

        West Bengal-South 24 Parganas-South Kolkata
            -> South Kolkata Center

        Delhi-East Delhi-East Delhi
            -> East Delhi Center

        Tamil Nadu-Chennai-Chennai
            -> Chennai Center

        Rajasthan-Jaipur Heritage-Jaipur
            -> Jaipur Center
    """

    value = normalize_match(centre_value)

    if not value:
        return None

    # --------------------------------------------------------
    # EXACT
    # --------------------------------------------------------

    centre = centre_index["exact"].get(value)

    if centre:
        return centre

    # --------------------------------------------------------
    # SIMPLE NAME
    # --------------------------------------------------------

    simple = simplify_name(value)

    centre = centre_index["simple"].get(simple)

    if centre:
        return centre

    # --------------------------------------------------------
    # COMPOSITE VALUE
    # --------------------------------------------------------

    parts = split_centre_value(value)

    if not parts:
        return None

    # Last part has highest priority.
    # Example:
    #
    # West Bengal-Kolkata-South Kolkata
    #
    # last part = South Kolkata

    for part in reversed(parts):

        if not part:
            continue

        # Exact simple candidate
        centre = centre_index["simple"].get(
            simplify_name(part)
        )

        if centre:
            return centre

        # Exact token candidate
        candidates = centre_index["tokens"].get(
            part,
            [],
        )

        if len(candidates) == 1:
            return candidates[0]

        if candidates:

            # Prefer centre_name match
            for candidate in candidates:

                centre_name = simplify_name(
                    candidate.centre_name
                )

                if (
                    centre_name == part
                    or part == normalize_match(
                        candidate.mis_centre_id
                    )
                ):
                    return candidate

            # If still ambiguous, don't randomly choose.
            # Continue checking next component.
            continue

    # --------------------------------------------------------
    # CONTAINS MATCH
    # --------------------------------------------------------

    for part in reversed(parts):

        if not part:
            continue

        matches = []

        for candidate in centre_index["exact"].values():

            candidate_name = simplify_name(
                candidate.centre_name
            )

            candidate_location = simplify_name(
                candidate.location
            )

            candidate_mis = simplify_name(
                candidate.mis_centre_id
            )

            candidate_values = {
                candidate_name,
                candidate_location,
                candidate_mis,
            }

            for candidate_value in candidate_values:

                if not candidate_value:
                    continue

                if (
                    part == candidate_value
                    or part in candidate_value
                    or candidate_value in part
                ):
                    matches.append(candidate)
                    break

        unique = []

        for candidate in matches:
            if candidate not in unique:
                unique.append(candidate)

        if len(unique) == 1:
            return unique[0]

    return None


# ============================================================
# BATCH MATCHING
# ============================================================

def normalize_batch(value):
    value = clean(value)

    if not value:
        return ""

    return value.strip().lower()


def build_batch_index(db):
    """
    Load active batches once.

    Batch matching is always scoped by centre_id.
    """

    batches = (
        db.query(BatchMaster)
        .filter(
            BatchMaster.deleted_at.is_(None)
        )
        .all()
    )

    index = {}

    for batch in batches:

        centre_id = batch.centre_id

        if centre_id not in index:
            index[centre_id] = {
                "exact": {},
                "numeric": {},
            }

        values = [
            batch.mis_batch_id,
            batch.batch_name,
        ]

        for raw in values:

            value = normalize_batch(raw)

            if value:
                index[centre_id]["exact"].setdefault(
                    value,
                    batch,
                )
                if value.startswith("batch-"):
                    num = value[6:].strip()
                    if num:
                        index[centre_id]["exact"].setdefault(num, batch)
                elif value.startswith("batch "):
                    num = value[6:].strip()
                    if num:
                        index[centre_id]["exact"].setdefault(num, batch)
                else:
                    index[centre_id]["exact"].setdefault(f"batch-{value}", batch)

        if batch.batch_id is not None:

            index[centre_id]["numeric"][
                str(batch.batch_id)
            ] = batch

    return index


def find_batch(
    batch_index,
    centre,
    batch_value,
):
    """
    Match batch only inside selected centre.

    Priority:

    1. mis_batch_id
    2. batch_name (exact or with/without 'Batch-' prefix)
    3. internal batch_id
    """

    if not centre:
        return None

    value = normalize_batch(batch_value)

    if not value:
        return None

    centre_batches = batch_index.get(
        centre.centre_id
    )

    if not centre_batches:
        return None

    # MIS batch ID / batch name
    batch = centre_batches["exact"].get(
        value
    )

    if batch:
        return batch

    if value.startswith("batch-"):
        batch = centre_batches["exact"].get(
            value[6:].strip()
        )
        if batch:
            return batch
    else:
        batch = centre_batches["exact"].get(
            f"batch-{value}"
        )
        if batch:
            return batch

    # Internal DB batch ID
    if value.isdigit():

        batch = centre_batches["numeric"].get(
            value
        )

        if batch:
            return batch

    return None


# ============================================================
# USERNAME
# ============================================================

def generate_username(
    enrollment_no,
    mobile_no,
    index,
):
    if enrollment_no:

        value = re.sub(
            r"[^A-Za-z0-9]",
            "",
            enrollment_no,
        )

        if value:
            return (
                f"trainee_{value}"
                .lower()
            )

    if mobile_no:

        value = re.sub(
            r"\D",
            "",
            mobile_no,
        )

        if value:
            return (
                f"trainee_{value}"
                .lower()
            )

    return f"trainee_{index + 1}"


# ============================================================
# PASSWORD
# ============================================================

def generate_password(
    enrollment_no,
    mobile_no,
    index,
):
    if enrollment_no:

        value = re.sub(
            r"[^A-Za-z0-9]",
            "",
            enrollment_no,
        )

        if value:
            return f"Lms@{value}"

    if mobile_no:

        value = re.sub(
            r"\D",
            "",
            mobile_no,
        )

        if value:
            return f"Lms@{value[-6:]}"

    return f"Lms@{index + 1:04d}"


# ============================================================
# DB DUPLICATES
# ============================================================

def enrollment_exists(
    db,
    enrollment_no,
):
    if not enrollment_no:
        return False

    return (
        db.query(ParticipantMaster)
        .filter(
            ParticipantMaster.enrollment_no
            == enrollment_no,
            ParticipantMaster.deleted_at.is_(None),
        )
        .first()
        is not None
    )


def username_exists(
    db,
    username,
):
    images = get_value(
        row,
        column_map,
        COLUMN_ALIASES.get("images", []),
    )

    if not username:
        return False

    return (
        db.query(ParticipantMaster)
        .filter(
            func.lower(
                func.trim(
                    ParticipantMaster.username
                )
            )
            == username.lower().strip(),
            ParticipantMaster.deleted_at.is_(None),
        )
        .first()
        is not None
    )


# ============================================================
# BUILD TRAINEE
# ============================================================

def build_trainee_data(
    row,
    column_map,
    index,
):

    participant_name = get_value(
        row,
        column_map,
        COLUMN_ALIASES["participant_name"],
    )

    enrollment_no = get_value(
        row,
        column_map,
        COLUMN_ALIASES["enrollment_no"],
    )

    centre_code = get_value(
        row,
        column_map,
        COLUMN_ALIASES["centre_code"],
    )

    batch_id = get_value(
        row,
        column_map,
        COLUMN_ALIASES["batch_id"],
    )

    gender = get_value(
        row,
        column_map,
        COLUMN_ALIASES["gender"],
    )

    age = get_int(
        get_value(
            row,
            column_map,
            COLUMN_ALIASES["age"],
        ),
        default=1,
    )

    email = get_value(
        row,
        column_map,
        COLUMN_ALIASES["email"],
    )
    if email:
        email = str(email).strip()
        email = re.sub(r"\s+", "", email).rstrip(".")
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
            email = None

    mobile_no = get_value(
        row,
        column_map,
        COLUMN_ALIASES["mobile_no"],
    )

    pin = get_value(
        row,
        column_map,
        COLUMN_ALIASES["pin"],
    )

    location = get_value(
        row,
        column_map,
        COLUMN_ALIASES["location"],
    )

    address = get_value(
        row,
        column_map,
        COLUMN_ALIASES["address"],
    )

    username = get_value(
        row,
        column_map,
        COLUMN_ALIASES["username"],
    )

    password = get_value(
        row,
        column_map,
        COLUMN_ALIASES["password"],
    )

    images = get_value(
        row,
        column_map,
        COLUMN_ALIASES.get("images", []),
    )

    if not username:
        username = generate_username(
            enrollment_no,
            mobile_no,
            index,
        )

    if not password:
        password = generate_password(
            enrollment_no,
            mobile_no,
            index,
        )

    return {
        "participant_name": participant_name,
        "enrollment_no": enrollment_no,
        "centre_code": centre_code,
        "batch_id": batch_id,
        "gender": gender,
        "age": age,
        "email": email,
        "mobile_no": mobile_no,
        "pin": pin,
        "location": location,
        "address": address,
        "username": username,
        "password": password,
        "images": images,
    }


# ============================================================
# VALIDATE ONE ROW
# ============================================================

def validate_row(
    db,
    centre_index,
    batch_index,
    trainee,
    excel_duplicates,
):
    errors = []

    participant_name = trainee["participant_name"]
    enrollment_no = trainee["enrollment_no"]
    centre_code = trainee["centre_code"]
    batch_id = trainee["batch_id"]
    username = trainee["username"]
    gender = trainee["gender"]
    age = trainee["age"]

    # --------------------------------------------------------
    # REQUIRED
    # --------------------------------------------------------

    required = {
        "Participant Name": participant_name,
        "Enrollment No": enrollment_no,
        "Centre Code": centre_code,
        "Batch ID": batch_id,
        "Username": username,
        "Password": trainee["password"],
        "Gender": gender,
        "Age": age,
    }

    for field, value in required.items():

        if value is None or value == "":
            errors.append(
                f"{field} is missing"
            )

    # --------------------------------------------------------
    # AGE
    # --------------------------------------------------------

    if age is not None:

        if age < 1 or age > 100:
            errors.append(
                f"Invalid age: {age}"
            )

    # --------------------------------------------------------
    # EXCEL DUPLICATE ENROLLMENT
    # --------------------------------------------------------

    enrollment_key = normalize_value(
        enrollment_no
    )

    if (
        enrollment_key
        and excel_duplicates["enrollment"].get(
            enrollment_key,
            0,
        ) > 1
    ):
        errors.append(
            "Duplicate enrollment number inside Excel"
        )

    # --------------------------------------------------------
    # EXCEL DUPLICATE USERNAME
    # --------------------------------------------------------

    username_key = normalize_value(
        username
    )

    if (
        username_key
        and excel_duplicates["username"].get(
            username_key,
            0,
        ) > 1
    ):
        errors.append(
            "Duplicate username inside Excel"
        )

    # --------------------------------------------------------
    # DB DUPLICATE ENROLLMENT
    # --------------------------------------------------------

    if enrollment_no:

        if enrollment_exists(
            db,
            enrollment_no,
        ):
            errors.append(
                "Enrollment number already exists in DB"
            )

    # --------------------------------------------------------
    # DB DUPLICATE USERNAME
    # --------------------------------------------------------

    if username:

        if username_exists(
            db,
            username,
        ):
            errors.append(
                "Username already exists in DB"
            )

    # --------------------------------------------------------
    # CENTRE
    # --------------------------------------------------------

    centre = None

    if centre_code:

        centre = find_centre(
            centre_index,
            centre_code,
        )

        if not centre:

            errors.append(
                f"Centre mapping not found: "
                f"{centre_code}"
            )

    # --------------------------------------------------------
    # BATCH
    # --------------------------------------------------------

    batch = None

    if centre and batch_id:

        batch = find_batch(
            batch_index,
            centre,
            batch_id,
        )

        if not batch:

            errors.append(
                f"Batch mapping not found: "
                f"{batch_id} for centre: "
                f"{centre_code}"
            )

    return errors, centre, batch


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 75)
    print("              LMS TRAINEE IMPORT")
    print("=" * 75)
    print()

    if IMPORT_MODE:
        print("MODE: ACTUAL IMPORT")
        print("WARNING: DATABASE INSERT WILL BE PERFORMED")
    else:
        print("MODE: CHECK ONLY")
        print("NO DATABASE INSERT/UPDATE WILL BE PERFORMED")

    print()

    # ========================================================
    # CHECK EXCEL
    # ========================================================

    if not EXCEL_FILE.exists():

        print(
            f"ERROR: Excel file not found:\n"
            f"{EXCEL_FILE}"
        )

        return

    # ========================================================
    # READ EXCEL
    # ========================================================

    print("Reading Excel...")

    try:

        df = pd.read_excel(
            EXCEL_FILE
        )

    except Exception as e:

        print(
            f"ERROR reading Excel: {e}"
        )

        return

    df = df.dropna(
        how="all"
    )

    print(
        f"Total Excel records: {len(df)}"
    )

    # ========================================================
    # COLUMN MAP
    # ========================================================

    column_map = build_column_map(df)

    print()
    print("-" * 75)
    print("EXCEL COLUMN MAPPING")
    print("-" * 75)

    missing_columns = []
    mapping_rows = []

    for field, aliases in COLUMN_ALIASES.items():

        actual_column = find_column(
            column_map,
            aliases,
        )

        if actual_column:

            print(
                f"{field:20} -> {actual_column}"
            )

            mapping_rows.append({
                "Field": field,
                "Excel Column": actual_column,
                "Status": "FOUND",
            })

        else:

            print(
                f"{field:20} -> NOT FOUND"
            )

            mapping_rows.append({
                "Field": field,
                "Excel Column": "",
                "Status": "NOT FOUND",
            })

    # ========================================================
    # REQUIRED EXCEL COLUMNS
    # ========================================================

    required_excel_fields = [
        "participant_name",
        "enrollment_no",
        "centre_code",
        "batch_id",
        "gender",
        "age",
    ]

    for field in required_excel_fields:

        if not find_column(
            column_map,
            COLUMN_ALIASES[field],
        ):
            missing_columns.append(
                field
            )

    if missing_columns:

        print()
        print("=" * 75)
        print(
            "STOPPED - REQUIRED EXCEL COLUMNS NOT FOUND"
        )
        print("=" * 75)

        for field in missing_columns:
            print(f" - {field}")

        pd.DataFrame(
            mapping_rows
        ).to_excel(
            VALIDATION_REPORT,
            index=False,
        )

        return

    # ========================================================
    # BUILD TRAINEES
    # ========================================================

    trainees = []

    for index, row in df.iterrows():

        trainee = build_trainee_data(
            row,
            column_map,
            index,
        )

        trainee["excel_row"] = index + 2

        trainees.append(
            trainee
        )

    # ========================================================
    # DUPLICATES
    # ========================================================

    enrollment_counter = Counter()
    username_counter = Counter()

    for trainee in trainees:

        enrollment_key = normalize_value(
            trainee["enrollment_no"]
        )

        username_key = normalize_value(
            trainee["username"]
        )

        if enrollment_key:
            enrollment_counter[
                enrollment_key
            ] += 1

        if username_key:
            username_counter[
                username_key
            ] += 1

    excel_duplicates = {
        "enrollment":
            enrollment_counter,

        "username":
            username_counter,
    }

    # ========================================================
    # DB CONNECTION
    # ========================================================

    db: Session = SessionLocal()

    validation_results = []
    valid_rows = []
    total_errors = 0

    try:

        print()
        print("-" * 75)
        print("LOADING CENTRE/BATCH MASTER DATA")
        print("-" * 75)

        centre_index = build_centre_index(db)
        batch_index = build_batch_index(db)

        print(
            f"Active centres loaded : "
            f"{len(centre_index['exact'])}"
        )

        print(
            f"Centre batch groups   : "
            f"{len(batch_index)}"
        )

        # ====================================================
        # VALIDATION
        # ====================================================

        print()
        print("-" * 75)
        print("VALIDATING RECORDS")
        print("-" * 75)

        skipped_blank_batch = 0

        for index, trainee in enumerate(
            trainees
        ):

            excel_row = trainee["excel_row"]

            participant_name = (
                trainee["participant_name"]
            )

            # Skip rows where batch is missing / blank
            if not trainee.get("batch_id"):
                skipped_blank_batch += 1
                validation_results.append({
                    "Excel Row": excel_row,
                    "Participant Name": participant_name,
                    "Enrollment No": trainee["enrollment_no"],
                    "Centre Code": trainee["centre_code"],
                    "Resolved Centre ID": "",
                    "Resolved Centre Name": "",
                    "Batch": "",
                    "Resolved Batch ID": "",
                    "Username": trainee["username"],
                    "Status": "SKIPPED",
                    "Errors": "Batch is blank (skipped as requested)",
                })
                continue

            errors, centre, batch = validate_row(
                db,
                centre_index,
                batch_index,
                trainee,
                excel_duplicates,
            )

            status = (
                "VALID"
                if not errors
                else "ERROR"
            )

            if errors:

                total_errors += len(errors)

                print()
                print(
                    f"[ERROR] Row {excel_row} - "
                    f"{participant_name}"
                )

                print(
                    "        "
                    + " | ".join(errors)
                )

            else:

                valid_rows.append(
                    (
                        trainee,
                        centre,
                        batch,
                    )
                )

            validation_results.append({
                "Excel Row":
                    excel_row,

                "Participant Name":
                    participant_name,

                "Enrollment No":
                    trainee[
                        "enrollment_no"
                    ],

                "Centre Code":
                    trainee[
                        "centre_code"
                    ],

                "Resolved Centre ID":
                    (
                        centre.centre_id
                        if centre
                        else ""
                    ),

                "Resolved Centre Name":
                    (
                        centre.centre_name
                        if centre
                        else ""
                    ),

                "Batch":
                    trainee[
                        "batch_id"
                    ],

                "Resolved Batch ID":
                    (
                        batch.batch_id
                        if batch
                        else ""
                    ),

                "Username":
                    trainee[
                        "username"
                    ],

                "Status":
                    status,

                "Errors":
                    " | ".join(errors),
            })

        # ====================================================
        # SUMMARY
        # ====================================================

        valid_count = len(
            valid_rows
        )

        invalid_count = (
            len(trainees)
            - valid_count
            - skipped_blank_batch
        )

        print()
        print("=" * 75)
        print("VALIDATION SUMMARY")
        print("=" * 75)

        print(
            f"Total Records           : {len(trainees)}"
        )

        print(
            f"Valid Records           : {valid_count}"
        )

        print(
            f"Skipped (Blank Batch)   : {skipped_blank_batch}"
        )

        print(
            f"Invalid Rows (Errors)   : {invalid_count}"
        )

        print(
            f"Total Errors            : {total_errors}"
        )

        print("=" * 75)

        # ====================================================
        # VALIDATION REPORT
        # ====================================================

        report_df = pd.DataFrame(
            validation_results
        )

        report_df.to_excel(
            VALIDATION_REPORT,
            index=False,
        )

        print()
        print(
            f"Validation report created:\n"
            f"{VALIDATION_REPORT}"
        )

        # ====================================================
        # CHECK ONLY
        # ====================================================

        if not IMPORT_MODE:

            print()
            print("=" * 75)
            print("CHECK-ONLY COMPLETED SUCCESSFULLY")
            print("=" * 75)

            print(
                f"Valid records ready to import: {valid_count}"
            )

            print(
                "No participant was inserted."
            )

            print()
            print(
                "If everything looks correct, change:"
            )

            print(
                "IMPORT_MODE = True"
            )

            print(
                "and run the script again."
            )

            print("=" * 75)

            return

        if valid_count == 0:
            print("No valid rows to import.")
            return

        # ====================================================
        # ACTUAL IMPORT
        # ====================================================

        print()
        print("=" * 75)
        print("STARTING ACTUAL IMPORT")
        print("=" * 75)

        success_count = 0
        duplicate_count = 0
        failed_count = 0

        import_errors = []

        for (
            trainee,
            centre,
            batch,
        ) in valid_rows:

            excel_row = (
                trainee[
                    "excel_row"
                ]
            )

            participant_name = (
                trainee[
                    "participant_name"
                ]
            )

            print()
            print(
                f"Importing row {excel_row}: "
                f"{participant_name}"
            )

            try:

                request = (
                    WWWTraineeCreateRequest(
                        centre_code=
                            trainee[
                                "centre_code"
                            ],

                        batch_id=
                            trainee[
                                "batch_id"
                            ],

                        participant_name=
                            trainee[
                                "participant_name"
                            ],

                        enrollment_no=
                            trainee[
                                "enrollment_no"
                            ],

                        username=
                            trainee[
                                "username"
                            ],

                        password=
                            trainee[
                                "password"
                            ],

                        gender=
                            trainee[
                                "gender"
                            ],

                        age=
                            trainee[
                                "age"
                            ],

                        email=
                            trainee[
                                "email"
                            ],

                        mobile_no=
                            trainee[
                                "mobile_no"
                            ],

                        pin=
                            trainee[
                                "pin"
                            ],

                        location=
                            trainee[
                                "location"
                            ],

                        address=
                            trainee[
                                "address"
                            ],

                        images=
                            trainee.get(
                                "images"
                            ),
                    )
                )

                result = (
                    WWWIntegrationService
                    .create_participant(
                        db=db,
                        data=request,
                    )
                )

                if (
                    result
                    == "duplicate_enrollment_no"
                ):

                    duplicate_count += 1

                    import_errors.append({
                        "Excel Row":
                            excel_row,

                        "Participant Name":
                            participant_name,

                        "Enrollment No":
                            trainee[
                                "enrollment_no"
                            ],

                        "Username":
                            trainee[
                                "username"
                            ],

                        "Error":
                            "Duplicate enrollment number",
                    })

                    print(
                        "SKIPPED - "
                        "Duplicate enrollment"
                    )

                    continue

                if (
                    result
                    == "duplicate_username"
                ):

                    duplicate_count += 1

                    import_errors.append({
                        "Excel Row":
                            excel_row,

                        "Participant Name":
                            participant_name,

                        "Enrollment No":
                            trainee[
                                "enrollment_no"
                            ],

                        "Username":
                            trainee[
                                "username"
                            ],

                        "Error":
                            "Duplicate username",
                    })

                    print(
                        "SKIPPED - "
                        "Duplicate username"
                    )

                    continue

                success_count += 1

                participant_id = getattr(
                    result,
                    "participant_id",
                    None,
                )

                if participant_id:

                    print(
                        "SUCCESS - "
                        f"Participant ID: "
                        f"{participant_id}"
                    )

                else:

                    print(
                        "SUCCESS"
                    )

            except Exception as e:

                db.rollback()

                failed_count += 1

                error_message = str(e)

                import_errors.append({
                    "Excel Row":
                        excel_row,

                    "Participant Name":
                        participant_name,

                    "Enrollment No":
                        trainee[
                            "enrollment_no"
                        ],

                    "Username":
                        trainee[
                            "username"
                        ],

                    "Error":
                        error_message,
                })

                print(
                    "FAILED"
                )

                print(
                    f"Reason: "
                    f"{error_message}"
                )

        # ====================================================
        # IMPORT ERROR REPORT
        # ====================================================

        if import_errors:

            pd.DataFrame(
                import_errors
            ).to_excel(
                IMPORT_ERROR_REPORT,
                index=False,
            )

            print()
            print(
                f"Import error report:\n"
                f"{IMPORT_ERROR_REPORT}"
            )

        # ====================================================
        # FINAL SUMMARY
        # ====================================================

        print()
        print("=" * 75)
        print("IMPORT COMPLETED")
        print("=" * 75)

        print(
            f"Total Records      : "
            f"{len(trainees)}"
        )

        print(
            f"Successfully Added : "
            f"{success_count}"
        )

        print(
            f"Duplicates         : "
            f"{duplicate_count}"
        )

        print(
            f"Failed             : "
            f"{failed_count}"
        )

        print("=" * 75)

    finally:

        db.close()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()