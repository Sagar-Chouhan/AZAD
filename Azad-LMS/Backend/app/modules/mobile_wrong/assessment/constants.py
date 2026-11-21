"""
Constants for the module post-session assessment.
"""

# assessment_mapping.assessment_type
TYPE_MCQ = "MCQ"
TYPE_SCQ = "SCQ"
TYPE_DROP_BUCKET = "DB"
TYPE_MATCH_MAKING = "MM"

ALL_TYPES = [
    TYPE_MCQ,
    TYPE_SCQ,
    TYPE_DROP_BUCKET,
    TYPE_MATCH_MAKING,
]

ACTIVE = 1

# Percentage that must be scored to complete the module.
PASS_PERCENTAGE = 80.0

# Multi-answer questions are marked proportionally rather than
# all-or-nothing: every correct choice earns credit and every wrong choice
# cancels one out, floored at zero for the question.
PARTIAL_CREDIT = True
