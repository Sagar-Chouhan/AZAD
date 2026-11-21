"""
Module progress constants shared by the mobile module and dashboard features.

The values mirror what the existing LMS already writes into
``participant_module.lock_status``.
"""

# -------------------------
# participant_module.lock_status
# -------------------------
LOCK_STATUS_LOCKED = 0
LOCK_STATUS_ACTIVE = 1
LOCK_STATUS_COMPLETED = 2

# -------------------------
# Status exposed to the app
# -------------------------
MODULE_STATUS_LOCKED = "locked"
MODULE_STATUS_ACTIVE = "active"
MODULE_STATUS_COMPLETED = "completed"

LOCK_STATUS_MAP = {
    LOCK_STATUS_LOCKED: MODULE_STATUS_LOCKED,
    LOCK_STATUS_ACTIVE: MODULE_STATUS_ACTIVE,
    LOCK_STATUS_COMPLETED: MODULE_STATUS_COMPLETED,
}

# -------------------------
# Filters
# -------------------------
DEFAULT_LANGUAGE_ID = 1

# module_masters.status / module_type.status
ACTIVE_STATUS = 1

# topic_mapping.status is a varchar
MAPPING_ACTIVE_STATUS = "1"

# -------------------------
# document_masters.doc_type
# -------------------------
DOC_TYPE_VIDEO = "Video"
DOC_TYPE_PDF = "PDF"
DOC_TYPE_PPT = "PPT"

# Topics are listed in this order within a module: watch, then present,
# then any other document, and reading material last.
DOC_TYPE_ORDER = {
    DOC_TYPE_VIDEO: 0,
    DOC_TYPE_PPT: 1,
    DOC_TYPE_PDF: 3,
}

# Anything unrecognised sits between presentations and pdfs.
DOC_TYPE_ORDER_FALLBACK = 2

# ==============================================================================
# Module Progression & Display Sequence
# ==============================================================================
# Technical Track (module_type == 1):
# 1. Learner's license (parent_id: 1)
# 2. Permanent license (parent_id: 18)
# 3. On road (parent_id: 5)
# 4. Self driving (parent_id: 22)
#
# Non-Technical Track (module_type == 2):
# 1. Gender & Patriarchy (parent_id: 9)   - visible before SRHR
# 2. SRHR (parent_id: 26)
# 3. Communication (parent_id: 30)         - visible before Work readiness
# 4. Work readiness (parent_id: 13)
# ==============================================================================

PARENT_ID_SEQUENCE_MAP = {
    # Technical (Track 1)
    1: 1,   # Learner's license
    18: 2,  # Permanent license
    5: 3,   # On road
    22: 4,  # Self driving
    # Non-Technical (Track 2)
    9: 11,  # Gender & Patriarchy (visible before SRHR)
    26: 12, # SRHR
    30: 13, # Communication (visible before Work readiness)
    13: 14, # Work readiness / Spoken English
}


def get_module_sort_rank(parent_id=None, module_name=None) -> int:
    """
    Returns the designated sequence rank for a module:
    Technical: 1 (LL), 2 (PL), 3 (On-road), 4 (Self-drive)
    Non-Technical: 11 (Gender & Patriarchy), 12 (SRHR), 13 (Communication), 14 (Work readiness)
    """
    if parent_id is not None:
        try:
            pid = int(parent_id)
            if pid in PARENT_ID_SEQUENCE_MAP:
                return PARENT_ID_SEQUENCE_MAP[pid]
        except (ValueError, TypeError):
            pass

    if not module_name:
        return 999

    name_lower = str(module_name).lower().strip()

    # Technical Sequence Keywords
    # 1. Learner's license
    if any(k in name_lower for k in ["learn", "llr", "ll handbook", "লার্নিং", "லர்னிங்"]):
        return 1
    # 2. Permanent license
    if any(k in name_lower for k in ["permanent", "পার্মানেন্ট", "பெர்மனென்ட்"]) or name_lower.startswith("pl"):
        return 2
    # 3. On road
    if any(k in name_lower for k in ["on-road", "on road", "অন-রোড", "சாலை"]):
        return 3
    # 4. Self driving / Self drive
    if any(k in name_lower for k in ["self-drive", "self drive", "self driving", "safe driving", "সেলফ", "செல்ஃப்"]):
        return 4

    # Non-Technical Sequence Keywords
    # 1. Gender & Patriarchy (visible before SRHR)
    if any(k in name_lower for k in ["gender", "patriarch", "পিতৃতন্ত্র", "பாலினம்"]):
        return 11
    # 2. SRHR
    if any(k in name_lower for k in ["srhr", "reproductive", "sexual", "স্বাস্থ্য", "ஆரோக்கியம்"]):
        return 12
    # 3. Communication (visible before Work readiness)
    if any(k in name_lower for k in ["communication", "কমিউনিকেশন", "கம்யூனிகேஷன்"]):
        return 13
    # 4. Work readiness / Spoken English / Job interview
    if any(k in name_lower for k in ["work readiness", "readiness", "interview", "spoken english", "english", "ইংরেজি", "ஆங்கிலம்"]):
        return 14

    return 999


def build_module_order_case(module_model):
    """
    SQLAlchemy CASE expression for ordering queries that join or select from ModuleMaster.
    """
    from sqlalchemy import case, func, or_

    return case(
        # Technical
        (or_(module_model.parent_id == 1, func.lower(module_model.module_name).like("%learn%")), 1),
        (or_(module_model.parent_id == 18, func.lower(module_model.module_name).like("%permanent%")), 2),
        (
            or_(
                module_model.parent_id == 5,
                func.lower(module_model.module_name).like("%on-road%"),
                func.lower(module_model.module_name).like("%on road%"),
            ),
            3,
        ),
        (or_(module_model.parent_id == 22, func.lower(module_model.module_name).like("%self%")), 4),
        # Non-Technical
        (
            or_(
                module_model.parent_id == 9,
                func.lower(module_model.module_name).like("%gender%"),
                func.lower(module_model.module_name).like("%patriarch%"),
            ),
            11,
        ),
        (
            or_(
                module_model.parent_id == 26,
                func.lower(module_model.module_name).like("%srhr%"),
                func.lower(module_model.module_name).like("%reproductive%"),
            ),
            12,
        ),
        (or_(module_model.parent_id == 30, func.lower(module_model.module_name).like("%communication%")), 13),
        (
            or_(
                module_model.parent_id == 13,
                func.lower(module_model.module_name).like("%readiness%"),
                func.lower(module_model.module_name).like("%interview%"),
                func.lower(module_model.module_name).like("%spoken%"),
                func.lower(module_model.module_name).like("%english%"),
            ),
            14,
        ),
        else_=999,
    )


def build_module_group_order_case(module_model):
    """
    SQLAlchemy CASE expression for queries grouping strictly by module_model.parent_id.
    """
    from sqlalchemy import case

    return case(
        (module_model.parent_id == 1, 1),
        (module_model.parent_id == 18, 2),
        (module_model.parent_id == 5, 3),
        (module_model.parent_id == 22, 4),
        (module_model.parent_id == 9, 11),
        (module_model.parent_id == 26, 12),
        (module_model.parent_id == 30, 13),
        (module_model.parent_id == 13, 14),
        else_=999,
    )

