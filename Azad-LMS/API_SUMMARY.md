# Azad LMS - API Inventory Executive Summary

- **Total Endpoints Documented**: **215**
- **Total Modules / Controllers Inspected**: **30**
- **Total Database Tables in ORM**: **51**
- **Total Tables in PostgreSQL SQL Dump**: **80** (51 active, 29 legacy Laravel/backup)
- **Frontend API Instances Traced**: **207** (across 102 unique endpoint calls)

## 1. Endpoints Grouped by HTTP Method

| HTTP Method | Endpoint Count | Percentage |
|---|---|---|
| **`GET`** | 120 | 55.8% |
| **`POST`** | 46 | 21.4% |
| **`PUT`** | 26 | 12.1% |
| **`DELETE`** | 18 | 8.4% |
| **`PATCH`** | 5 | 2.3% |
| **Total** | **215** | **100.0%** |

## 2. Endpoints Grouped by Authentication Type

| Authentication Type | Count | Description |
|---|---|---|
| `Bearer Token (User JWT)` | 175 | Requires Bearer JWT / API Key |
| `Public (None)` | 21 | Publicly accessible |
| `Bearer Token (Participant JWT)` | 18 | Requires Bearer JWT / API Key |
| `API Key / Custom Token (WWW Integration)` | 1 | Requires Bearer JWT / API Key |

## 3. Endpoints Grouped by Module

| Module Name | Total Endpoints | GET | POST | PUT | DELETE | PATCH |
|---|---|---|---|---|---|---|
| `Assessment - Drop Bucket` | **11** | 5 | 1 | 4 | 1 | 0 |
| `Assessment - MCQ` | **7** | 3 | 1 | 2 | 1 | 0 |
| `Assessment - SCQ` | **7** | 3 | 1 | 2 | 1 | 0 |
| `Assessment - Uploads` | **1** | 0 | 1 | 0 | 0 | 0 |
| `Authentication` | **6** | 1 | 5 | 0 | 0 | 0 |
| `Batch Master` | **7** | 3 | 1 | 1 | 1 | 1 |
| `Centres` | **9** | 5 | 1 | 1 | 1 | 1 |
| `Courses` | **5** | 4 | 0 | 1 | 0 | 0 |
| `Dashboard` | **15** | 15 | 0 | 0 | 0 | 0 |
| `District Masters` | **5** | 2 | 1 | 1 | 1 | 0 |
| `Document Management` | **11** | 7 | 2 | 1 | 1 | 0 |
| `Match Making` | **20** | 8 | 4 | 4 | 4 | 0 |
| `Mobile Activity` | **4** | 1 | 3 | 0 | 0 | 0 |
| `Mobile Assessment` | **2** | 1 | 1 | 0 | 0 | 0 |
| `Mobile Authentication` | **7** | 1 | 6 | 0 | 0 | 0 |
| `Mobile Dashboard` | **2** | 2 | 0 | 0 | 0 | 0 |
| `Mobile Feedback` | **3** | 2 | 1 | 0 | 0 | 0 |
| `Mobile Media` | **3** | 3 | 0 | 0 | 0 | 0 |
| `Mobile Module` | **4** | 4 | 0 | 0 | 0 | 0 |
| `Mobile Profile` | **1** | 0 | 1 | 0 | 0 | 0 |
| `Module Master` | **24** | 14 | 5 | 1 | 1 | 3 |
| `PDF Master` | **7** | 4 | 1 | 1 | 1 | 0 |
| `PPT Master` | **7** | 4 | 1 | 1 | 1 | 0 |
| `Participants` | **18** | 13 | 3 | 2 | 0 | 0 |
| `Reference Data` | **3** | 3 | 0 | 0 | 0 | 0 |
| `State Masters` | **5** | 2 | 1 | 1 | 1 | 0 |
| `Topic Master` | **7** | 3 | 2 | 1 | 1 | 0 |
| `Users` | **6** | 3 | 1 | 1 | 1 | 0 |
| `VIDEO Master` | **7** | 4 | 1 | 1 | 1 | 0 |
| `WWW Integration` | **1** | 0 | 1 | 0 | 0 | 0 |

## 4. Key Findings and Unresolved Issues

1. **Double Prefix Bugs (4 routes)**:
   - `/participants/participants/all-centres`
   - `/participants/participants/batches`
   - `/modules/modules/{module_id}/post-assessments`
   - `/modules/modules/{module_id}/pre-assessments`
2. **Frontend-Referenced Missing Endpoints (2 routes)**:
   - `GET /auth/me` (called in `Frontend/src/api/AuthApi.js`)
   - `GET /dashboard/monthly-logins` (commented out in backend router)
3. **PostgreSQL Migration Compatibility**:
   - Codebase successfully uses PostgreSQL dialects (`JSONB`, `func.to_char`, `.ilike()`).
   - Sequence desynchronization risk on primary keys requires `setval()` verification.
   - 29 legacy Laravel tables remain in the database dump.

## 5. Generated Documentation Artifacts

- [`API_INVENTORY.md`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/API_INVENTORY.md) — Complete 215-endpoint inventory grouped by module.
- [`API_INVENTORY.csv`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/API_INVENTORY.csv) — Spreadsheet inventory with method, path, auth, handler, tables, status.
- [`API_DATABASE_MAPPING.md`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/API_DATABASE_MAPPING.md) — Endpoint-to-table/column dependency mapping.
- [`API_MIGRATION_RISKS.md`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/API_MIGRATION_RISKS.md) — PostgreSQL compatibility and frontend issues.
- [`API_SUMMARY.md`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/API_SUMMARY.md) — High-level metric summary.
