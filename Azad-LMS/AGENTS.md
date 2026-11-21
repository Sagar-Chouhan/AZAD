# Azad LMS Project Context & Instructions

## Core Architecture
- **Backend:** FastAPI, PostgreSQL, SQLAlchemy ORM (Python 3.14 via `py -3.14`).
- **Frontend:** React (Vite), Tailwind CSS, Shadcn UI.
- **Port:** `8000` (`uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`).

## Database Standards & Known Column Names
- **`centre_masters`:** Column is `mis_center_id` in database; SQLAlchemy model uses `Column("mis_center_id", ...)` with synonym `mis_centre_id`.
  - Known Centre IDs: South Delhi (5), North Delhi (6), East Delhi (7), Jaipur (8), Chennai (9), North Kolkata (10), Azad Test (14), South Kolkata (15), West Kolkata (16).
- **Dashboard State & Location Consistency:**
  - Trainees are linked to Centres via `batch_participant -> batch_masters -> centre_masters`.
  - `ParticipantMaster.state_id` and `CentreMaster.state_id` must remain synchronized.
  - Participant 401 (`Priya Sharma`, `WWW/RJ/JH/26-27/JP/12/34`): mapped to Jaipur Center (`centre_id = 8`, `batch_id = 100` / `Batch-12`, `district_id = 8110`, `block_id = 811001`).
- **Dashboard Metrics Consistency Formula:**
  - $\text{Active Trainees (Card 3, logged in } \ge \text{1 time)} + \text{Never Logged In (Need Attention)} = \text{Total Enrolled Trainees}$
  - $\text{No Activity in 30d (Need Attention)} + \text{Active in Last 30d} = \text{Active Trainees (Card 3)}$
  - `DashboardRepository.get_active_participants`: Counts trainees with `status == "1"` who have logged in or spent time at least 1 time ever.
- **PostgreSQL Case-Sensitivity:** Table column names in PostgreSQL are lowercase.
  - In SQLAlchemy models, NEVER specify uppercase string names like `Column("Assessment_id", ...)` or `Column("Topic_name", ...)`. Always use lowercase or omit the name string argument.
  - `AssessmentMaster` has columns: `assessment_id`, `assessment_name`, `module_id`, etc.
  - `AssessmentMapping` has `assessment_type` (lowercase).
  - `TopicMaster` has `topic_name` and `is_active` (lowercase).

## Trainee Import Guidelines (`Backend/scripts/import_lms_trainees.py`)
- Standard Excel file: `LMS_Trainee_Import_Data_CORRECTED.xlsx`.
- Image Excel file: `IMAGE_URL.xlsx`.
- **CRITICAL:** Trainees whose batch is blank/missing must NEVER be imported into the database.
- Column aliases include `Trainee Image` and `Profile Image`.
- Sanitize emails before Pydantic validation (strip whitespace, trailing dots; placeholders like `X` or `No` become `None`).

## Image Serving Architecture (S3 Bucket + Local Folder Paths)
- The system supports both direct S3 URLs and local folder paths without 404 errors.
- **Storage:** `public.participantmasters.images` contains either full S3 URLs (`https://...`) or local file paths (`/uploads/...` or `www_trainee_...`).
- **Frontend (`Frontend/src/shared/utils/mediaUrl.js`):**
  - `getParticipantImageUrl` must return `http/https` URLs directly as-is.
  - If a path contains `uploads/` or subdirectories, it should resolve to `${BASE_URL}/...` or `${BASE_URL}/uploads/...` without forcing `/participants/`.
- **Backend (`Backend/app/main.py`):**
  - `/uploads` is mounted via `MultiDirectoryStaticFiles` across `Backend/uploads` and `Backend/app/storage/app/uploads`.
- **Backend Image Resolver (`Backend/app/modules/users/participant_images.py`):**
  - `participant_image_url` preserves S3 URLs and relative paths cleanly.
  - `deduplicate_participant_images` never wipes out real images stored in the database.

