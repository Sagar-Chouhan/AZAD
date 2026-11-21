# Azad LMS - API Issues & PostgreSQL Migration Risks

This report provides a rigorous audit of database compatibility, route conflicts, frontend integration discrepancies, and operational risks.

## 1. Route Registration Conflicts & Double Prefixes

### 1.1 Duplicated Route Prefixes in Module and Users Routers

Two critical router prefix duplications exist in the codebase where the router defines a `prefix`, and sub-routes redundantly re-declare the same prefix:

1. **Participants Router Duplication** (`Backend/app/modules/users/router.py`):
   - `participants_router = APIRouter(prefix="/participants", ...)`
   - Line 174: `@participants_router.get("/participants/all-centres")` -> Evaluates to `/participants/participants/all-centres`
   - Line 182: `@participants_router.get("/participants/batches")` -> Evaluates to `/participants/participants/batches`
   - **Frontend Impact**: `Frontend/src/features/participant/services/ParticipantService.js` (lines 107 and 117) was hardcoded to call `/participants/participants/all-centres` and `/participants/participants/batches` to work around this bug.

2. **Module Master Router Duplication** (`Backend/app/modules/module/router.py`):
   - `router = APIRouter(prefix="/modules", ...)`
   - Line 210: `@router.get("/modules/{module_id}/post-assessments")` -> Evaluates to `/modules/modules/{module_id}/post-assessments`
   - Line 217: `@router.get("/modules/{module_id}/pre-assessments")` -> Evaluates to `/modules/modules/{module_id}/pre-assessments`
   - **Frontend Impact**: `Frontend/src/features/module/ListModule/services/ConfigurationService.js` calls `/modules/modules/${moduleId}/post-assessments` and `/modules/modules/${moduleId}/pre-assessments`.

## 2. Missing Endpoints Called by Frontend

1. **`GET /auth/me`**:
   - **Location**: `Frontend/src/api/AuthApi.js` (Line 29: `getCurrentUser`)
   - **Status**: Missing in Backend (`Backend/app/modules/auth/router.py` does not define `/me`).
   - **Severity**: Low (currently not called by active UI pages, but exported in `AuthApi.js`).

2. **`GET /dashboard/monthly-logins`**:
   - **Location**: `Frontend/src/features/dashboard/services/DashboardService.js` (Line 183)
   - **Status**: Commented out in Backend (`Backend/app/modules/dashboard/router.py` lines 352-378).
   - **Severity**: High. If the dashboard UI triggers this service function, it receives `404 Not Found`.

## 3. Database Compatibility Risks (MySQL to PostgreSQL Migration)

### 3.1 PostgreSQL Sequence Desynchronization (`setval`)
- **Finding**: In PostgreSQL, auto-incrementing primary keys use sequences (e.g., `users_id_seq`, `assessment_mapping_assessment_mapping_id_seq`).
- **Risk**: When databases are restored or migrated from MySQL with explicit primary key IDs in `INSERT` statements, PostgreSQL sequences are NOT automatically advanced.
- **Symptom**: Subsequent `INSERT` operations through SQLAlchemy fail with: `UniqueViolation: duplicate key value violates unique constraint`.
- **Mitigation**: Execute `SELECT setval(pg_get_serial_sequence('tablename', 'id'), coalesce(max(id), 1)) FROM tablename;` across all 51 active tables.

### 3.2 JSON vs JSONB Data Types
- **Finding**: `Backend/app/modules/audit_log/model.py` uses `from sqlalchemy.dialects.postgresql import JSONB` for `details`.
- **Risk**: `JSONB` is PostgreSQL-specific. It is not supported by MySQL. Any migration back to MySQL or testing on non-PostgreSQL dialects will raise an exception.

### 3.3 Case-Sensitive String Matching (`ILIKE`)
- **Finding**: Search queries across `BatchRepository`, `CentreRepository`, `CourseRepository`, `ModuleRepository`, `DocumentRepository`, `ParticipantRepository`, and `VideoRepository` explicitly use `.ilike(f'%{search}%')`.
- **Risk**: MySQL default collations are case-insensitive (`utf8mb4_general_ci`), whereas PostgreSQL `=` and `LIKE` are case-sensitive. The codebase properly uses `.ilike()`, which compiles correctly on PostgreSQL.

### 3.4 PostgreSQL-Specific Functions (`to_char`)
- **Finding**: `Backend/app/modules/dashboard/repository.py` calls `func.to_char(...)`.
- **Risk**: `to_char()` is native to PostgreSQL. In MySQL, the equivalent is `DATE_FORMAT()`. This code cannot run on MySQL without dialect adaptation.

### 3.5 Boolean vs Integer Flag Handling
- **Finding**: Columns such as `is_active` and `status` in `azadlms_dev_db.sql` are defined as `integer NOT NULL` or `varchar`, rather than PostgreSQL `BOOLEAN`.
- **Risk**: PostgreSQL does not automatically cast boolean literals (`TRUE`/`FALSE`) to integers (`1`/`0`). If a client sends boolean JSON values to an endpoint that writes directly to `is_active`, PostgreSQL will abort the transaction with a type mismatch error.

### 3.6 Legacy Laravel Tables in Database Dump
- **Finding**: The database dump `azadlms_dev_db.sql` contains 80 tables, of which 29 are unmanaged Laravel tables:
  - `cache`, `cache_locks`, `failed_jobs`, `job_batches`, `jobs`, `migrations`, `password_reset_tokens`, `personal_access_tokens`, `sessions`, `course_masters_bck`, `participant_module_bkp`, etc.
- **Status**: Unreferenced by the FastAPI application. They consume storage and indicate an incomplete cleanup from the previous Laravel PHP backend.

## 4. Frontend Integration Mismatches

| Frontend Service | Backend Route | Issue Description | Recommendation |
|---|---|---|---|
| `AuthApi.js:29` | `GET /auth/me` | Missing route on backend. Returns 404. | Implement `/auth/me` returning current user profile or remove unused export. |
| `DashboardService.js:183` | `GET /dashboard/monthly-logins` | Route is commented out in `dashboard/router.py`. Returns 404. | Uncomment route or redirect frontend to `/dashboard/monthly-logins/details`. |
| `ParticipantService.js:107` | `GET /participants/participants/all-centres` | Duplicate `/participants/participants/` prefix. | Refactor route to `/participants/all-centres` on both frontend and backend. |
| `ParticipantService.js:117` | `GET /participants/participants/batches` | Duplicate `/participants/participants/` prefix. | Refactor route to `/participants/batches` on both frontend and backend. |
| `ConfigurationService.js:210` | `GET /modules/modules/{id}/post-assessments` | Duplicate `/modules/modules/` prefix. | Refactor route to `/modules/{id}/post-assessments`. |
| `ConfigurationService.js:217` | `GET /modules/modules/{id}/pre-assessments` | Duplicate `/modules/modules/` prefix. | Refactor route to `/modules/{id}/pre-assessments`. |
