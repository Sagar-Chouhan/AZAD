# app/modules/dashboard/constants.py

# Chart Keys
STATE_WISE_PARTICIPANTS = "stateWiseParticipants"
STATE_WISE_CENTRES = "stateWiseCentres"
STATUS_DISTRIBUTION = "statusDistribution"
MODULE_WISE_ASSIGNMENTS = "moduleWiseAssignments"
GENDER_DISTRIBUTION = "genderDistribution"
MONTHLY_LOGINS = "monthlyLogins"
AGE_GROUP_DISTRIBUTION = "ageGroupDistribution"
DOCUMENT_TYPE_DISTRIBUTION = "documentTypeDistribution"
DISTRICT_WISE_PARTICIPANTS = "districtWiseParticipants"

# Performance Labels
PERFORMANCE_YET_TO_START = "YetToStart"
PERFORMANCE_POOR = "Poor"
PERFORMANCE_AVERAGE = "Average"
PERFORMANCE_GOOD = "Good"

# Performance Thresholds
GOOD_PERCENTAGE = 70
AVERAGE_PERCENTAGE = 40


# Leaderboard scoring weights (combined ranking).
# Equal weighting => combined = Average(Assessment Score %, Time Performance %),
# so neither score alone nor time alone decides the rank.
LEADERBOARD_ASSESSMENT_WEIGHT = 0.50
LEADERBOARD_LEARNING_TIME_WEIGHT = 0.50
