# Azad LMS - Complete API Inventory

Generated from static and AST inspection of the backend codebase (`Backend/app`) and frontend client (`Frontend/src`).

## 1. Architectural Overview

- **Backend Framework**: FastAPI 0.139.1 (Python 3.14+)
- **Database ORM**: SQLAlchemy 2.0 with Declarative Models
- **Database Engine**: PostgreSQL (`postgresql+psycopg2://`)
- **Validation**: Pydantic v2
- **Entry Point**: `Backend/app/main.py`
- **Static File Mount**: `/uploads` (`MultiDirStaticFiles` across 7 storage directories)
- **Frontend Framework**: React 18 + Vite (Axios centralized in `Frontend/src/api/Api.js`)
- **Total Endpoints Documented**: 215

## 2. Table of Contents

- [Assessment - Drop Bucket](#assessment---drop-bucket) (11 endpoints)
- [Assessment - MCQ](#assessment---mcq) (7 endpoints)
- [Assessment - SCQ](#assessment---scq) (7 endpoints)
- [Assessment - Uploads](#assessment---uploads) (1 endpoints)
- [Authentication](#authentication) (6 endpoints)
- [Batch Master](#batch-master) (7 endpoints)
- [Centres](#centres) (9 endpoints)
- [Courses](#courses) (5 endpoints)
- [Dashboard](#dashboard) (15 endpoints)
- [District Masters](#district-masters) (5 endpoints)
- [Document Management](#document-management) (11 endpoints)
- [Match Making](#match-making) (20 endpoints)
- [Mobile Activity](#mobile-activity) (4 endpoints)
- [Mobile Assessment](#mobile-assessment) (2 endpoints)
- [Mobile Authentication](#mobile-authentication) (7 endpoints)
- [Mobile Dashboard](#mobile-dashboard) (2 endpoints)
- [Mobile Feedback](#mobile-feedback) (3 endpoints)
- [Mobile Media](#mobile-media) (3 endpoints)
- [Mobile Module](#mobile-module) (4 endpoints)
- [Mobile Profile](#mobile-profile) (1 endpoints)
- [Module Master](#module-master) (24 endpoints)
- [PDF Master](#pdf-master) (7 endpoints)
- [PPT Master](#ppt-master) (7 endpoints)
- [Participants](#participants) (18 endpoints)
- [Reference Data](#reference-data) (3 endpoints)
- [State Masters](#state-masters) (5 endpoints)
- [Topic Master](#topic-master) (7 endpoints)
- [Users](#users) (6 endpoints)
- [VIDEO Master](#video-master) (7 endpoints)
- [WWW Integration](#www-integration) (1 endpoints)

---

## Assessment - Drop Bucket

Total endpoints in module: **11**

### `GET` /drop-buckets/

- **Summary**: Get All Drop Buckets
- **Router / Handler**: [`get_all`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/controller/drop_bucket_controller.py#L21) in `Backend\app\modules\assessment\controller\drop_bucket_controller.py` (Line 21)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `any` | No | `None` | - |
| `search` | `any` | No | `None` | - |
| `page` | `integer` | No | `1` | - |
| `limit` | `integer` | No | `10` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: Yes
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\DropBucket\services\DropBucketServices.js` (Line 7)
  - Snippet: `API.get("/drop-buckets/", { params }); //   return response.data; // };  /`
- File: `features\assessment\DropBucket\services\DropBucketServices.js` (Line 97)
  - Snippet: `API.get(         "/drop-buckets/",         {             params,         }     );  `

---

### `GET` /drop-buckets/{parent_id}/all

- **Summary**: Get Drop Bucket with all languages' buckets
- **Router / Handler**: [`get_all_languages`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/controller/drop_bucket_controller.py#L47) in `Backend\app\modules\assessment\controller\drop_bucket_controller.py` (Line 47)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `parent_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\DropBucket\services\DropBucketServices.js` (Line 140)
  - Snippet: `API.get(         `/drop-buckets/${parentId}/all`     );      return response.data; };  /* ========`

---

### `PUT` /drop-buckets/{parent_id}/all

- **Summary**: Bulk update Drop Bucket across all languages
- **Router / Handler**: [`bulk_update`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/controller/drop_bucket_controller.py#L57) in `Backend\app\modules\assessment\controller\drop_bucket_controller.py` (Line 57)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `parent_id` | `integer` | Yes | - |

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `DropBucketBulkUpdate`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `drop_bucket_question_title` | `string` | Yes | `None` | - |
| `drop_bucket_question_description` | `any` | No | `None` | - |
| `image_url` | `any` | No | `None` | - |
| `marks` | `any` | Yes | `None` | - |
| `status` | `integer` | Yes | `None` | - |
| `buckets` | `array` | No | `[]` | - |

**Example Request Payload:**
```json
{
  "drop_bucket_question_title": "sample_drop_bucket_question_title",
  "drop_bucket_question_description": "sample_drop_bucket_question_description",
  "image_url": "sample_image_url",
  "marks": "sample_marks",
  "status": 1,
  "buckets": []
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `UPDATE`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\DropBucket\services\DropBucketServices.js` (Line 153)
  - Snippet: `API.put(         `/drop-buckets/${parentId}/all`,         payload     );      return response.data`

---

### `GET` /drop-buckets/{drop_bucket_id}/items

- **Summary**: Get all items of a question across its buckets
- **Router / Handler**: [`get_question_items`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/controller/drop_bucket_controller.py#L113) in `Backend\app\modules\assessment\controller\drop_bucket_controller.py` (Line 113)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `drop_bucket_id` | `integer` | Yes | - |

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `integer` | No | `1` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `drop_buckets`
- **SQLAlchemy Models**: `DropBucket`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `drop_buckets.bucket_id`, `drop_buckets.drop_bucket_id`, `drop_buckets.language_id`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\DropBucket\services\DropBucketServices.js` (Line 246)
  - Snippet: `API.get(         `/drop-buckets/${dropBucketId}/items`,         {             params: { language_id:`

---

### `GET` /drop-buckets/{parent_id}

- **Summary**: Get Drop Bucket by Parent & Language
- **Router / Handler**: [`get_by_id`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/controller/drop_bucket_controller.py#L35) in `Backend\app\modules\assessment\controller\drop_bucket_controller.py` (Line 35)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `parent_id` | `integer` | Yes | - |

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `integer` | Yes | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `DropBucketResponse`

**Example Success Response:**
```json
{
  "parent_id": 1,
  "drop_bucket_question_title": "sample_drop_bucket_question_title",
  "drop_bucket_question_description": "sample_drop_bucket_question_description",
  "image_url": "sample_image_url",
  "marks": "sample_marks",
  "status": 1,
  "language_id": 1,
  "drop_bucket_id": "sample_drop_bucket_id",
  "created_at": "sample_created_at",
  "updated_at": "sample_updated_at",
  "deleted_at": "sample_deleted_at",
  "bucket_name": "sample_bucket_name",
  "bucket_image": "sample_bucket_image",
  "buckets": [],
  "is_translation": true
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\DropBucket\services\DropBucketServices.js` (Line 15)
  - Snippet: `API.get(`/drop-buckets/${parentId}`, { //     params: { language_id: Number(languageI`
- File: `features\assessment\DropBucket\services\DropBucketServices.js` (Line 120)
  - Snippet: `API.get(         `/drop-buckets/${parentId}`,         {             params: {                 `

---

### `POST` /drop-buckets/

- **Summary**: Create Drop Bucket
- **Router / Handler**: [`create`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/controller/drop_bucket_controller.py#L69) in `Backend\app\modules\assessment\controller\drop_bucket_controller.py` (Line 69)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `DropBucketCreate`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `parent_id` | `integer` | No | `0` | - |
| `drop_bucket_question_title` | `string` | Yes | `None` | - |
| `drop_bucket_question_description` | `any` | No | `None` | - |
| `image_url` | `any` | No | `None` | - |
| `marks` | `any` | Yes | `None` | - |
| `status` | `integer` | Yes | `None` | - |
| `language_id` | `integer` | Yes | `None` | - |
| `buckets` | `array` | No | `[]` | - |

**Example Request Payload:**
```json
{
  "parent_id": 1,
  "drop_bucket_question_title": "sample_drop_bucket_question_title",
  "drop_bucket_question_description": "sample_drop_bucket_question_description",
  "image_url": "sample_image_url",
  "marks": "sample_marks",
  "status": 1,
  "language_id": 1,
  "buckets": []
}
```

#### Responses

- **Success Status Code**: `201`
- **Response Model**: `DropBucketResponse`

**Example Success Response:**
```json
{
  "parent_id": 1,
  "drop_bucket_question_title": "sample_drop_bucket_question_title",
  "drop_bucket_question_description": "sample_drop_bucket_question_description",
  "image_url": "sample_image_url",
  "marks": "sample_marks",
  "status": 1,
  "language_id": 1,
  "drop_bucket_id": "sample_drop_bucket_id",
  "created_at": "sample_created_at",
  "updated_at": "sample_updated_at",
  "deleted_at": "sample_deleted_at",
  "bucket_name": "sample_bucket_name",
  "bucket_image": "sample_bucket_image",
  "buckets": [],
  "is_translation": true
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `INSERT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\DropBucket\services\DropBucketServices.js` (Line 36)
  - Snippet: `API.post("/drop-buckets/", payload); //   return response.data; // };  // e`
- File: `features\assessment\DropBucket\services\DropBucketServices.js` (Line 190)
  - Snippet: `API.post(         "/drop-buckets/",         payload     );       return response.dat`

---

### `PUT` /drop-buckets/{drop_bucket_id}

- **Summary**: Update Drop Bucket
- **Router / Handler**: [`update`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/controller/drop_bucket_controller.py#L79) in `Backend\app\modules\assessment\controller\drop_bucket_controller.py` (Line 79)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `drop_bucket_id` | `integer` | Yes | - |

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `DropBucketUpdate`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `drop_bucket_question_title` | `any` | No | `None` | - |
| `drop_bucket_question_description` | `any` | No | `None` | - |
| `image_url` | `any` | No | `None` | - |
| `marks` | `any` | No | `None` | - |
| `status` | `any` | No | `None` | - |
| `language_id` | `any` | No | `None` | - |
| `buckets` | `any` | No | `None` | - |

**Example Request Payload:**
```json
{
  "drop_bucket_question_title": "sample_drop_bucket_question_title",
  "drop_bucket_question_description": "sample_drop_bucket_question_description",
  "image_url": "sample_image_url",
  "marks": "sample_marks",
  "status": "sample_status",
  "language_id": "sample_language_id",
  "buckets": "sample_buckets"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `DropBucketResponse`

**Example Success Response:**
```json
{
  "parent_id": 1,
  "drop_bucket_question_title": "sample_drop_bucket_question_title",
  "drop_bucket_question_description": "sample_drop_bucket_question_description",
  "image_url": "sample_image_url",
  "marks": "sample_marks",
  "status": 1,
  "language_id": 1,
  "drop_bucket_id": "sample_drop_bucket_id",
  "created_at": "sample_created_at",
  "updated_at": "sample_updated_at",
  "deleted_at": "sample_deleted_at",
  "bucket_name": "sample_bucket_name",
  "bucket_image": "sample_bucket_image",
  "buckets": [],
  "is_translation": true
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `drop_buckets`
- **SQLAlchemy Models**: `DropBucket`
- **Operations Performed**: `UPDATE`
- **Key Columns Referenced**: `drop_buckets.bucket_id`, `drop_buckets.drop_bucket_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\DropBucket\services\DropBucketServices.js` (Line 41)
  - Snippet: `API.put(`/drop-buckets/${dropBucketId}`, payload); //   return response.data; // };  // e`
- File: `features\assessment\DropBucket\services\DropBucketServices.js` (Line 210)
  - Snippet: `API.put(         `/drop-buckets/${dropBucketId}`,         payload     );       return response.dat`

---

### `DELETE` /drop-buckets/{drop_bucket_id}

- **Summary**: Delete Drop Bucket
- **Router / Handler**: [`delete`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/controller/drop_bucket_controller.py#L91) in `Backend\app\modules\assessment\controller\drop_bucket_controller.py` (Line 91)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `drop_bucket_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `drop_buckets`
- **SQLAlchemy Models**: `DropBucket`
- **Operations Performed**: `DELETE`
- **Key Columns Referenced**: `drop_buckets.bucket_id`, `drop_buckets.drop_bucket_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\DropBucket\services\DropBucketServices.js` (Line 46)
  - Snippet: `API.delete(`/drop-buckets/${dropBucketId}`); //   return response.data; // };  // /* =======`
- File: `features\assessment\DropBucket\services\DropBucketServices.js` (Line 228)
  - Snippet: `API.delete(         `/drop-buckets/${dropBucketId}`     );       return response.data; };  /* ======`

---

### `GET` /drop-buckets/buckets/{bucket_id}/items

- **Summary**: Get Bucket Items
- **Router / Handler**: [`get_bucket_items`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/router/drop_bucket_route.py#L73) in `Backend\app\modules\assessment\router\drop_bucket_route.py` (Line 73)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `bucket_id` | `integer` | Yes | - |

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `integer` | No | `1` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[DropBucketItemResponse]`

**Example Success Response:**
```json
[
  {
    "bucket_id": "sample_bucket_id",
    "item_name": "sample_item_name",
    "item_image": "sample_item_image",
    "status": 1,
    "language_id": 1,
    "drop_bucket_item_id": 1,
    "created_at": "sample_created_at",
    "updated_at": "sample_updated_at"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\DropBucket\services\DropBucketServices.js` (Line 55)
  - Snippet: `API.get(`/drop-buckets/buckets/${bucketId}/items`); //   return response.data; // };  // export con`

---

### `PUT` /drop-buckets/buckets/{bucket_id}/items

- **Summary**: Update Bucket Items
- **Router / Handler**: [`update_bucket_items`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/router/drop_bucket_route.py#L91) in `Backend\app\modules\assessment\router\drop_bucket_route.py` (Line 91)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `bucket_id` | `integer` | Yes | - |

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `DropBucketItemsUpdateRequest`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `items` | `array` | Yes | `None` | - |

**Example Request Payload:**
```json
{
  "items": []
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[DropBucketItemResponse]`

**Example Success Response:**
```json
[
  {
    "bucket_id": "sample_bucket_id",
    "item_name": "sample_item_name",
    "item_image": "sample_item_image",
    "status": 1,
    "language_id": 1,
    "drop_bucket_item_id": 1,
    "created_at": "sample_created_at",
    "updated_at": "sample_updated_at"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `UPDATE`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\DropBucket\services\DropBucketServices.js` (Line 300)
  - Snippet: `API.put(         `/drop-buckets/buckets/${bucketId}/items`,         payload     );       return resp`

---

### `PUT` /drop-buckets/{parent_id}/translation

- **Summary**: Save Drop Bucket Translation
- **Router / Handler**: [`save_translation`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/router/drop_bucket_route.py#L109) in `Backend\app\modules\assessment\router\drop_bucket_route.py` (Line 109)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `parent_id` | `integer` | Yes | - |

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `DropBucketCreate`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `parent_id` | `integer` | No | `0` | - |
| `drop_bucket_question_title` | `string` | Yes | `None` | - |
| `drop_bucket_question_description` | `any` | No | `None` | - |
| `image_url` | `any` | No | `None` | - |
| `marks` | `any` | Yes | `None` | - |
| `status` | `integer` | Yes | `None` | - |
| `language_id` | `integer` | Yes | `None` | - |
| `buckets` | `array` | No | `[]` | - |

**Example Request Payload:**
```json
{
  "parent_id": 1,
  "drop_bucket_question_title": "sample_drop_bucket_question_title",
  "drop_bucket_question_description": "sample_drop_bucket_question_description",
  "image_url": "sample_image_url",
  "marks": "sample_marks",
  "status": 1,
  "language_id": 1,
  "buckets": []
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `UPDATE`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\DropBucket\services\DropBucketServices.js` (Line 172)
  - Snippet: `API.put(         `/drop-buckets/${parentId}/translation`,         payload     );       return respon`

---

## Assessment - MCQ

Total endpoints in module: **7**

### `GET` /mcqs/

- **Summary**: Get all MCQs
- **Router / Handler**: [`get_all_mcqs`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/controller/mcq_controller.py#L17) in `Backend\app\modules\assessment\controller\mcq_controller.py` (Line 17)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `any` | No | `None` | - |
| `search` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\MCQ\services\MCQServices.js` (Line 27)
  - Snippet: `API.get("/mcqs", {         params,     });      return response.d`

---

### `GET` /mcqs/export

- **Summary**: Export MCQs
- **Router / Handler**: [`export_mcqs`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/controller/mcq_controller.py#L73) in `Backend\app\modules\assessment\controller\mcq_controller.py` (Line 73)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `any` | No | `None` | - |
| `search` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\MCQ\services\MCQServices.js` (Line 107)
  - Snippet: `API.get("/mcqs/export", {         params,         responseType: "blob", `

---

### `GET` /mcqs/{parent_id}

- **Summary**: Get MCQ Translation
- **Router / Handler**: [`get_mcq`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/controller/mcq_controller.py#L29) in `Backend\app\modules\assessment\controller\mcq_controller.py` (Line 29)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `parent_id` | `integer` | Yes | - |

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `integer` | No | `1` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\MCQ\services\MCQServices.js` (Line 40)
  - Snippet: `API.get(`/mcqs/${parentId}`, {         params: {             language_id: lan`
- File: `features\assessment\MCQ\services\MCQServices.js` (Line 65)
  - Snippet: `API.get(`/mcqs/${parentId}`, {         params: {             language_id: lan`

---

### `PUT` /mcqs/{parent_id}/translation

- **Summary**: Create / Update MCQ Translation
- **Router / Handler**: [`save_translation`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/controller/mcq_controller.py#L85) in `Backend\app\modules\assessment\controller\mcq_controller.py` (Line 85)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `parent_id` | `integer` | Yes | - |

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `McqCreate`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `parent_id` | `any` | No | `None` | - |
| `mcq_question_title` | `string` | Yes | `None` | - |
| `mcq_question_description` | `any` | No | `None` | - |
| `image_url` | `any` | No | `None` | - |
| `marks` | `any` | Yes | `None` | - |
| `status` | `integer` | No | `1` | - |
| `language_id` | `integer` | Yes | `None` | - |
| `options` | `array` | Yes | `None` | - |

**Example Request Payload:**
```json
{
  "parent_id": "sample_parent_id",
  "mcq_question_title": "sample_mcq_question_title",
  "mcq_question_description": "sample_mcq_question_description",
  "image_url": "sample_image_url",
  "marks": "sample_marks",
  "status": 1,
  "language_id": 1,
  "options": []
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `UPDATE`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\MCQ\services\MCQServices.js` (Line 55)
  - Snippet: `API.put(         `/mcqs/${parentId}/translation`,         payload     );      return response.data`

---

### `POST` /mcqs/

- **Summary**: Create MCQ
- **Router / Handler**: [`create_mcq`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/controller/mcq_controller.py#L41) in `Backend\app\modules\assessment\controller\mcq_controller.py` (Line 41)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `McqCreate`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `parent_id` | `any` | No | `None` | - |
| `mcq_question_title` | `string` | Yes | `None` | - |
| `mcq_question_description` | `any` | No | `None` | - |
| `image_url` | `any` | No | `None` | - |
| `marks` | `any` | Yes | `None` | - |
| `status` | `integer` | No | `1` | - |
| `language_id` | `integer` | Yes | `None` | - |
| `options` | `array` | Yes | `None` | - |

**Example Request Payload:**
```json
{
  "parent_id": "sample_parent_id",
  "mcq_question_title": "sample_mcq_question_title",
  "mcq_question_description": "sample_mcq_question_description",
  "image_url": "sample_image_url",
  "marks": "sample_marks",
  "status": 1,
  "language_id": 1,
  "options": []
}
```

#### Responses

- **Success Status Code**: `201`
- **Response Model**: `McqResponse`

**Example Success Response:**
```json
{
  "parent_id": "sample_parent_id",
  "mcq_question_title": "sample_mcq_question_title",
  "mcq_question_description": "sample_mcq_question_description",
  "image_url": "sample_image_url",
  "marks": "sample_marks",
  "status": 1,
  "language_id": 1,
  "mcq_id": 1,
  "created_at": "sample_created_at",
  "updated_at": "sample_updated_at",
  "options": []
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `INSERT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\MCQ\services\MCQServices.js` (Line 79)
  - Snippet: `API.post("/mcqs/", payload);      return response.data; }; /* =====`

---

### `PUT` /mcqs/{mcq_id}

- **Summary**: Update MCQ
- **Router / Handler**: [`update_mcq`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/controller/mcq_controller.py#L51) in `Backend\app\modules\assessment\controller\mcq_controller.py` (Line 51)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `mcq_id` | `integer` | Yes | - |

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `McqUpdate`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `parent_id` | `any` | No | `None` | - |
| `mcq_question_title` | `any` | No | `None` | - |
| `mcq_question_description` | `any` | No | `None` | - |
| `image_url` | `any` | No | `None` | - |
| `marks` | `any` | No | `None` | - |
| `status` | `any` | No | `None` | - |
| `language_id` | `any` | No | `None` | - |
| `options` | `any` | No | `None` | - |

**Example Request Payload:**
```json
{
  "parent_id": "sample_parent_id",
  "mcq_question_title": "sample_mcq_question_title",
  "mcq_question_description": "sample_mcq_question_description",
  "image_url": "sample_image_url",
  "marks": "sample_marks",
  "status": "sample_status",
  "language_id": "sample_language_id",
  "options": "sample_options"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `McqResponse`

**Example Success Response:**
```json
{
  "parent_id": "sample_parent_id",
  "mcq_question_title": "sample_mcq_question_title",
  "mcq_question_description": "sample_mcq_question_description",
  "image_url": "sample_image_url",
  "marks": "sample_marks",
  "status": 1,
  "language_id": 1,
  "mcq_id": 1,
  "created_at": "sample_created_at",
  "updated_at": "sample_updated_at",
  "options": []
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `UPDATE`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\MCQ\services\MCQServices.js` (Line 94)
  - Snippet: `API.put(`/mcqs/${mcqId}`, payload, {         headers: {             "Conte`

---

### `DELETE` /mcqs/{mcq_id}

- **Summary**: Delete MCQ
- **Router / Handler**: [`delete_mcq`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/controller/mcq_controller.py#L63) in `Backend\app\modules\assessment\controller\mcq_controller.py` (Line 63)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `mcq_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `DELETE`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\MCQ\services\MCQServices.js` (Line 88)
  - Snippet: `API.delete(`/mcqs/${mcqId}`);      return response.data; };  export const upd`

---

## Assessment - SCQ

Total endpoints in module: **7**

### `GET` /scqs/export

- **Summary**: Export SCQs
- **Router / Handler**: [`export_scqs`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/controller/scq_controller.py#L110) in `Backend\app\modules\assessment\controller\scq_controller.py` (Line 110)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `any` | No | `None` | - |
| `search` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\SCQ\services\SCQServices.js` (Line 185)
  - Snippet: `Api.get(             "/scqs/export",             {                 params,           `

---

### `GET` /scqs/

- **Summary**: Get All SCQs
- **Router / Handler**: [`get_all_scqs`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/controller/scq_controller.py#L24) in `Backend\app\modules\assessment\controller\scq_controller.py` (Line 24)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `any` | No | `None` | - |
| `search` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\SCQ\services\SCQServices.js` (Line 33)
  - Snippet: `Api.get(             "/scqs",             {                 params,           `

---

### `PUT` /scqs/{parent_id}/translation

- **Summary**: Create / Update SCQ Translation
- **Router / Handler**: [`save_translation`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/controller/scq_controller.py#L146) in `Backend\app\modules\assessment\controller\scq_controller.py` (Line 146)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `parent_id` | `integer` | Yes | - |

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `ScqCreate`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `parent_id` | `any` | No | `None` | - |
| `scq_question_title` | `string` | Yes | `None` | - |
| `scq_question_description` | `any` | No | `None` | - |
| `image_url` | `any` | No | `None` | - |
| `marks` | `any` | Yes | `None` | - |
| `status` | `integer` | No | `1` | - |
| `language_id` | `integer` | Yes | `None` | - |
| `options` | `array` | Yes | `None` | - |

**Example Request Payload:**
```json
{
  "parent_id": "sample_parent_id",
  "scq_question_title": "sample_scq_question_title",
  "scq_question_description": "sample_scq_question_description",
  "image_url": "sample_image_url",
  "marks": "sample_marks",
  "status": 1,
  "language_id": 1,
  "options": []
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `UPDATE`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\SCQ\services\SCQServices.js` (Line 165)
  - Snippet: `Api.put(         `/scqs/${parentId}/translation`,         payload,         {             headers: `

---

### `GET` /scqs/{parent_id}

- **Summary**: Get SCQ by Parent & Language
- **Router / Handler**: [`get_scq`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/controller/scq_controller.py#L44) in `Backend\app\modules\assessment\controller\scq_controller.py` (Line 44)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `parent_id` | `integer` | Yes | - |

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `integer` | No | `1` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\SCQ\services\SCQServices.js` (Line 54)
  - Snippet: `Api.get(             `/scqs/${parentId}`,             {                 params: {         `
- File: `features\assessment\SCQ\services\SCQServices.js` (Line 142)
  - Snippet: `Api.get(             `/scqs/${parentId}`,             {                 params: {         `

---

### `POST` /scqs/

- **Summary**: Create SCQ
- **Router / Handler**: [`create_scq`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/controller/scq_controller.py#L62) in `Backend\app\modules\assessment\controller\scq_controller.py` (Line 62)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `ScqCreate`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `parent_id` | `any` | No | `None` | - |
| `scq_question_title` | `string` | Yes | `None` | - |
| `scq_question_description` | `any` | No | `None` | - |
| `image_url` | `any` | No | `None` | - |
| `marks` | `any` | Yes | `None` | - |
| `status` | `integer` | No | `1` | - |
| `language_id` | `integer` | Yes | `None` | - |
| `options` | `array` | Yes | `None` | - |

**Example Request Payload:**
```json
{
  "parent_id": "sample_parent_id",
  "scq_question_title": "sample_scq_question_title",
  "scq_question_description": "sample_scq_question_description",
  "image_url": "sample_image_url",
  "marks": "sample_marks",
  "status": 1,
  "language_id": 1,
  "options": []
}
```

#### Responses

- **Success Status Code**: `201`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `INSERT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\SCQ\services\SCQServices.js` (Line 75)
  - Snippet: `Api.post(         "/scqs/",         payload,         {             headers: `

---

### `PUT` /scqs/{scq_id}

- **Summary**: Update SCQ
- **Router / Handler**: [`update_scq`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/controller/scq_controller.py#L78) in `Backend\app\modules\assessment\controller\scq_controller.py` (Line 78)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `scq_id` | `integer` | Yes | - |

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `ScqUpdate`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `parent_id` | `any` | No | `None` | - |
| `scq_question_title` | `any` | No | `None` | - |
| `scq_question_description` | `any` | No | `None` | - |
| `image_url` | `any` | No | `None` | - |
| `marks` | `any` | No | `None` | - |
| `status` | `any` | No | `None` | - |
| `language_id` | `any` | No | `None` | - |
| `options` | `any` | No | `None` | - |

**Example Request Payload:**
```json
{
  "parent_id": "sample_parent_id",
  "scq_question_title": "sample_scq_question_title",
  "scq_question_description": "sample_scq_question_description",
  "image_url": "sample_image_url",
  "marks": "sample_marks",
  "status": "sample_status",
  "language_id": "sample_language_id",
  "options": "sample_options"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `UPDATE`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\SCQ\services\SCQServices.js` (Line 100)
  - Snippet: `Api.put(             `/scqs/${scqId}`,             payload,             {              `

---

### `DELETE` /scqs/{scq_id}

- **Summary**: Delete SCQ
- **Router / Handler**: [`delete_scq`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/controller/scq_controller.py#L96) in `Backend\app\modules\assessment\controller\scq_controller.py` (Line 96)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `scq_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `DELETE`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\SCQ\services\SCQServices.js` (Line 124)
  - Snippet: `Api.delete(             `/scqs/${scqId}`         );      return response.data; };   /* ===`

---

## Assessment - Uploads

Total endpoints in module: **1**

### `POST` /assessment/upload-image

- **Summary**: Upload an assessment image and return its permanent URL
- **Description**: Persist an uploaded image and return the public URL path.

Used by the MCQ / SCQ / Drop Bucket / Match Making forms so that the
stored ``image_url`` is always a real ``/uploads/...`` path and never a
client-side ``blob:`` URL.
- **Router / Handler**: [`upload_assessment_image`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/router/upload_route.py#L13) in `Backend\app\modules\assessment\router\upload_route.py` (Line 13)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `multipart/form-data`
- **Schema**: `Body_upload_assessment_image_assessment_upload_image_post`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `image` | `string` | Yes | `None` | - |

**Example Request Payload:**
```json
{
  "image": "sample_image"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `INSERT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: Yes (Multipart)

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\DropBucket\services\DropBucketServices.js` (Line 82)
  - Snippet: `API.post(         "/assessment/upload-image",         formData     );      return response.dat`
- File: `features\assessment\MatchMaking\services\MatchingMakingService.js` (Line 6)
  - Snippet: `API.post(         "/assessment/upload-image",         formData     );      return response.dat`
- File: `features\assessment\MCQ\services\MCQServices.js` (Line 13)
  - Snippet: `API.post(         "/assessment/upload-image",         formData     );      return response.dat`
- File: `features\assessment\SCQ\services\SCQServices.js` (Line 15)
  - Snippet: `Api.post(         "/assessment/upload-image",         formData     );      return response.dat`

---

## Authentication

Total endpoints in module: **6**

### `GET` /auth/captcha

- **Summary**: Get Captcha
- **Description**: Generate a new captcha.
- **Router / Handler**: [`get_captcha`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/auth/router.py#L31) in `Backend\app\modules\auth\router.py` (Line 31)
- **Authentication**: `Public (None)`
- **Allowed Roles**: Public / Open
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `404`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `api\AuthApi.js` (Line 4)
  - Snippet: `API.get("/auth/captcha");     return data; };  export const loginUser = a`

---

### `POST` /auth/login

- **Summary**: User Login
- **Description**: Authenticate user and return JWT access token.
- **Router / Handler**: [`login`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/auth/router.py#L39) in `Backend\app\modules\auth\router.py` (Line 39)
- **Authentication**: `Public (None)`
- **Allowed Roles**: Public / Open
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `LoginRequest`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `email` | `string` | Yes | `None` | - |
| `password` | `string` | Yes | `None` | - |
| `captcha_answer` | `integer` | Yes | `None` | - |
| `captcha_token` | `string` | Yes | `None` | - |

**Example Request Payload:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123",
  "captcha_answer": 1,
  "captcha_token": "sample_captcha_token"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `app__modules__auth__schema__LoginResponse`

**Example Success Response:**
```json
{
  "access_token": "sample_access_token",
  "token_type": "sample_token_type",
  "refresh_token": "sample_refresh_token",
  "user": "sample_user"
}
```

- **Possible Error Status Codes**: `400`, `404`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `INSERT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `api\AuthApi.js` (Line 9)
  - Snippet: `API.post("/auth/login", payload);     return data; };  export const refr`

---

### `POST` /auth/refresh

- **Summary**: Refresh Token
- **Router / Handler**: [`refresh_token`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/auth/router.py#L57) in `Backend\app\modules\auth\router.py` (Line 57)
- **Authentication**: `Public (None)`
- **Allowed Roles**: Public / Open
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `app__modules__auth__schema__RefreshTokenRequest`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `refresh_token` | `string` | Yes | `None` | - |

**Example Request Payload:**
```json
{
  "refresh_token": "sample_refresh_token"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `app__modules__auth__schema__RefreshTokenResponse`

**Example Success Response:**
```json
{
  "access_token": "sample_access_token",
  "refresh_token": "sample_refresh_token",
  "token_type": "sample_token_type"
}
```

- **Possible Error Status Codes**: `400`, `404`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `INSERT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `api\AuthApi.js` (Line 16)
  - Snippet: `API.post("/auth/refresh", {         refresh_token,     });      return dat`

---

### `POST` /auth/logout

- **Summary**: User Logout
- **Description**: Logout user.
Frontend should remove stored JWT tokens.
- **Router / Handler**: [`logout`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/auth/router.py#L71) in `Backend\app\modules\auth\router.py` (Line 71)
- **Authentication**: `Public (None)`
- **Allowed Roles**: Public / Open
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `LogoutResponse`

**Example Success Response:**
```json
{
  "message": "sample_message"
}
```

- **Possible Error Status Codes**: `400`, `404`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `INSERT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `api\AuthApi.js` (Line 24)
  - Snippet: `API.post("/auth/logout");     return data; };  export const getCurrentUse`

---

### `POST` /auth/forgot-password

- **Summary**: Forgot Password
- **Router / Handler**: [`forgot_password`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/auth/router.py#L89) in `Backend\app\modules\auth\router.py` (Line 89)
- **Authentication**: `Public (None)`
- **Allowed Roles**: Public / Open
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Unused by Web Frontend (no frontend service or page calls this endpoint).

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `app__modules__auth__schema__ForgotPasswordRequest`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `email` | `string` | Yes | `None` | - |
| `recaptcha_token` | `string` | Yes | `None` | - |

**Example Request Payload:**
```json
{
  "email": "user@example.com",
  "recaptcha_token": "sample_recaptcha_token"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `app__modules__auth__schema__ForgotPasswordResponse`

**Example Success Response:**
```json
{
  "message": "sample_message",
  "reset_token": "sample_reset_token"
}
```

- **Possible Error Status Codes**: `400`, `404`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `INSERT`
- **Key Columns Referenced**: `users.password`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

No matching frontend service call found in `Frontend/src` (Backend-only / Unused by web frontend).

---

### `POST` /auth/reset-password

- **Summary**: Reset Password
- **Description**: Reset password using a valid reset token.
- **Router / Handler**: [`reset_password`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/auth/router.py#L104) in `Backend\app\modules\auth\router.py` (Line 104)
- **Authentication**: `Public (None)`
- **Allowed Roles**: Public / Open
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Unused by Web Frontend (no frontend service or page calls this endpoint).

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `app__modules__auth__schema__ResetPasswordRequest`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `reset_token` | `string` | Yes | `None` | - |
| `new_password` | `string` | Yes | `None` | - |
| `confirm_password` | `string` | Yes | `None` | - |

**Example Request Payload:**
```json
{
  "reset_token": "sample_reset_token",
  "new_password": "SecurePassword123",
  "confirm_password": "SecurePassword123"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `ResetPasswordResponse`

**Example Success Response:**
```json
{
  "message": "sample_message"
}
```

- **Possible Error Status Codes**: `400`, `404`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `INSERT`
- **Key Columns Referenced**: `users.id`, `users.password`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

No matching frontend service call found in `Frontend/src` (Backend-only / Unused by web frontend).

---

## Batch Master

Total endpoints in module: **7**

### `GET` /batches

- **Summary**: Get Batches
- **Router / Handler**: [`get_batches`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/batch/router.py#L35) in `Backend\app\modules\batch\router.py` (Line 35)
- **Authentication**: `Public (None)`
- **Allowed Roles**: Public / Open
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `state_id` | `any` | No | `None` | - |
| `district_id` | `any` | No | `None` | - |
| `status_filter` | `any` | No | `None` | - |
| `search` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[BatchListResponse]`

**Example Success Response:**
```json
[
  {
    "batch_id": 1,
    "batch_name": "sample_batch_name",
    "centre_name": "sample_centre_name",
    "centre_id": "sample_centre_id",
    "state_id": "sample_state_id",
    "district_id": "sample_district_id",
    "block_id": "sample_block_id",
    "fy_year": "sample_fy_year",
    "created_by": "sample_created_by",
    "status": 1,
    "participant_count": 1
  }
]
```

- **Possible Error Status Codes**: `400`, `404`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `batch_masters`, `batch_participant`, `centre_masters`, `district_master`, `participantmasters`, `state_master`, `users`
- **SQLAlchemy Models**: `BatchMaster`, `BatchParticipant`, `CentreMaster`, `DistrictMaster`, `ParticipantMaster`, `StateMaster`, `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `batch_masters.status`, `centre_masters.district_id`, `centre_masters.state_id`, `centre_masters.status`, `district_master.status`, `participantmasters.district_id`, `participantmasters.state_id`, `participantmasters.status`, `state_master.status`, `users.id`, `users.status`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\batch\services\BatchService.js` (Line 13)
  - Snippet: `API.get('/batches', {             params: {                 ...(stat`

---

### `POST` /batches

- **Summary**: Create Batch
- **Router / Handler**: [`create_batch`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/batch/router.py#L55) in `Backend\app\modules\batch\router.py` (Line 55)
- **Authentication**: `Public (None)`
- **Allowed Roles**: Public / Open
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `BatchCreateRequest`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `batch_name` | `string` | Yes | `None` | - |
| `centre_id` | `integer` | Yes | `None` | - |
| `fy_year` | `string` | Yes | `None` | - |
| `status` | `integer` | Yes | `None` | - |

**Example Request Payload:**
```json
{
  "batch_name": "sample_batch_name",
  "centre_id": 1,
  "fy_year": "sample_fy_year",
  "status": 1
}
```

#### Responses

- **Success Status Code**: `201`
- **Response Model**: `app__modules__batch__schema__BatchResponse`

**Example Success Response:**
```json
{
  "batch_id": 1,
  "batch_name": "sample_batch_name",
  "centre_id": 1,
  "fy_year": "sample_fy_year",
  "created_by": 1,
  "status": 1,
  "created_at": "sample_created_at",
  "updated_at": "sample_updated_at"
}
```

- **Possible Error Status Codes**: `400`, `404`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `INSERT`
- **Key Columns Referenced**: `users.id`, `users.role`, `users.status`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\batch\services\BatchService.js` (Line 29)
  - Snippet: `API.post('/batches', {             batch_name: batchName,            `

---

### `GET` /batches/{batch_id}

- **Summary**: Get Batch By Id
- **Router / Handler**: [`get_batch_by_id`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/batch/router.py#L74) in `Backend\app\modules\batch\router.py` (Line 74)
- **Authentication**: `Public (None)`
- **Allowed Roles**: Public / Open
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `batch_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `BatchDetailResponse`

**Example Success Response:**
```json
{
  "batch_id": 1,
  "batch_name": "sample_batch_name",
  "state_id": 1,
  "district_id": 1,
  "block_id": 1,
  "centre_id": 1,
  "centre_name": "sample_centre_name",
  "fy_year": "sample_fy_year",
  "created_by": 1,
  "created_by_name": "sample_created_by_name",
  "status": 1,
  "created_at": "sample_created_at",
  "updated_at": "sample_updated_at"
}
```

- **Possible Error Status Codes**: `400`, `404`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `batch_masters`, `batch_participant`, `centre_masters`, `district_master`, `participantmasters`, `state_master`, `users`
- **SQLAlchemy Models**: `BatchMaster`, `BatchParticipant`, `CentreMaster`, `DistrictMaster`, `ParticipantMaster`, `StateMaster`, `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `batch_masters.batch_id`, `batch_participant.batch_id`, `users.id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\batch\services\BatchService.js` (Line 76)
  - Snippet: `API.get(`/batches/${batchId}`);         return response.data;     } catch (erro`

---

### `PUT` /batches/{batch_id}

- **Summary**: Update Batch
- **Router / Handler**: [`update_batch`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/batch/router.py#L88) in `Backend\app\modules\batch\router.py` (Line 88)
- **Authentication**: `Public (None)`
- **Allowed Roles**: Public / Open
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `batch_id` | `integer` | Yes | - |

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `BatchUpdateRequest`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `batch_name` | `string` | Yes | `None` | - |
| `centre_id` | `integer` | Yes | `None` | - |
| `fy_year` | `string` | Yes | `None` | - |
| `status` | `integer` | Yes | `None` | - |

**Example Request Payload:**
```json
{
  "batch_name": "sample_batch_name",
  "centre_id": 1,
  "fy_year": "sample_fy_year",
  "status": 1
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `app__modules__batch__schema__BatchResponse`

**Example Success Response:**
```json
{
  "batch_id": 1,
  "batch_name": "sample_batch_name",
  "centre_id": 1,
  "fy_year": "sample_fy_year",
  "created_by": 1,
  "status": 1,
  "created_at": "sample_created_at",
  "updated_at": "sample_updated_at"
}
```

- **Possible Error Status Codes**: `400`, `404`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `UPDATE`
- **Key Columns Referenced**: `users.id`, `users.role`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\batch\services\BatchService.js` (Line 87)
  - Snippet: `API.put(`/batches/${batchId}`, {             batch_name: batchName,            `

---

### `PATCH` /batches/{batch_id}/status

- **Summary**: Update Batch Status
- **Router / Handler**: [`update_batch_status`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/batch/router.py#L106) in `Backend\app\modules\batch\router.py` (Line 106)
- **Authentication**: `Public (None)`
- **Allowed Roles**: Public / Open
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `batch_id` | `integer` | Yes | - |

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `BatchStatusUpdateRequest`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `status` | `integer` | Yes | `None` | - |

**Example Request Payload:**
```json
{
  "status": 1
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `app__modules__batch__schema__BatchResponse`

**Example Success Response:**
```json
{
  "batch_id": 1,
  "batch_name": "sample_batch_name",
  "centre_id": 1,
  "fy_year": "sample_fy_year",
  "created_by": 1,
  "status": 1,
  "created_at": "sample_created_at",
  "updated_at": "sample_updated_at"
}
```

- **Possible Error Status Codes**: `400`, `404`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `UPDATE`
- **Key Columns Referenced**: `users.id`, `users.role`, `users.status`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\batch\services\BatchService.js` (Line 54)
  - Snippet: `API.patch(`/batches/${batchId}/status`, {             status: newStatus,         });    `

---

### `DELETE` /batches/{batch_id}

- **Summary**: Delete Batch
- **Router / Handler**: [`delete_batch`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/batch/router.py#L124) in `Backend\app\modules\batch\router.py` (Line 124)
- **Authentication**: `Public (None)`
- **Allowed Roles**: Public / Open
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `batch_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `404`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `DELETE`
- **Key Columns Referenced**: `users.id`, `users.role`, `users.status`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\batch\services\BatchService.js` (Line 66)
  - Snippet: `API.delete(`/batches/${batchId}`);         return response.data;     } catch (erro`

---

### `GET` /batches/{batch_id}/participants

- **Summary**: Get Batch Participants
- **Router / Handler**: [`get_batch_participants`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/batch/router.py#L140) in `Backend\app\modules\batch\router.py` (Line 140)
- **Authentication**: `Public (None)`
- **Allowed Roles**: Public / Open
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `batch_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[BatchParticipantResponse]`

**Example Success Response:**
```json
[
  {
    "participant_id": 1,
    "participant_name": "sample_participant_name",
    "email": "user@example.com",
    "mobile_no": "sample_mobile_no",
    "enrollment_no": "sample_enrollment_no"
  }
]
```

- **Possible Error Status Codes**: `400`, `404`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `batch_masters`, `batch_participant`, `centre_masters`, `district_master`, `participantmasters`, `state_master`, `users`
- **SQLAlchemy Models**: `BatchMaster`, `BatchParticipant`, `CentreMaster`, `DistrictMaster`, `ParticipantMaster`, `StateMaster`, `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `batch_masters.batch_id`, `batch_participant.batch_id`, `users.id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\batch\services\BatchService.js` (Line 44)
  - Snippet: `API.get(`/batches/${batchId}/participants`);         return response.data;     } catch (erro`

---

## Centres

Total endpoints in module: **9**

### `GET` /centres/states

- **Summary**: Get Active States
- **Description**: Returns all active states.
- **Router / Handler**: [`get_states`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/centres/router.py#L33) in `Backend\app\modules\centres\router.py` (Line 33)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1
- **Required Permissions / Scopes**: Module: CENTRES
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[app__modules__centres__schema__StateResponse]`

**Example Success Response:**
```json
[
  {
    "state_lgd_code": 1,
    "state_name": "sample_state_name"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `centre_masters`, `district_master`
- **SQLAlchemy Models**: `CentreMaster`, `DistrictMaster`
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\center\services\CenterService.js` (Line 6)
  - Snippet: `API.get("/centres/states"); };  // Get districts by state export const getD`
- File: `features\dashboard\services\DashboardFilterService.js` (Line 12)
  - Snippet: `API.get("/centres/states");     return response.data; };  export const getD`

---

### `GET` /centres/districts/{state_id}

- **Summary**: Get Districts by State
- **Description**: Returns all active districts for the selected state.
- **Router / Handler**: [`get_districts`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/centres/router.py#L47) in `Backend\app\modules\centres\router.py` (Line 47)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1
- **Required Permissions / Scopes**: Module: CENTRES
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `state_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[app__modules__centres__schema__DistrictResponse]`

**Example Success Response:**
```json
[
  {
    "district_lgd_code": 1,
    "district_name": "sample_district_name"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `centre_masters`, `district_master`
- **SQLAlchemy Models**: `CentreMaster`, `DistrictMaster`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `centre_masters.state_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\center\services\CenterService.js` (Line 11)
  - Snippet: `API.get(`/centres/districts/${stateId}`); };  // Get blocks by district export const getB`
- File: `features\dashboard\services\DashboardFilterService.js` (Line 17)
  - Snippet: `API.get(         `/centres/districts/${stateId}`     );      return response.data; };  export cons`

---

### `GET` /centres/blocks/{district_id}

- **Summary**: Get Blocks by District
- **Description**: Returns all active blocks for the selected district.
- **Router / Handler**: [`get_blocks`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/centres/router.py#L62) in `Backend\app\modules\centres\router.py` (Line 62)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1
- **Required Permissions / Scopes**: Module: CENTRES
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `district_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[BlockResponse]`

**Example Success Response:**
```json
[
  {
    "block_lgd_code": 1,
    "block_name": "sample_block_name"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `centre_masters`, `district_master`
- **SQLAlchemy Models**: `CentreMaster`, `DistrictMaster`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `centre_masters.district_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\center\services\CenterService.js` (Line 16)
  - Snippet: `API.get(`/centres/blocks/${districtId}`); };    /* =========================    CENTRE CR`

---

### `GET` /centres

- **Summary**: Get Centres
- **Router / Handler**: [`get_centres`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/centres/router.py#L77) in `Backend\app\modules\centres\router.py` (Line 77)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1
- **Required Permissions / Scopes**: Module: CENTRES
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `state_id` | `any` | No | `None` | - |
| `district_id` | `any` | No | `None` | - |
| `search` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[CentreListResponse]`

**Example Success Response:**
```json
[
  {
    "centre_id": 1,
    "centre_name": "sample_centre_name",
    "state_name": "sample_state_name",
    "district_name": "sample_district_name",
    "block_name": "sample_block_name",
    "phone_number": "sample_phone_number",
    "status": 1
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `block_master`, `centre_masters`, `district_master`, `state_master`
- **SQLAlchemy Models**: `BlockMaster`, `CentreMaster`, `DistrictMaster`, `StateMaster`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `centre_masters.district_id`, `centre_masters.state_id`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\center\services\CenterService.js` (Line 27)
  - Snippet: `API.get("/centres", {         params,     }); };  // Create centre e`
- File: `features\dashboard\services\DashboardFilterService.js` (Line 28)
  - Snippet: `API.get("/centres", {         params: {             state_id: stateI`

---

### `POST` /centres

- **Summary**: Create Centre
- **Router / Handler**: [`create_centre`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/centres/router.py#L96) in `Backend\app\modules\centres\router.py` (Line 96)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1
- **Required Permissions / Scopes**: Module: CENTRES
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `CentreCreateRequest`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `centre_name` | `string` | Yes | `None` | - |
| `address` | `string` | Yes | `None` | - |
| `location` | `string` | Yes | `None` | - |
| `latitude` | `any` | No | `None` | - |
| `longitude` | `any` | No | `None` | - |
| `pin` | `string` | Yes | `None` | - |
| `phone_number` | `string` | Yes | `None` | - |
| `email` | `string` | Yes | `None` | - |
| `block_id` | `integer` | Yes | `None` | - |
| `district_id` | `integer` | Yes | `None` | - |
| `state_id` | `integer` | Yes | `None` | - |
| `status` | `integer` | No | `1` | - |

**Example Request Payload:**
```json
{
  "centre_name": "sample_centre_name",
  "address": "sample_address",
  "location": "sample_location",
  "latitude": "sample_latitude",
  "longitude": "sample_longitude",
  "pin": "sample_pin",
  "phone_number": "9876543210",
  "email": "user@example.com",
  "block_id": 1,
  "district_id": 1,
  "state_id": 1,
  "status": 1
}
```

#### Responses

- **Success Status Code**: `201`
- **Response Model**: `app__modules__centres__schema__CentreResponse`

**Example Success Response:**
```json
{
  "centre_id": 1,
  "centre_name": "sample_centre_name",
  "address": "sample_address",
  "location": "sample_location",
  "latitude": "sample_latitude",
  "longitude": "sample_longitude",
  "pin": "sample_pin",
  "phone_number": "sample_phone_number",
  "email": "user@example.com",
  "block_id": 1,
  "district_id": 1,
  "state_id": 1,
  "status": 1
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `block_master`, `centre_masters`, `district_master`, `state_master`
- **SQLAlchemy Models**: `BlockMaster`, `CentreMaster`, `DistrictMaster`, `StateMaster`
- **Operations Performed**: `INSERT`
- **Key Columns Referenced**: `block_master.status`, `centre_masters.status`, `district_master.status`, `state_master.status`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\center\services\CenterService.js` (Line 34)
  - Snippet: `API.post("/centres", payload); };  // Get single centre by ID export `

---

### `GET` /centres/{centre_id}

- **Summary**: Get Centre By Id
- **Router / Handler**: [`get_centre_by_id`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/centres/router.py#L111) in `Backend\app\modules\centres\router.py` (Line 111)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1
- **Required Permissions / Scopes**: Module: CENTRES
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `centre_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `CentreDetailResponse`

**Example Success Response:**
```json
{
  "centre_id": 1,
  "centre_name": "sample_centre_name",
  "address": "sample_address",
  "location": "sample_location",
  "latitude": "sample_latitude",
  "longitude": "sample_longitude",
  "pin": "sample_pin",
  "phone_number": "sample_phone_number",
  "email": "user@example.com",
  "state_id": "sample_state_id",
  "state_name": "sample_state_name",
  "district_id": "sample_district_id",
  "district_name": "sample_district_name",
  "block_id": "sample_block_id",
  "block_name": "sample_block_name",
  "status": 1,
  "created_at": "sample_created_at",
  "updated_at": "sample_updated_at"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `block_master`, `centre_masters`, `district_master`, `state_master`
- **SQLAlchemy Models**: `BlockMaster`, `CentreMaster`, `DistrictMaster`, `StateMaster`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `centre_masters.centre_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\center\services\CenterService.js` (Line 39)
  - Snippet: `API.get(`/centres/${centreId}`); };  // Update centre export const updateCentre `

---

### `PUT` /centres/{centre_id}

- **Summary**: Update Centre
- **Router / Handler**: [`update_centre`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/centres/router.py#L125) in `Backend\app\modules\centres\router.py` (Line 125)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1
- **Required Permissions / Scopes**: Module: CENTRES
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `centre_id` | `integer` | Yes | - |

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `CentreUpdateRequest`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `centre_name` | `string` | Yes | `None` | - |
| `address` | `string` | Yes | `None` | - |
| `location` | `string` | Yes | `None` | - |
| `latitude` | `any` | No | `None` | - |
| `longitude` | `any` | No | `None` | - |
| `pin` | `string` | Yes | `None` | - |
| `phone_number` | `string` | Yes | `None` | - |
| `email` | `string` | Yes | `None` | - |
| `state_id` | `integer` | Yes | `None` | - |
| `district_id` | `integer` | Yes | `None` | - |
| `block_id` | `integer` | Yes | `None` | - |
| `status` | `integer` | Yes | `None` | - |

**Example Request Payload:**
```json
{
  "centre_name": "sample_centre_name",
  "address": "sample_address",
  "location": "sample_location",
  "latitude": "sample_latitude",
  "longitude": "sample_longitude",
  "pin": "sample_pin",
  "phone_number": "9876543210",
  "email": "user@example.com",
  "state_id": 1,
  "district_id": 1,
  "block_id": 1,
  "status": 1
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `app__modules__centres__schema__CentreResponse`

**Example Success Response:**
```json
{
  "centre_id": 1,
  "centre_name": "sample_centre_name",
  "address": "sample_address",
  "location": "sample_location",
  "latitude": "sample_latitude",
  "longitude": "sample_longitude",
  "pin": "sample_pin",
  "phone_number": "sample_phone_number",
  "email": "user@example.com",
  "block_id": 1,
  "district_id": 1,
  "state_id": 1,
  "status": 1
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `block_master`, `centre_masters`, `district_master`, `state_master`
- **SQLAlchemy Models**: `BlockMaster`, `CentreMaster`, `DistrictMaster`, `StateMaster`
- **Operations Performed**: `UPDATE`
- **Key Columns Referenced**: `centre_masters.centre_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\center\services\CenterService.js` (Line 44)
  - Snippet: `API.put(`/centres/${centreId}`, payload); };  // Update centre status export con`

---

### `PATCH` /centres/{centre_id}/status

- **Summary**: Update Centre Status
- **Router / Handler**: [`update_centre_status`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/centres/router.py#L141) in `Backend\app\modules\centres\router.py` (Line 141)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1
- **Required Permissions / Scopes**: Module: CENTRES
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `centre_id` | `integer` | Yes | - |

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `CentreStatusUpdateRequest`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `status` | `integer` | Yes | `None` | - |

**Example Request Payload:**
```json
{
  "status": 1
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `app__modules__centres__schema__CentreResponse`

**Example Success Response:**
```json
{
  "centre_id": 1,
  "centre_name": "sample_centre_name",
  "address": "sample_address",
  "location": "sample_location",
  "latitude": "sample_latitude",
  "longitude": "sample_longitude",
  "pin": "sample_pin",
  "phone_number": "sample_phone_number",
  "email": "user@example.com",
  "block_id": 1,
  "district_id": 1,
  "state_id": 1,
  "status": 1
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `block_master`, `centre_masters`, `district_master`, `state_master`
- **SQLAlchemy Models**: `BlockMaster`, `CentreMaster`, `DistrictMaster`, `StateMaster`
- **Operations Performed**: `UPDATE`
- **Key Columns Referenced**: `block_master.status`, `centre_masters.centre_id`, `centre_masters.status`, `district_master.status`, `state_master.status`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\center\services\CenterService.js` (Line 49)
  - Snippet: `API.patch(`/centres/${centreId}/status`, {         status,     }); };  // Delete centre e`

---

### `DELETE` /centres/{centre_id}

- **Summary**: Delete Centre
- **Router / Handler**: [`delete_centre`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/centres/router.py#L157) in `Backend\app\modules\centres\router.py` (Line 157)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1
- **Required Permissions / Scopes**: Module: CENTRES
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `centre_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `DeleteCentreResponse`

**Example Success Response:**
```json
{
  "message": "sample_message"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `block_master`, `centre_masters`, `district_master`, `state_master`
- **SQLAlchemy Models**: `BlockMaster`, `CentreMaster`, `DistrictMaster`, `StateMaster`
- **Operations Performed**: `DELETE`
- **Key Columns Referenced**: `block_master.status`, `centre_masters.centre_id`, `centre_masters.status`, `district_master.status`, `state_master.status`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\center\services\CenterService.js` (Line 56)
  - Snippet: `API.delete(`/centres/${centreId}`); };`

---

## Courses

Total endpoints in module: **5**

### `GET` /courses

- **Summary**: Get Courses
- **Router / Handler**: [`get_courses`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/course/router.py#L20) in `Backend\app\modules\course\router.py` (Line 20)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `page` | `integer` | No | `1` | - |
| `page_size` | `integer` | No | `10` | - |
| `search` | `any` | No | `None` | - |
| `language_id` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `course_masters`, `language_master`, `module_masters`, `participant_module`
- **SQLAlchemy Models**: `CourseMaster`, `LanguageMaster`, `ModuleMaster`, `ParticipantModule`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `course_masters.language_id`, `language_master.language_id`, `module_masters.language_id`
- **Pagination Supported**: Yes
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\course\services\CourseService.js` (Line 4)
  - Snippet: `API.get("/courses", {         params: {             language_id: lan`

---

### `GET` /courses/{course_id}/translation

- **Summary**: Get Course Translation
- **Router / Handler**: [`get_course_translation`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/course/router.py#L44) in `Backend\app\modules\course\router.py` (Line 44)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Unused by Web Frontend (no frontend service or page calls this endpoint).

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `course_id` | `integer` | Yes | - |

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `integer` | Yes | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `course_masters`, `language_master`, `module_masters`, `participant_module`
- **SQLAlchemy Models**: `CourseMaster`, `LanguageMaster`, `ModuleMaster`, `ParticipantModule`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `course_masters.course_id`, `course_masters.language_id`, `language_master.language_id`, `module_masters.language_id`, `participant_module.course_id`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

No matching frontend service call found in `Frontend/src` (Backend-only / Unused by web frontend).

---

### `GET` /courses/{course_id}/edit

- **Summary**: Edit Course
- **Router / Handler**: [`edit_course`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/course/router.py#L63) in `Backend\app\modules\course\router.py` (Line 63)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `course_id` | `integer` | Yes | - |

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `integer` | Yes | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `course_masters`, `language_master`, `module_masters`, `participant_module`
- **SQLAlchemy Models**: `CourseMaster`, `LanguageMaster`, `ModuleMaster`, `ParticipantModule`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `course_masters.course_id`, `course_masters.language_id`, `language_master.language_id`, `module_masters.language_id`, `participant_module.course_id`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\course\services\CourseService.js` (Line 52)
  - Snippet: `API.get(         `/courses/${courseId}/edit`,         {             params: {                 `

---

### `PUT` /courses/{course_id}

- **Summary**: Update Course
- **Router / Handler**: [`update_course`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/course/router.py#L82) in `Backend\app\modules\course\router.py` (Line 82)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `course_id` | `integer` | Yes | - |

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `integer` | Yes | `None` | - |

#### Request Body

- **Content-Type**: `multipart/form-data`
- **Schema**: `Body_update_course_courses__course_id__put`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `course_name` | `string` | Yes | `None` | - |
| `course_description` | `string` | Yes | `None` | - |
| `status` | `integer` | Yes | `None` | - |
| `course_image` | `any` | No | `None` | - |

**Example Request Payload:**
```json
{
  "course_name": "sample_course_name",
  "course_description": "sample_course_description",
  "status": 1,
  "course_image": "sample_course_image"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `course_masters`, `language_master`, `module_masters`, `participant_module`
- **SQLAlchemy Models**: `CourseMaster`, `LanguageMaster`, `ModuleMaster`, `ParticipantModule`
- **Operations Performed**: `UPDATE`
- **Key Columns Referenced**: `course_masters.course_description`, `course_masters.course_id`, `course_masters.course_image`, `course_masters.course_name`, `course_masters.language_id`, `course_masters.status`, `language_master.language_id`, `module_masters.language_id`, `module_masters.status`, `participant_module.course_id`, `participant_module.status`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: Yes (Multipart)

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\course\services\CourseService.js` (Line 65)
  - Snippet: `API.put(         `/courses/${courseId}`,         payload,         {             params: {`

---

### `GET` /courses/export

- **Summary**: Export Courses
- **Router / Handler**: [`export_courses`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/course/router.py#L104) in `Backend\app\modules\course\router.py` (Line 104)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `search` | `any` | No | `None` | - |
| `language_id` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `course_masters`, `language_master`, `module_masters`, `participant_module`
- **SQLAlchemy Models**: `CourseMaster`, `LanguageMaster`, `ModuleMaster`, `ParticipantModule`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `course_masters.course_name`, `course_masters.language_id`, `course_masters.status`, `language_master.language_id`, `language_master.language_name`, `module_masters.language_id`, `module_masters.module_name`, `module_masters.status`, `participant_module.status`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\course\services\CourseService.js` (Line 77)
  - Snippet: `API.get("/courses/export", {         params,         responseType: "blob", `

---

## Dashboard

Total endpoints in module: **15**

### `GET` /dashboard

- **Summary**: Get Dashboard
- **Router / Handler**: [`get_dashboard`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/dashboard/router.py#L36) in `Backend\app\modules\dashboard\router.py` (Line 36)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: DASHBOARD, Location Scope Clamping (State/District/Centre)
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `state_id` | `any` | No | `None` | - |
| `district_id` | `any` | No | `None` | - |
| `centre_id` | `any` | No | `None` | - |
| `from_date` | `any` | No | `None` | - |
| `to_date` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `DashboardResponse`

**Example Success Response:**
```json
{
  "summary": "sample_summary",
  "trainee_status": [],
  "state_wise_participants": [],
  "state_wise_centres": [],
  "gender_distribution": [],
  "monthly_login_trend": [],
  "document_type_distribution": [],
  "district_wise_participants": [],
  "age_group_distribution": [],
  "module_lock_status": [],
  "module_wise_performance": []
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `users.centre_id`, `users.id`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\dashboard\services\DashboardFilterService.js` (Line 4)
  - Snippet: `API.get("/dashboard", {         params: filters,     });      return r`
- File: `features\dashboard\services\DashboardService.js` (Line 18)
  - Snippet: `API.get("/dashboard", {         params: cleanParams(filters),     }); `

---

### `GET` /dashboard/trainee-status/details

- **Summary**: Get Trainee Status Details
- **Router / Handler**: [`get_trainee_status_details`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/dashboard/router.py#L62) in `Backend\app\modules\dashboard\router.py` (Line 62)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: DASHBOARD, Location Scope Clamping (State/District/Centre)
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `state_id` | `any` | No | `None` | - |
| `district_id` | `any` | No | `None` | - |
| `centre_id` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[TraineeStatusDetail]`

**Example Success Response:**
```json
[
  {
    "participant_id": "sample_participant_id",
    "participant_name": "sample_participant_name",
    "mobile_no": "sample_mobile_no",
    "enrollment_no": "sample_enrollment_no",
    "age": "sample_age",
    "state_name": "sample_state_name",
    "district_name": "sample_district_name",
    "centre_name": "sample_centre_name",
    "course_progress": "sample_course_progress",
    "performance_status": "sample_performance_status"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `users.centre_id`, `users.id`, `users.status`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\dashboard\services\DashboardService.js` (Line 30)
  - Snippet: `API.get("/dashboard/trainee-status/details", {         params: cleanParams(filters),     }); `

---

### `GET` /dashboard/state-wise-trainee-status

- **Summary**: Get State Wise Trainee Status Route
- **Router / Handler**: [`get_state_wise_trainee_status_route`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/dashboard/router.py#L84) in `Backend\app\modules\dashboard\router.py` (Line 84)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: DASHBOARD, Location Scope Clamping (State/District/Centre)
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `state_id` | `any` | No | `None` | - |
| `district_id` | `any` | No | `None` | - |
| `centre_id` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[StateWiseTraineeStatusItem]`

**Example Success Response:**
```json
[
  {
    "state_name": "sample_state_name",
    "status": "sample_status",
    "label": "sample_label",
    "total": 1
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `users.centre_id`, `users.id`, `users.status`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\dashboard\services\DashboardService.js` (Line 38)
  - Snippet: `API.get(         "/dashboard/state-wise-trainee-status",         { params: cleanParams(filters) }   `

---

### `GET` /dashboard/state-wise-participants

- **Summary**: Get State Wise Participants
- **Router / Handler**: [`get_state_wise_participants`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/dashboard/router.py#L110) in `Backend\app\modules\dashboard\router.py` (Line 110)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: DASHBOARD, Location Scope Clamping (State/District/Centre)
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `clicked_value` | `any` | No | `None` | - |
| `state_id` | `any` | No | `None` | - |
| `district_id` | `any` | No | `None` | - |
| `centre_id` | `any` | No | `None` | - |
| `from_date` | `any` | No | `None` | - |
| `to_date` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[DashboardParticipantDetail]`

**Example Success Response:**
```json
[
  {
    "participant_id": 1,
    "participant_name": "sample_participant_name",
    "mobile_no": "sample_mobile_no",
    "email": "user@example.com",
    "enrollment_no": "sample_enrollment_no",
    "gender": "sample_gender",
    "age": "sample_age",
    "state_name": "sample_state_name",
    "district_name": "sample_district_name"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `users.centre_id`, `users.id`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\dashboard\services\DashboardService.js` (Line 69)
  - Snippet: `API.get(         "/dashboard/state-wise-participants",         {             params: cleanParams(fil`

---

### `GET` /dashboard/district-wise-participants

- **Summary**: Get District Wise Participants
- **Router / Handler**: [`get_district_wise_participants`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/dashboard/router.py#L138) in `Backend\app\modules\dashboard\router.py` (Line 138)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: DASHBOARD, Location Scope Clamping (State/District/Centre)
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `clicked_value` | `any` | No | `None` | - |
| `state_id` | `any` | No | `None` | - |
| `district_id` | `any` | No | `None` | - |
| `centre_id` | `any` | No | `None` | - |
| `from_date` | `any` | No | `None` | - |
| `to_date` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[DashboardParticipantDetail]`

**Example Success Response:**
```json
[
  {
    "participant_id": 1,
    "participant_name": "sample_participant_name",
    "mobile_no": "sample_mobile_no",
    "email": "user@example.com",
    "enrollment_no": "sample_enrollment_no",
    "gender": "sample_gender",
    "age": "sample_age",
    "state_name": "sample_state_name",
    "district_name": "sample_district_name"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `users.centre_id`, `users.id`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\dashboard\services\DashboardService.js` (Line 86)
  - Snippet: `API.get(         "/dashboard/district-wise-participants",         {             params: cleanParams(`

---

### `GET` /dashboard/gender-distribution

- **Summary**: Get Gender Distribution
- **Router / Handler**: [`get_gender_distribution`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/dashboard/router.py#L166) in `Backend\app\modules\dashboard\router.py` (Line 166)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: DASHBOARD, Location Scope Clamping (State/District/Centre)
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `clicked_value` | `any` | No | `None` | - |
| `state_id` | `any` | No | `None` | - |
| `district_id` | `any` | No | `None` | - |
| `centre_id` | `any` | No | `None` | - |
| `from_date` | `any` | No | `None` | - |
| `to_date` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[DashboardParticipantDetail]`

**Example Success Response:**
```json
[
  {
    "participant_id": 1,
    "participant_name": "sample_participant_name",
    "mobile_no": "sample_mobile_no",
    "email": "user@example.com",
    "enrollment_no": "sample_enrollment_no",
    "gender": "sample_gender",
    "age": "sample_age",
    "state_name": "sample_state_name",
    "district_name": "sample_district_name"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `users.centre_id`, `users.id`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\dashboard\services\DashboardService.js` (Line 103)
  - Snippet: `API.get(         "/dashboard/gender-distribution",         {             params: cleanParams(filter`

---

### `GET` /dashboard/age-group-distribution

- **Summary**: Get Age Group Distribution
- **Router / Handler**: [`get_age_group_distribution`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/dashboard/router.py#L194) in `Backend\app\modules\dashboard\router.py` (Line 194)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: DASHBOARD, Location Scope Clamping (State/District/Centre)
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `clicked_value` | `any` | No | `None` | - |
| `state_id` | `any` | No | `None` | - |
| `district_id` | `any` | No | `None` | - |
| `centre_id` | `any` | No | `None` | - |
| `from_date` | `any` | No | `None` | - |
| `to_date` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[DashboardParticipantDetail]`

**Example Success Response:**
```json
[
  {
    "participant_id": 1,
    "participant_name": "sample_participant_name",
    "mobile_no": "sample_mobile_no",
    "email": "user@example.com",
    "enrollment_no": "sample_enrollment_no",
    "gender": "sample_gender",
    "age": "sample_age",
    "state_name": "sample_state_name",
    "district_name": "sample_district_name"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `users.centre_id`, `users.id`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\dashboard\services\DashboardService.js` (Line 120)
  - Snippet: `API.get(         "/dashboard/age-group-distribution",         {             params: cleanParams(filt`

---

### `GET` /dashboard/state-wise-centres

- **Summary**: Get State Wise Centres
- **Router / Handler**: [`get_state_wise_centres`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/dashboard/router.py#L222) in `Backend\app\modules\dashboard\router.py` (Line 222)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: DASHBOARD, Location Scope Clamping (State/District/Centre)
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `clicked_value` | `any` | No | `None` | - |
| `state_id` | `any` | No | `None` | - |
| `district_id` | `any` | No | `None` | - |
| `centre_id` | `any` | No | `None` | - |
| `from_date` | `any` | No | `None` | - |
| `to_date` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[DashboardCentreDetail]`

**Example Success Response:**
```json
[
  {
    "centre_name": "sample_centre_name",
    "address": "sample_address",
    "state_name": "sample_state_name",
    "district_name": "sample_district_name",
    "status": "sample_status"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `users.centre_id`, `users.id`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\dashboard\services\DashboardService.js` (Line 137)
  - Snippet: `API.get(         "/dashboard/state-wise-centres",         {             params: cleanParams(filter`

---

### `GET` /dashboard/module-wise-performance

- **Summary**: Get Module Wise Performance
- **Router / Handler**: [`get_module_wise_performance`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/dashboard/router.py#L250) in `Backend\app\modules\dashboard\router.py` (Line 250)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: DASHBOARD, Location Scope Clamping (State/District/Centre)
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `clicked_value` | `any` | No | `None` | - |
| `state_id` | `any` | No | `None` | - |
| `district_id` | `any` | No | `None` | - |
| `centre_id` | `any` | No | `None` | - |
| `from_date` | `any` | No | `None` | - |
| `to_date` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[DashboardModuleDetail]`

**Example Success Response:**
```json
[
  {
    "module_name": "sample_module_name",
    "total": 1
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `users.centre_id`, `users.id`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\dashboard\services\DashboardService.js` (Line 154)
  - Snippet: `API.get(         "/dashboard/module-wise-performance",         {             params: cleanParams(fil`

---

### `GET` /dashboard/document-type-distribution

- **Summary**: Get Document Type Distribution
- **Router / Handler**: [`get_document_type_distribution`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/dashboard/router.py#L278) in `Backend\app\modules\dashboard\router.py` (Line 278)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: DASHBOARD
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[DashboardDocumentDetail]`

**Example Success Response:**
```json
[
  {
    "doc_title": "sample_doc_title",
    "doc_type": "sample_doc_type",
    "format": "sample_format",
    "module_name": "sample_module_name",
    "status": "sample_status"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `assessment_master`, `batch_masters`, `batch_participant`, `centre_masters`, `course_masters`, `district_master`, `document_categories`, `document_masters`, `login_logs`, `module_masters`, `participant_dbs`, `participant_mcqs`, `participant_mm`, `participant_module`, `participant_scs`, `participantmasters`, `post_session_assessment`, `state_master`, `users`
- **SQLAlchemy Models**: `AssessmentMaster`, `BatchMaster`, `BatchParticipant`, `CentreMaster`, `CourseMaster`, `DistrictMaster`, `DocumentCategory`, `DocumentMaster`, `LoginLog`, `ModuleMaster`, `ParticipantDb`, `ParticipantMaster`, `ParticipantMcq`, `ParticipantMm`, `ParticipantModule`, `ParticipantScq`, `PostSessionAssessment`, `StateMaster`, `User`
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\dashboard\services\DashboardService.js` (Line 169)
  - Snippet: `API.get(         "/dashboard/document-type-distribution"     );      return response.data; };  /* ==`

---

### `GET` /dashboard/monthly-trending-modules

- **Summary**: Get Monthly Trending Modules
- **Router / Handler**: [`get_monthly_trending_modules`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/dashboard/router.py#L290) in `Backend\app\modules\dashboard\router.py` (Line 290)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: DASHBOARD, Location Scope Clamping (State/District/Centre)
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `state_id` | `any` | No | `None` | - |
| `district_id` | `any` | No | `None` | - |
| `centre_id` | `any` | No | `None` | - |
| `from_date` | `any` | No | `None` | - |
| `to_date` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[MonthlyTrendingModuleItem]`

**Example Success Response:**
```json
[
  {
    "month": "sample_month",
    "module_id": 1,
    "module_name": "sample_module_name",
    "total": 1
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `users.centre_id`, `users.id`, `users.status`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\dashboard\services\DashboardService.js` (Line 47)
  - Snippet: `API.get(         "/dashboard/monthly-trending-modules",         { params: cleanParams(filters) }    `

---

### `GET` /dashboard/module-assignment-usage

- **Summary**: Get Module Assignment Usage
- **Router / Handler**: [`get_module_assignment_usage`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/dashboard/router.py#L326) in `Backend\app\modules\dashboard\router.py` (Line 326)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: DASHBOARD, Location Scope Clamping (State/District/Centre)
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `state_id` | `any` | No | `None` | - |
| `district_id` | `any` | No | `None` | - |
| `centre_id` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[ModuleAssignmentUsageItem]`

**Example Success Response:**
```json
[
  {
    "module_id": 1,
    "module_name": "sample_module_name",
    "total_assigned": 1
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `users.centre_id`, `users.id`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\dashboard\services\DashboardService.js` (Line 56)
  - Snippet: `API.get(         "/dashboard/module-assignment-usage",         { params: cleanParams(filters) }     `

---

### `GET` /dashboard/monthly-logins/details

- **Summary**: Get Monthly Login Details
- **Router / Handler**: [`get_monthly_login_details`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/dashboard/router.py#L380) in `Backend\app\modules\dashboard\router.py` (Line 380)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: DASHBOARD, Location Scope Clamping (State/District/Centre)
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `clicked_value` | `string` | Yes | `None` | - |
| `state_id` | `any` | No | `None` | - |
| `district_id` | `any` | No | `None` | - |
| `centre_id` | `any` | No | `None` | - |
| `from_date` | `any` | No | `None` | - |
| `to_date` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[DashboardLoginDetail]`

**Example Success Response:**
```json
[
  {
    "participant_name": "sample_participant_name",
    "mobile_no": "sample_mobile_no",
    "login_time": "sample_login_time",
    "app_version": "sample_app_version"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `users.centre_id`, `users.id`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\dashboard\services\DashboardService.js` (Line 200)
  - Snippet: `API.get(         "/dashboard/monthly-logins/details",         {             params: cleanParams(filt`

---

### `GET` /dashboard/centre-wise-trainees

- **Summary**: Get Centre Wise Trainees
- **Router / Handler**: [`get_centre_wise_trainees`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/dashboard/router.py#L408) in `Backend\app\modules\dashboard\router.py` (Line 408)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: DASHBOARD, Location Scope Clamping (State/District/Centre)
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `state_id` | `any` | No | `None` | - |
| `district_id` | `any` | No | `None` | - |
| `centre_id` | `any` | No | `None` | - |
| `from_date` | `any` | No | `None` | - |
| `to_date` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[CentreWiseTraineesItem]`

**Example Success Response:**
```json
[
  {
    "state_id": 1,
    "state_name": "sample_state_name",
    "centre_id": 1,
    "centre_name": "sample_centre_name",
    "district_name": "sample_district_name",
    "total_trainees": 1
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `users.centre_id`, `users.id`, `users.status`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\dashboard\services\DashboardService.js` (Line 244)
  - Snippet: `API.get(         "/dashboard/centre-wise-trainees",         {             params: cleanParams(filter`

---

### `GET` /dashboard/state-wise-trainees

- **Summary**: Get State Wise Trainees
- **Router / Handler**: [`get_state_wise_trainees`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/dashboard/router.py#L447) in `Backend\app\modules\dashboard\router.py` (Line 447)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: DASHBOARD, Location Scope Clamping (State/District/Centre)
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `state_id` | `any` | No | `None` | - |
| `district_id` | `any` | No | `None` | - |
| `centre_id` | `any` | No | `None` | - |
| `from_date` | `any` | No | `None` | - |
| `to_date` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[StateWiseTraineesItem]`

**Example Success Response:**
```json
[
  {
    "state_id": 1,
    "state_name": "sample_state_name",
    "total_trainees": 1
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `users.centre_id`, `users.id`, `users.status`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\dashboard\services\DashboardService.js` (Line 277)
  - Snippet: `API.get("/dashboard/state-wise-trainees", {         params,     });      const result = re`

---

## District Masters

Total endpoints in module: **5**

### `GET` /districts

- **Summary**: Get Districts
- **Router / Handler**: [`get_districts`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/master/district/router.py#L42) in `Backend\app\modules\master\district\router.py` (Line 42)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1
- **Required Permissions / Scopes**: Module: MASTER
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `state_lgd_code` | `any` | No | `None` | - |
| `district_name` | `any` | No | `None` | - |
| `status` | `any` | No | `None` | - |
| `page` | `integer` | No | `1` | - |
| `per_page` | `integer` | No | `10` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `DistrictListResponse`

**Example Success Response:**
```json
{
  "data": [],
  "total": 1,
  "page": 1,
  "per_page": 1,
  "total_pages": 1
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `users.name`, `users.state_lgd_code`, `users.status`
- **Pagination Supported**: Yes
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\master\district\services\DistrictService.js` (Line 4)
  - Snippet: `API.get("/districts", {         params,     });     return response.da`

---

### `POST` /districts

- **Summary**: Create District
- **Router / Handler**: [`create_district`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/master/district/router.py#L88) in `Backend\app\modules\master\district\router.py` (Line 88)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1
- **Required Permissions / Scopes**: Module: MASTER
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `DistrictCreateRequest`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `district_lgd_code` | `integer` | Yes | `None` | - |
| `district_name` | `string` | Yes | `None` | - |
| `state_lgd_code` | `integer` | Yes | `None` | - |
| `status` | `string` | No | `1` | - |

**Example Request Payload:**
```json
{
  "district_lgd_code": 1,
  "district_name": "sample_district_name",
  "state_lgd_code": 1,
  "status": "sample_status"
}
```

#### Responses

- **Success Status Code**: `201`
- **Response Model**: `app__modules__master__district__schema__DistrictResponse`

**Example Success Response:**
```json
{
  "district_lgd_code": 1,
  "district_name": "sample_district_name",
  "state_lgd_code": 1,
  "state_name": "sample_state_name",
  "status": "sample_status"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `INSERT`
- **Key Columns Referenced**: `users.role`, `users.status`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\master\district\services\DistrictService.js` (Line 16)
  - Snippet: `API.post("/districts", payload);     return response.data; };  export c`

---

### `GET` /districts/{district_lgd_code}

- **Summary**: Get District
- **Router / Handler**: [`get_district`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/master/district/router.py#L115) in `Backend\app\modules\master\district\router.py` (Line 115)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1
- **Required Permissions / Scopes**: Module: MASTER
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `district_lgd_code` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `app__modules__master__district__schema__DistrictResponse`

**Example Success Response:**
```json
{
  "district_lgd_code": 1,
  "district_name": "sample_district_name",
  "state_lgd_code": 1,
  "state_name": "sample_state_name",
  "status": "sample_status"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `users.district_lgd_code`, `users.status`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\master\district\services\DistrictService.js` (Line 11)
  - Snippet: `API.get(`/districts/${code}`);     return response.data; };  export const crea`

---

### `PUT` /districts/{district_lgd_code}

- **Summary**: Update District
- **Router / Handler**: [`update_district`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/master/district/router.py#L137) in `Backend\app\modules\master\district\router.py` (Line 137)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1
- **Required Permissions / Scopes**: Module: MASTER
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `district_lgd_code` | `integer` | Yes | - |

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `DistrictUpdateRequest`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `district_name` | `string` | Yes | `None` | - |
| `state_lgd_code` | `integer` | Yes | `None` | - |
| `status` | `string` | Yes | `None` | - |

**Example Request Payload:**
```json
{
  "district_name": "sample_district_name",
  "state_lgd_code": 1,
  "status": "sample_status"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `app__modules__master__district__schema__DistrictResponse`

**Example Success Response:**
```json
{
  "district_lgd_code": 1,
  "district_name": "sample_district_name",
  "state_lgd_code": 1,
  "state_name": "sample_state_name",
  "status": "sample_status"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `UPDATE`
- **Key Columns Referenced**: `users.district_lgd_code`, `users.role`, `users.status`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\master\district\services\DistrictService.js` (Line 21)
  - Snippet: `API.put(`/districts/${code}`, payload);     return response.data; };  export c`

---

### `DELETE` /districts/{district_lgd_code}

- **Summary**: Delete District
- **Router / Handler**: [`delete_district`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/master/district/router.py#L166) in `Backend\app\modules\master\district\router.py` (Line 166)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1
- **Required Permissions / Scopes**: Module: MASTER
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `district_lgd_code` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `DeleteDistrictResponse`

**Example Success Response:**
```json
{
  "message": "sample_message"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `DELETE`
- **Key Columns Referenced**: `users.district_lgd_code`, `users.role`, `users.status`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\master\district\services\DistrictService.js` (Line 26)
  - Snippet: `API.delete(`/districts/${code}`);     return response.data; };`

---

## Document Management

Total endpoints in module: **11**

### `GET` /documents/categories

- **Summary**: Get Document Categories
- **Router / Handler**: [`get_document_categories`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/document/router.py#L45) in `Backend\app\modules\document\router.py` (Line 45)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: DOCUMENT_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[DocumentCategoryResponse]`

**Example Success Response:**
```json
[
  {
    "id": 1,
    "name": "sample_name"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\document\services\DocumentServices.js` (Line 28)
  - Snippet: `API.get("/documents/categories", {         params: languageId ? { language_id: la`

---

### `GET` /documents/languages

- **Summary**: Get Document Languages
- **Router / Handler**: [`get_document_languages`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/document/router.py#L59) in `Backend\app\modules\document\router.py` (Line 59)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: DOCUMENT_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[TranslationLanguageResponse]`

**Example Success Response:**
```json
[
  {
    "language_id": 1,
    "language_name": "sample_language_name"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\document\services\DocumentServices.js` (Line 14)
  - Snippet: `API.get("/documents/languages");     return response.data.map(({ language_id, la`

---

### `GET` /documents

- **Summary**: Get Documents
- **Router / Handler**: [`get_documents`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/document/router.py#L69) in `Backend\app\modules\document\router.py` (Line 69)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: DOCUMENT_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `search` | `any` | No | `None` | - |
| `language_id` | `any` | No | `None` | - |
| `doc_type` | `any` | No | `None` | - |
| `page` | `integer` | No | `1` | - |
| `per_page` | `integer` | No | `10` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `PaginatedDocumentListResponse`

**Example Success Response:**
```json
{
  "data": [],
  "total": 1,
  "page": 1,
  "per_page": 1,
  "total_pages": 1
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `document_categories`, `document_masters`, `language_master`, `module_masters`, `module_type`, `pdf_masters`, `ppt_masters`, `topic_master`, `video_masters`
- **SQLAlchemy Models**: `DocumentCategory`, `DocumentMaster`, `LanguageMaster`, `ModuleMaster`, `ModuleType`, `PdfMaster`, `PptMaster`, `TopicMaster`, `VideoMaster`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `document_categories.language_id`, `document_masters.doc_type`, `document_masters.language_id`, `language_master.language_id`, `module_masters.language_id`, `pdf_masters.language_id`, `ppt_masters.language_id`, `topic_master.language_id`, `video_masters.language_id`
- **Pagination Supported**: Yes
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\document\services\DocumentServices.js` (Line 4)
  - Snippet: `API.get("/documents", { params });     return response.data; };  expor`

---

### `GET` /documents/export/csv

- **Summary**: Export Csv
- **Router / Handler**: [`export_csv`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/document/router.py#L96) in `Backend\app\modules\document\router.py` (Line 96)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: DOCUMENT_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `status` | `any` | No | `None` | - |
| `doc_category_id` | `any` | No | `None` | - |
| `doc_ref_id` | `any` | No | `None` | - |
| `language_id` | `any` | No | `None` | - |
| `search` | `any` | No | `None` | - |
| `doc_type` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `document_masters`
- **SQLAlchemy Models**: `DocumentMaster`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `document_masters.doc_category_id`, `document_masters.doc_ref_id`, `document_masters.doc_type`, `document_masters.language_id`, `document_masters.status`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\document\services\DocumentServices.js` (Line 54)
  - Snippet: `API.get("/documents/export/csv", {         params,         responseType: "blob", `

---

### `GET` /documents/{doc_id}

- **Summary**: Get Document By Id
- **Router / Handler**: [`get_document_by_id`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/document/router.py#L125) in `Backend\app\modules\document\router.py` (Line 125)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: DOCUMENT_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `doc_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `DocumentViewResponse`

**Example Success Response:**
```json
{
  "document": "sample_document",
  "translations": []
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `document_categories`, `document_masters`, `language_master`, `module_masters`, `module_type`, `pdf_masters`, `ppt_masters`, `topic_master`, `video_masters`
- **SQLAlchemy Models**: `DocumentCategory`, `DocumentMaster`, `LanguageMaster`, `ModuleMaster`, `ModuleType`, `PdfMaster`, `PptMaster`, `TopicMaster`, `VideoMaster`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `document_masters.doc_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\document\services\DocumentServices.js` (Line 9)
  - Snippet: `API.get(`/documents/${docId}`);     return response.data; };  export const getL`

---

### `POST` /documents

- **Summary**: Create Document
- **Router / Handler**: [`create_document`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/document/router.py#L144) in `Backend\app\modules\document\router.py` (Line 144)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: DOCUMENT_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `multipart/form-data`
- **Schema**: `Body_create_document_documents_post`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `document_image` | `any` | No | `None` | - |
| `media_file` | `string` | Yes | `None` | - |
| `doc_title` | `string` | Yes | `None` | - |
| `doc_description` | `any` | No | `None` | - |
| `doc_category_id` | `integer` | Yes | `None` | - |
| `doc_type` | `string` | Yes | `None` | - |
| `status` | `integer` | Yes | `None` | - |
| `module_id` | `any` | No | `None` | - |
| `submodule_id` | `any` | No | `None` | - |
| `topic_id` | `any` | No | `None` | - |
| `language_id` | `integer` | No | `1` | - |
| `self_paced_learning` | `integer` | No | `0` | - |
| `pre_session_assessment` | `integer` | No | `0` | - |
| `main_content_of_the_module` | `integer` | No | `0` | - |
| `post_session_assessment` | `integer` | No | `0` | - |
| `doc_duration` | `any` | No | `None` | - |

**Example Request Payload:**
```json
{
  "document_image": "sample_document_image",
  "media_file": "sample_media_file",
  "doc_title": "sample_doc_title",
  "doc_description": "sample_doc_description",
  "doc_category_id": 1,
  "doc_type": "sample_doc_type",
  "status": 1,
  "module_id": "sample_module_id",
  "submodule_id": "sample_submodule_id",
  "topic_id": "sample_topic_id",
  "language_id": 1,
  "self_paced_learning": 1,
  "pre_session_assessment": 1,
  "main_content_of_the_module": 1,
  "post_session_assessment": 1,
  "doc_duration": "sample_doc_duration"
}
```

#### Responses

- **Success Status Code**: `201`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `document_categories`, `document_masters`, `language_master`, `module_masters`, `module_type`, `pdf_masters`, `ppt_masters`, `topic_master`, `video_masters`
- **SQLAlchemy Models**: `DocumentCategory`, `DocumentMaster`, `LanguageMaster`, `ModuleMaster`, `ModuleType`, `PdfMaster`, `PptMaster`, `TopicMaster`, `VideoMaster`
- **Operations Performed**: `INSERT`
- **Key Columns Referenced**: `document_categories.status`, `document_masters.status`, `module_masters.status`, `module_type.status`, `pdf_masters.status`, `ppt_masters.status`, `video_masters.status`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: Yes (Multipart)

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\document\services\DocumentServices.js` (Line 35)
  - Snippet: `API.post("/documents", payload, {         headers: { "Content-Type": un`

---

### `PUT` /documents/{doc_id}

- **Summary**: Update Document
- **Router / Handler**: [`update_document`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/document/router.py#L167) in `Backend\app\modules\document\router.py` (Line 167)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: DOCUMENT_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `doc_id` | `integer` | Yes | - |

#### Request Body

- **Content-Type**: `multipart/form-data`
- **Schema**: `Body_update_document_documents__doc_id__put`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `document_image` | `any` | No | `None` | - |
| `media_file` | `any` | No | `None` | - |
| `doc_title` | `string` | Yes | `None` | - |
| `doc_description` | `any` | No | `None` | - |
| `doc_category_id` | `integer` | Yes | `None` | - |
| `doc_type` | `string` | Yes | `None` | - |
| `status` | `integer` | Yes | `None` | - |
| `module_id` | `any` | No | `None` | - |
| `submodule_id` | `any` | No | `None` | - |
| `topic_id` | `any` | No | `None` | - |
| `language_id` | `integer` | No | `1` | - |
| `self_paced_learning` | `integer` | No | `0` | - |
| `pre_session_assessment` | `integer` | No | `0` | - |
| `main_content_of_the_module` | `integer` | No | `0` | - |
| `post_session_assessment` | `integer` | No | `0` | - |
| `doc_duration` | `any` | No | `None` | - |

**Example Request Payload:**
```json
{
  "document_image": "sample_document_image",
  "media_file": "sample_media_file",
  "doc_title": "sample_doc_title",
  "doc_description": "sample_doc_description",
  "doc_category_id": 1,
  "doc_type": "sample_doc_type",
  "status": 1,
  "module_id": "sample_module_id",
  "submodule_id": "sample_submodule_id",
  "topic_id": "sample_topic_id",
  "language_id": 1,
  "self_paced_learning": 1,
  "pre_session_assessment": 1,
  "main_content_of_the_module": 1,
  "post_session_assessment": 1,
  "doc_duration": "sample_doc_duration"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `document_categories`, `document_masters`, `language_master`, `module_masters`, `module_type`, `pdf_masters`, `ppt_masters`, `topic_master`, `video_masters`
- **SQLAlchemy Models**: `DocumentCategory`, `DocumentMaster`, `LanguageMaster`, `ModuleMaster`, `ModuleType`, `PdfMaster`, `PptMaster`, `TopicMaster`, `VideoMaster`
- **Operations Performed**: `UPDATE`
- **Key Columns Referenced**: `document_categories.status`, `document_masters.doc_id`, `document_masters.status`, `module_masters.status`, `module_type.status`, `pdf_masters.status`, `ppt_masters.status`, `video_masters.status`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: Yes (Multipart)

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\document\services\DocumentServices.js` (Line 42)
  - Snippet: `API.put(`/documents/${docId}`, payload, {         headers: { "Content-Type": un`

---

### `DELETE` /documents/{doc_id}

- **Summary**: Delete Document
- **Router / Handler**: [`delete_document`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/document/router.py#L192) in `Backend\app\modules\document\router.py` (Line 192)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: DOCUMENT_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `doc_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `document_categories`, `document_masters`, `language_master`, `module_masters`, `module_type`, `pdf_masters`, `ppt_masters`, `topic_master`, `video_masters`
- **SQLAlchemy Models**: `DocumentCategory`, `DocumentMaster`, `LanguageMaster`, `ModuleMaster`, `ModuleType`, `PdfMaster`, `PptMaster`, `TopicMaster`, `VideoMaster`
- **Operations Performed**: `DELETE`
- **Key Columns Referenced**: `document_categories.status`, `document_masters.doc_id`, `document_masters.status`, `module_masters.status`, `module_type.status`, `pdf_masters.status`, `ppt_masters.status`, `video_masters.status`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\document\services\DocumentServices.js` (Line 49)
  - Snippet: `API.delete(`/documents/${docId}`);     return response.data; };  export const expo`

---

### `GET` /documents/{document_id}/translation/form

- **Summary**: Get Translation Form
- **Router / Handler**: [`get_translation_form`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/document/router.py#L213) in `Backend\app\modules\document\router.py` (Line 213)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: DOCUMENT_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `document_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `TranslationFormResponse`

**Example Success Response:**
```json
{
  "document": "sample_document",
  "languages": [],
  "translations": []
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `document_masters`
- **SQLAlchemy Models**: `DocumentMaster`
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\document\services\DocumentServices.js` (Line 65)
  - Snippet: `API.get(         `/documents/${documentId}/translation/form`     );      return response.data; };  e`

---

### `GET` /documents/{document_id}/translation/{language_id}

- **Summary**: Get Translation
- **Router / Handler**: [`get_translation`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/document/router.py#L232) in `Backend\app\modules\document\router.py` (Line 232)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: DOCUMENT_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `document_id` | `integer` | Yes | - |
| `language_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `document_categories`, `document_masters`, `language_master`, `module_masters`, `module_type`, `pdf_masters`, `ppt_masters`, `topic_master`, `video_masters`
- **SQLAlchemy Models**: `DocumentCategory`, `DocumentMaster`, `LanguageMaster`, `ModuleMaster`, `ModuleType`, `PdfMaster`, `PptMaster`, `TopicMaster`, `VideoMaster`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `document_categories.language_id`, `document_masters.language_id`, `language_master.language_id`, `module_masters.language_id`, `pdf_masters.language_id`, `ppt_masters.language_id`, `topic_master.language_id`, `video_masters.language_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\document\services\DocumentServices.js` (Line 73)
  - Snippet: `API.get(         `/documents/${documentId}/translation/${languageId}`     );      return response.da`

---

### `POST` /documents/{document_id}/translation/save

- **Summary**: Save Translation
- **Router / Handler**: [`save_translation`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/document/router.py#L252) in `Backend\app\modules\document\router.py` (Line 252)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: DOCUMENT_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `document_id` | `integer` | Yes | - |

#### Request Body

- **Content-Type**: `multipart/form-data`
- **Schema**: `Body_save_translation_documents__document_id__translation_save_post`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `integer` | Yes | `None` | - |
| `title` | `string` | Yes | `None` | - |
| `description` | `any` | No | `None` | - |
| `document_image` | `any` | No | `None` | - |
| `media_file` | `any` | No | `None` | - |

**Example Request Payload:**
```json
{
  "language_id": 1,
  "title": "sample_title",
  "description": "sample_description",
  "document_image": "sample_document_image",
  "media_file": "sample_media_file"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `document_masters`
- **SQLAlchemy Models**: `DocumentMaster`
- **Operations Performed**: `INSERT`
- **Key Columns Referenced**: `document_masters.language_id`, `document_masters.status`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: Yes (Multipart)

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\document\services\DocumentServices.js` (Line 81)
  - Snippet: `API.post(         `/documents/${documentId}/translation/save`,         payload,         {           `

---

## Match Making

Total endpoints in module: **20**

### `GET` /match-making/

- **Summary**: Get All
- **Router / Handler**: [`get_all`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/router/match_making_route.py#L34) in `Backend\app\modules\assessment\router\match_making_route.py` (Line 34)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `any` | No | `None` | - |
| `search` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[MatchMakingResponse]`

**Example Success Response:**
```json
[
  {
    "parent_id": 1,
    "match_making_question_title": "sample_match_making_question_title",
    "match_making_question_description": "sample_match_making_question_description",
    "image_url": "sample_image_url",
    "marks": "sample_marks",
    "status": 1,
    "language_id": 1,
    "match_making_id": "sample_match_making_id",
    "created_at": "sample_created_at",
    "updated_at": "sample_updated_at",
    "deleted_at": "sample_deleted_at",
    "is_translation": true
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\MatchMaking\services\MatchingMakingService.js` (Line 19)
  - Snippet: `API.get("/match-making/", {         params,     });      return response.d`

---

### `GET` /match-making/{parent_id}

- **Summary**: Get By Id
- **Router / Handler**: [`get_by_id`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/router/match_making_route.py#L50) in `Backend\app\modules\assessment\router\match_making_route.py` (Line 50)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `parent_id` | `integer` | Yes | - |

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `integer` | Yes | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `MatchMakingResponse`

**Example Success Response:**
```json
{
  "parent_id": 1,
  "match_making_question_title": "sample_match_making_question_title",
  "match_making_question_description": "sample_match_making_question_description",
  "image_url": "sample_image_url",
  "marks": "sample_marks",
  "status": 1,
  "language_id": 1,
  "match_making_id": "sample_match_making_id",
  "created_at": "sample_created_at",
  "updated_at": "sample_updated_at",
  "deleted_at": "sample_deleted_at",
  "is_translation": true
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\MatchMaking\services\MatchingMakingService.js` (Line 30)
  - Snippet: `API.get(         `/match-making/${parentId}`,         {             params: {                 `

---

### `POST` /match-making/

- **Summary**: Create
- **Router / Handler**: [`create`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/router/match_making_route.py#L66) in `Backend\app\modules\assessment\router\match_making_route.py` (Line 66)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `MatchMakingCreate`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `parent_id` | `integer` | No | `0` | - |
| `match_making_question_title` | `string` | Yes | `None` | - |
| `match_making_question_description` | `any` | No | `None` | - |
| `image_url` | `any` | No | `None` | - |
| `marks` | `any` | Yes | `None` | - |
| `status` | `integer` | Yes | `None` | - |
| `language_id` | `integer` | Yes | `None` | - |

**Example Request Payload:**
```json
{
  "parent_id": 1,
  "match_making_question_title": "sample_match_making_question_title",
  "match_making_question_description": "sample_match_making_question_description",
  "image_url": "sample_image_url",
  "marks": "sample_marks",
  "status": 1,
  "language_id": 1
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `MatchMakingResponse`

**Example Success Response:**
```json
{
  "parent_id": 1,
  "match_making_question_title": "sample_match_making_question_title",
  "match_making_question_description": "sample_match_making_question_description",
  "image_url": "sample_image_url",
  "marks": "sample_marks",
  "status": 1,
  "language_id": 1,
  "match_making_id": "sample_match_making_id",
  "created_at": "sample_created_at",
  "updated_at": "sample_updated_at",
  "deleted_at": "sample_deleted_at",
  "is_translation": true
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `INSERT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\MatchMaking\services\MatchingMakingService.js` (Line 43)
  - Snippet: `API.post(         "/match-making/",         data     );      return response.data; }`

---

### `PUT` /match-making/{match_making_id}

- **Summary**: Update
- **Router / Handler**: [`update`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/router/match_making_route.py#L80) in `Backend\app\modules\assessment\router\match_making_route.py` (Line 80)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `match_making_id` | `integer` | Yes | - |

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `MatchMakingUpdate`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `match_making_question_title` | `any` | No | `None` | - |
| `match_making_question_description` | `any` | No | `None` | - |
| `image_url` | `any` | No | `None` | - |
| `marks` | `any` | No | `None` | - |
| `status` | `any` | No | `None` | - |
| `language_id` | `any` | No | `None` | - |

**Example Request Payload:**
```json
{
  "match_making_question_title": "sample_match_making_question_title",
  "match_making_question_description": "sample_match_making_question_description",
  "image_url": "sample_image_url",
  "marks": "sample_marks",
  "status": "sample_status",
  "language_id": "sample_language_id"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `MatchMakingResponse`

**Example Success Response:**
```json
{
  "parent_id": 1,
  "match_making_question_title": "sample_match_making_question_title",
  "match_making_question_description": "sample_match_making_question_description",
  "image_url": "sample_image_url",
  "marks": "sample_marks",
  "status": 1,
  "language_id": 1,
  "match_making_id": "sample_match_making_id",
  "created_at": "sample_created_at",
  "updated_at": "sample_updated_at",
  "deleted_at": "sample_deleted_at",
  "is_translation": true
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `UPDATE`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\MatchMaking\services\MatchingMakingService.js` (Line 55)
  - Snippet: `API.put(         `/match-making/${matchMakingId}`,         data     );      return response.data; }`

---

### `DELETE` /match-making/{match_making_id}

- **Summary**: Delete
- **Router / Handler**: [`delete`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/router/match_making_route.py#L96) in `Backend\app\modules\assessment\router\match_making_route.py` (Line 96)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `match_making_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `DELETE`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\MatchMaking\services\MatchingMakingService.js` (Line 66)
  - Snippet: `API.delete(         `/match-making/${matchMakingId}`     );      return response.data; };  // ======`

---

### `GET` /match-making/{match_making_id}/left-items

- **Summary**: Get Left Items
- **Router / Handler**: [`get_left_items`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/router/match_making_route.py#L114) in `Backend\app\modules\assessment\router\match_making_route.py` (Line 114)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `match_making_id` | `integer` | Yes | - |

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[MatchLeftItemResponse]`

**Example Success Response:**
```json
[
  {
    "match_left_text": "sample_match_left_text",
    "sort_order": "sample_sort_order",
    "language_id": 1,
    "match_left_id": 1,
    "match_making_id": 1,
    "created_at": "sample_created_at",
    "updated_at": "sample_updated_at",
    "deleted_at": "sample_deleted_at"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\MatchMaking\services\MatchingMakingService.js` (Line 81)
  - Snippet: `API.get(         `/match-making/${matchMakingId}/left-items`,         {             params: {       `

---

### `POST` /match-making/{match_making_id}/left-items

- **Summary**: Create Left Item
- **Router / Handler**: [`create_left_item`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/router/match_making_route.py#L130) in `Backend\app\modules\assessment\router\match_making_route.py` (Line 130)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `match_making_id` | `integer` | Yes | - |

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `MatchLeftItemCreate`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `match_left_text` | `string` | Yes | `None` | - |
| `sort_order` | `any` | No | `None` | - |
| `language_id` | `integer` | Yes | `None` | - |

**Example Request Payload:**
```json
{
  "match_left_text": "sample_match_left_text",
  "sort_order": "sample_sort_order",
  "language_id": 1
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `MatchLeftItemResponse`

**Example Success Response:**
```json
{
  "match_left_text": "sample_match_left_text",
  "sort_order": "sample_sort_order",
  "language_id": 1,
  "match_left_id": 1,
  "match_making_id": 1,
  "created_at": "sample_created_at",
  "updated_at": "sample_updated_at",
  "deleted_at": "sample_deleted_at"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `INSERT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\MatchMaking\services\MatchingMakingService.js` (Line 98)
  - Snippet: `API.post(         `/match-making/${matchMakingId}/left-items`,         data     );      return respo`

---

### `GET` /match-making/left-items/{match_left_id}

- **Summary**: Get Left Item By Id
- **Router / Handler**: [`get_left_item_by_id`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/router/match_making_route.py#L146) in `Backend\app\modules\assessment\router\match_making_route.py` (Line 146)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `match_left_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `MatchLeftItemResponse`

**Example Success Response:**
```json
{
  "match_left_text": "sample_match_left_text",
  "sort_order": "sample_sort_order",
  "language_id": 1,
  "match_left_id": 1,
  "match_making_id": 1,
  "created_at": "sample_created_at",
  "updated_at": "sample_updated_at",
  "deleted_at": "sample_deleted_at"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\MatchMaking\services\MatchingMakingService.js` (Line 109)
  - Snippet: `API.get(         `/match-making/left-items/${matchLeftId}`     );      return response.data; };  exp`

---

### `PUT` /match-making/left-items/{match_left_id}

- **Summary**: Update Left Item
- **Router / Handler**: [`update_left_item`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/router/match_making_route.py#L160) in `Backend\app\modules\assessment\router\match_making_route.py` (Line 160)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `match_left_id` | `integer` | Yes | - |

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `MatchLeftItemUpdate`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `match_left_text` | `any` | No | `None` | - |
| `sort_order` | `any` | No | `None` | - |
| `language_id` | `any` | No | `None` | - |

**Example Request Payload:**
```json
{
  "match_left_text": "sample_match_left_text",
  "sort_order": "sample_sort_order",
  "language_id": "sample_language_id"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `MatchLeftItemResponse`

**Example Success Response:**
```json
{
  "match_left_text": "sample_match_left_text",
  "sort_order": "sample_sort_order",
  "language_id": 1,
  "match_left_id": 1,
  "match_making_id": 1,
  "created_at": "sample_created_at",
  "updated_at": "sample_updated_at",
  "deleted_at": "sample_deleted_at"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `UPDATE`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\MatchMaking\services\MatchingMakingService.js` (Line 120)
  - Snippet: `API.put(         `/match-making/left-items/${matchLeftId}`,         data     );      return response`

---

### `DELETE` /match-making/left-items/{match_left_id}

- **Summary**: Delete Left Item
- **Router / Handler**: [`delete_left_item`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/router/match_making_route.py#L176) in `Backend\app\modules\assessment\router\match_making_route.py` (Line 176)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `match_left_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `DELETE`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\MatchMaking\services\MatchingMakingService.js` (Line 131)
  - Snippet: `API.delete(         `/match-making/left-items/${matchLeftId}`     );      return response.data; };  `

---

### `GET` /match-making/{match_making_id}/right-items

- **Summary**: Get Right Items
- **Router / Handler**: [`get_right_items`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/router/match_making_route.py#L189) in `Backend\app\modules\assessment\router\match_making_route.py` (Line 189)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `match_making_id` | `integer` | Yes | - |

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[MatchRightItemResponse]`

**Example Success Response:**
```json
[
  {
    "match_right_text": "sample_match_right_text",
    "sort_order": "sample_sort_order",
    "language_id": 1,
    "match_right_id": 1,
    "match_making_id": 1,
    "created_at": "sample_created_at",
    "updated_at": "sample_updated_at",
    "deleted_at": "sample_deleted_at"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\MatchMaking\services\MatchingMakingService.js` (Line 146)
  - Snippet: `API.get(         `/match-making/${matchMakingId}/right-items`,         {             params: {      `

---

### `POST` /match-making/{match_making_id}/right-items

- **Summary**: Create Right Item
- **Router / Handler**: [`create_right_item`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/router/match_making_route.py#L205) in `Backend\app\modules\assessment\router\match_making_route.py` (Line 205)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `match_making_id` | `integer` | Yes | - |

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `MatchRightItemCreate`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `match_right_text` | `string` | Yes | `None` | - |
| `sort_order` | `any` | No | `None` | - |
| `language_id` | `integer` | Yes | `None` | - |

**Example Request Payload:**
```json
{
  "match_right_text": "sample_match_right_text",
  "sort_order": "sample_sort_order",
  "language_id": 1
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `MatchRightItemResponse`

**Example Success Response:**
```json
{
  "match_right_text": "sample_match_right_text",
  "sort_order": "sample_sort_order",
  "language_id": 1,
  "match_right_id": 1,
  "match_making_id": 1,
  "created_at": "sample_created_at",
  "updated_at": "sample_updated_at",
  "deleted_at": "sample_deleted_at"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `INSERT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\MatchMaking\services\MatchingMakingService.js` (Line 163)
  - Snippet: `API.post(         `/match-making/${matchMakingId}/right-items`,         data     );      return resp`

---

### `GET` /match-making/right-items/{match_right_id}

- **Summary**: Get Right Item By Id
- **Router / Handler**: [`get_right_item_by_id`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/router/match_making_route.py#L221) in `Backend\app\modules\assessment\router\match_making_route.py` (Line 221)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `match_right_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `MatchRightItemResponse`

**Example Success Response:**
```json
{
  "match_right_text": "sample_match_right_text",
  "sort_order": "sample_sort_order",
  "language_id": 1,
  "match_right_id": 1,
  "match_making_id": 1,
  "created_at": "sample_created_at",
  "updated_at": "sample_updated_at",
  "deleted_at": "sample_deleted_at"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\MatchMaking\services\MatchingMakingService.js` (Line 174)
  - Snippet: `API.get(         `/match-making/right-items/${matchRightId}`     );      return response.data; };  e`

---

### `PUT` /match-making/right-items/{match_right_id}

- **Summary**: Update Right Item
- **Router / Handler**: [`update_right_item`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/router/match_making_route.py#L235) in `Backend\app\modules\assessment\router\match_making_route.py` (Line 235)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `match_right_id` | `integer` | Yes | - |

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `MatchRightItemUpdate`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `match_right_text` | `any` | No | `None` | - |
| `sort_order` | `any` | No | `None` | - |
| `language_id` | `any` | No | `None` | - |

**Example Request Payload:**
```json
{
  "match_right_text": "sample_match_right_text",
  "sort_order": "sample_sort_order",
  "language_id": "sample_language_id"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `MatchRightItemResponse`

**Example Success Response:**
```json
{
  "match_right_text": "sample_match_right_text",
  "sort_order": "sample_sort_order",
  "language_id": 1,
  "match_right_id": 1,
  "match_making_id": 1,
  "created_at": "sample_created_at",
  "updated_at": "sample_updated_at",
  "deleted_at": "sample_deleted_at"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `UPDATE`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\MatchMaking\services\MatchingMakingService.js` (Line 185)
  - Snippet: `API.put(         `/match-making/right-items/${matchRightId}`,         data     );      return respon`

---

### `DELETE` /match-making/right-items/{match_right_id}

- **Summary**: Delete Right Item
- **Router / Handler**: [`delete_right_item`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/router/match_making_route.py#L251) in `Backend\app\modules\assessment\router\match_making_route.py` (Line 251)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `match_right_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `DELETE`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\MatchMaking\services\MatchingMakingService.js` (Line 196)
  - Snippet: `API.delete(         `/match-making/right-items/${matchRightId}`     );      return response.data; };`

---

### `GET` /match-making/{match_making_id}/correct-answers

- **Summary**: Get All
- **Router / Handler**: [`get_all`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/router/match_correct_answer_route.py#L32) in `Backend\app\modules\assessment\router\match_correct_answer_route.py` (Line 32)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `match_making_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[MatchCorrectAnswerResponse]`

**Example Success Response:**
```json
[
  {
    "match_left_id": 1,
    "match_right_id": 1,
    "match_correct_answers_id": 1,
    "match_making_id": 1,
    "created_at": "sample_created_at",
    "updated_at": "sample_updated_at",
    "deleted_at": "sample_deleted_at"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\MatchMaking\services\MatchingMakingService.js` (Line 209)
  - Snippet: `API.get(         `/match-making/${matchMakingId}/correct-answers`     );       return response.data;`

---

### `GET` /match-making/correct-answers/{match_correct_answers_id}

- **Summary**: Get By Id
- **Router / Handler**: [`get_by_id`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/router/match_correct_answer_route.py#L51) in `Backend\app\modules\assessment\router\match_correct_answer_route.py` (Line 51)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `match_correct_answers_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `MatchCorrectAnswerResponse`

**Example Success Response:**
```json
{
  "match_left_id": 1,
  "match_right_id": 1,
  "match_correct_answers_id": 1,
  "match_making_id": 1,
  "created_at": "sample_created_at",
  "updated_at": "sample_updated_at",
  "deleted_at": "sample_deleted_at"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `match_correct_answers`
- **SQLAlchemy Models**: `MatchCorrectAnswer`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `match_correct_answers.match_correct_answers_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\MatchMaking\services\MatchingMakingService.js` (Line 233)
  - Snippet: `API.get(         `/match-making/correct-answers/${correctAnswerId}`     );      return response.data`

---

### `POST` /match-making/{match_making_id}/correct-answers

- **Summary**: Create
- **Router / Handler**: [`create`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/router/match_correct_answer_route.py#L70) in `Backend\app\modules\assessment\router\match_correct_answer_route.py` (Line 70)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `match_making_id` | `integer` | Yes | - |

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `MatchCorrectAnswerCreate`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `match_left_id` | `integer` | Yes | `None` | - |
| `match_right_id` | `integer` | Yes | `None` | - |

**Example Request Payload:**
```json
{
  "match_left_id": 1,
  "match_right_id": 1
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `MatchCorrectAnswerResponse`

**Example Success Response:**
```json
{
  "match_left_id": 1,
  "match_right_id": 1,
  "match_correct_answers_id": 1,
  "match_making_id": 1,
  "created_at": "sample_created_at",
  "updated_at": "sample_updated_at",
  "deleted_at": "sample_deleted_at"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `INSERT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\MatchMaking\services\MatchingMakingService.js` (Line 222)
  - Snippet: `API.post(         `/match-making/${matchMakingId}/correct-answers`,         data     );      return `

---

### `PUT` /match-making/correct-answers/{match_correct_answers_id}

- **Summary**: Update
- **Router / Handler**: [`update`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/router/match_correct_answer_route.py#L91) in `Backend\app\modules\assessment\router\match_correct_answer_route.py` (Line 91)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `match_correct_answers_id` | `integer` | Yes | - |

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `MatchCorrectAnswerUpdate`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `match_left_id` | `any` | No | `None` | - |
| `match_right_id` | `any` | No | `None` | - |

**Example Request Payload:**
```json
{
  "match_left_id": "sample_match_left_id",
  "match_right_id": "sample_match_right_id"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `MatchCorrectAnswerResponse`

**Example Success Response:**
```json
{
  "match_left_id": 1,
  "match_right_id": 1,
  "match_correct_answers_id": 1,
  "match_making_id": 1,
  "created_at": "sample_created_at",
  "updated_at": "sample_updated_at",
  "deleted_at": "sample_deleted_at"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `match_correct_answers`
- **SQLAlchemy Models**: `MatchCorrectAnswer`
- **Operations Performed**: `UPDATE`
- **Key Columns Referenced**: `match_correct_answers.match_correct_answers_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\MatchMaking\services\MatchingMakingService.js` (Line 244)
  - Snippet: `API.put(         `/match-making/correct-answers/${correctAnswerId}`,         data     );      return`

---

### `DELETE` /match-making/correct-answers/{match_correct_answers_id}

- **Summary**: Delete
- **Router / Handler**: [`delete`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/assessment/router/match_correct_answer_route.py#L112) in `Backend\app\modules\assessment\router\match_correct_answer_route.py` (Line 112)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: ASSESSMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `match_correct_answers_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `match_correct_answers`
- **SQLAlchemy Models**: `MatchCorrectAnswer`
- **Operations Performed**: `DELETE`
- **Key Columns Referenced**: `match_correct_answers.match_correct_answers_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\assessment\MatchMaking\services\MatchingMakingService.js` (Line 255)
  - Snippet: `API.delete(         `/match-making/correct-answers/${correctAnswerId}`     );      return response.d`

---

## Mobile Activity

Total endpoints in module: **4**

### `POST` /activity/time-spent

- **Summary**: N/A
- **Description**: Whole-session time, in minutes → participant_time_spent_log.
- **Router / Handler**: [`log_time_spent`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/mobile/activity/routes.py#L25) in `Backend\app\modules\mobile\activity\routes.py` (Line 25)
- **Authentication**: `Bearer Token (Participant JWT)`
- **Allowed Roles**: Trainee / Participant
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Unused by Web Frontend (no frontend service or page calls this endpoint).

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `201`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `INSERT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

No matching frontend service call found in `Frontend/src` (Backend-only / Unused by web frontend).

---

### `POST` /activity/module-time

- **Summary**: N/A
- **Description**: Seconds spent on a module/topic/document → time_spent_module_log.
- **Router / Handler**: [`log_module_time`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/mobile/activity/routes.py#L43) in `Backend\app\modules\mobile\activity\routes.py` (Line 43)
- **Authentication**: `Bearer Token (Participant JWT)`
- **Allowed Roles**: Trainee / Participant
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Unused by Web Frontend (no frontend service or page calls this endpoint).

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `201`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `INSERT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

No matching frontend service call found in `Frontend/src` (Backend-only / Unused by web frontend).

---

### `GET` /activity/video-questions/{video_id}

- **Summary**: N/A
- **Description**: The post-video questions for a video, in the requested language.
- **Router / Handler**: [`get_video_questions`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/mobile/activity/routes.py#L61) in `Backend\app\modules\mobile\activity\routes.py` (Line 61)
- **Authentication**: `Bearer Token (Participant JWT)`
- **Allowed Roles**: Trainee / Participant
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Unused by Web Frontend (no frontend service or page calls this endpoint).

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

No matching frontend service call found in `Frontend/src` (Backend-only / Unused by web frontend).

---

### `POST` /activity/video-question

- **Summary**: N/A
- **Description**: Store a participant's post-video answers → post_video_question_score.
- **Router / Handler**: [`submit_video_answers`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/mobile/activity/routes.py#L79) in `Backend\app\modules\mobile\activity\routes.py` (Line 79)
- **Authentication**: `Bearer Token (Participant JWT)`
- **Allowed Roles**: Trainee / Participant
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Unused by Web Frontend (no frontend service or page calls this endpoint).

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `INSERT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

No matching frontend service call found in `Frontend/src` (Backend-only / Unused by web frontend).

---

## Mobile Assessment

Total endpoints in module: **2**

### `GET` /assessment/{module_id}

- **Summary**: N/A
- **Description**: Every pre-session or post-session question for the module: MCQ, SCQ, drop bucket and
match making, in one ordered list.
- **Router / Handler**: [`get_module_assessment`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/mobile/assessment/routes.py#L23) in `Backend\app\modules\mobile\assessment\routes.py` (Line 23)
- **Authentication**: `Bearer Token (Participant JWT)`
- **Allowed Roles**: Trainee / Participant
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Unused by Web Frontend (no frontend service or page calls this endpoint).

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

No matching frontend service call found in `Frontend/src` (Backend-only / Unused by web frontend).

---

### `POST` /assessment/{module_id}/submit

- **Summary**: N/A
- **Router / Handler**: [`submit_module_assessment`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/mobile/assessment/routes.py#L46) in `Backend\app\modules\mobile\assessment\routes.py` (Line 46)
- **Authentication**: `Bearer Token (Participant JWT)`
- **Allowed Roles**: Trainee / Participant
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Unused by Web Frontend (no frontend service or page calls this endpoint).

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `INSERT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

No matching frontend service call found in `Frontend/src` (Backend-only / Unused by web frontend).

---

## Mobile Authentication

Total endpoints in module: **7**

### `POST` /mobile/auth/login

- **Summary**: Login
- **Router / Handler**: [`login`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/mobile/auth/router.py#L30) in `Backend\app\modules\mobile\auth\router.py` (Line 30)
- **Authentication**: `Public (None)`
- **Allowed Roles**: Public / Open
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Mobile App Endpoint (used by mobile client).

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `MobileLoginRequest`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `username` | `string` | Yes | `None` | Participant username |
| `password` | `string` | Yes | `None` | Participant password |

**Example Request Payload:**
```json
{
  "username": "sample_username",
  "password": "SecurePassword123"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `app__modules__mobile__auth__schema__LoginResponse`

**Example Success Response:**
```json
{
  "access_token": "sample_access_token",
  "refresh_token": "sample_refresh_token",
  "token_type": "sample_token_type",
  "participant": "sample_participant"
}
```

- **Possible Error Status Codes**: `400`, `404`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `participantmasters`
- **SQLAlchemy Models**: `ParticipantMaster`
- **Operations Performed**: `INSERT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

Dedicated mobile app endpoint (not invoked by web dashboard).

---

### `POST` /mobile/auth/refresh

- **Summary**: Refresh Token
- **Router / Handler**: [`refresh_token`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/mobile/auth/router.py#L44) in `Backend\app\modules\mobile\auth\router.py` (Line 44)
- **Authentication**: `Public (None)`
- **Allowed Roles**: Public / Open
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Mobile App Endpoint (used by mobile client).

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `app__modules__mobile__auth__schema__RefreshTokenRequest`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `refresh_token` | `string` | Yes | `None` | Refresh token |

**Example Request Payload:**
```json
{
  "refresh_token": "sample_refresh_token"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `app__modules__mobile__auth__schema__RefreshTokenResponse`

**Example Success Response:**
```json
{
  "access_token": "sample_access_token",
  "refresh_token": "sample_refresh_token",
  "token_type": "sample_token_type"
}
```

- **Possible Error Status Codes**: `400`, `404`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `INSERT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

Dedicated mobile app endpoint (not invoked by web dashboard).

---

### `POST` /mobile/auth/logout

- **Summary**: Logout
- **Router / Handler**: [`logout`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/mobile/auth/router.py#L58) in `Backend\app\modules\mobile\auth\router.py` (Line 58)
- **Authentication**: `Public (None)`
- **Allowed Roles**: Public / Open
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Mobile App Endpoint (used by mobile client).

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `LogoutResponse`

**Example Success Response:**
```json
{
  "message": "sample_message"
}
```

- **Possible Error Status Codes**: `400`, `404`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `INSERT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

Dedicated mobile app endpoint (not invoked by web dashboard).

---

### `GET` /mobile/auth/me

- **Summary**: Get Me
- **Router / Handler**: [`get_me`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/mobile/auth/router.py#L66) in `Backend\app\modules\mobile\auth\router.py` (Line 66)
- **Authentication**: `Bearer Token (Participant JWT)`
- **Allowed Roles**: Trainee / Participant
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Mobile App Endpoint (used by mobile client).

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `ParticipantResponse`

**Example Success Response:**
```json
{
  "participant_id": 1,
  "enrollment_no": "sample_enrollment_no",
  "participant_name": "sample_participant_name",
  "username": "sample_username",
  "email": "user@example.com",
  "mobile_no": "sample_mobile_no",
  "images": "sample_images",
  "progress_status": "sample_progress_status",
  "course_progress": "sample_course_progress"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

Dedicated mobile app endpoint (not invoked by web dashboard).

---

### `POST` /mobile/auth/forgot-password

- **Summary**: Forgot Password
- **Router / Handler**: [`forgot_password`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/mobile/auth/router.py#L80) in `Backend\app\modules\mobile\auth\router.py` (Line 80)
- **Authentication**: `Public (None)`
- **Allowed Roles**: Public / Open
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Mobile App Endpoint (used by mobile client).

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `app__modules__mobile__auth__schema__ForgotPasswordRequest`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `username` | `string` | Yes | `None` | Participant username. Used rather than email because most participants have no email on record. |

**Example Request Payload:**
```json
{
  "username": "sample_username"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `app__modules__mobile__auth__schema__ForgotPasswordResponse`

**Example Success Response:**
```json
{
  "message": "sample_message",
  "reset_token": "sample_reset_token",
  "expires_in_minutes": 1
}
```

- **Possible Error Status Codes**: `400`, `404`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `INSERT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

Dedicated mobile app endpoint (not invoked by web dashboard).

---

### `POST` /mobile/auth/reset-password

- **Summary**: Reset Password
- **Router / Handler**: [`reset_password`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/mobile/auth/router.py#L94) in `Backend\app\modules\mobile\auth\router.py` (Line 94)
- **Authentication**: `Public (None)`
- **Allowed Roles**: Public / Open
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Mobile App Endpoint (used by mobile client).

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `app__modules__mobile__auth__schema__ResetPasswordRequest`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `reset_token` | `string` | Yes | `None` | - |
| `new_password` | `string` | Yes | `None` | - |
| `confirm_password` | `string` | Yes | `None` | - |

**Example Request Payload:**
```json
{
  "reset_token": "sample_reset_token",
  "new_password": "SecurePassword123",
  "confirm_password": "SecurePassword123"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `ResetPasswordResponse`

**Example Success Response:**
```json
{
  "message": "sample_message"
}
```

- **Possible Error Status Codes**: `400`, `404`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `INSERT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

Dedicated mobile app endpoint (not invoked by web dashboard).

---

### `POST` /mobile/auth/change-password

- **Summary**: Change Password
- **Router / Handler**: [`change_password`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/mobile/auth/router.py#L110) in `Backend\app\modules\mobile\auth\router.py` (Line 110)
- **Authentication**: `Bearer Token (Participant JWT)`
- **Allowed Roles**: Trainee / Participant
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Mobile App Endpoint (used by mobile client).

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `ChangePasswordRequest`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `current_password` | `string` | Yes | `None` | - |
| `new_password` | `string` | Yes | `None` | - |
| `confirm_password` | `string` | Yes | `None` | - |

**Example Request Payload:**
```json
{
  "current_password": "SecurePassword123",
  "new_password": "SecurePassword123",
  "confirm_password": "SecurePassword123"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `ResetPasswordResponse`

**Example Success Response:**
```json
{
  "message": "sample_message"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `INSERT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

Dedicated mobile app endpoint (not invoked by web dashboard).

---

## Mobile Dashboard

Total endpoints in module: **2**

### `GET` /mobile/dashboard/stats

- **Summary**: Get Dashboard Stats
- **Router / Handler**: [`get_dashboard_stats`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/mobile/dashboard/routes.py#L19) in `Backend\app\modules\mobile\dashboard\routes.py` (Line 19)
- **Authentication**: `Bearer Token (Participant JWT)`
- **Allowed Roles**: Trainee / Participant
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Mobile App Endpoint (used by mobile client).

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `DashboardStatsResponse`

**Example Success Response:**
```json
{
  "modules_completed": 1,
  "total_modules": 1,
  "average_score": "sample_average_score",
  "questions_attempted": 1,
  "time_invested_minutes": 1,
  "time_invested_seconds": 1,
  "overall_progress": "sample_overall_progress"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

Dedicated mobile app endpoint (not invoked by web dashboard).

---

### `GET` /mobile/dashboard/tips

- **Summary**: Get Dashboard Tips
- **Description**: "Did You Know" safety tips shown on the dashboard.
- **Router / Handler**: [`get_dashboard_tips`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/mobile/dashboard/routes.py#L33) in `Backend\app\modules\mobile\dashboard\routes.py` (Line 33)
- **Authentication**: `Bearer Token (Participant JWT)`
- **Allowed Roles**: Trainee / Participant
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Mobile App Endpoint (used by mobile client).

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `integer` | No | `1` | language_master.language_id (1 = English) |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[DidYouKnowItem]`

**Example Success Response:**
```json
[
  {
    "didyouknow_id": 1,
    "text": "sample_text",
    "image_url": "sample_image_url",
    "language_id": "sample_language_id"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

Dedicated mobile app endpoint (not invoked by web dashboard).

---

## Mobile Feedback

Total endpoints in module: **3**

### `POST` /mobile/feedback/submit

- **Summary**: Submit Feedback
- **Router / Handler**: [`submit_feedback`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/mobile/feedback/routes.py#L22) in `Backend\app\modules\mobile\feedback\routes.py` (Line 22)
- **Authentication**: `Bearer Token (Participant JWT)`
- **Allowed Roles**: Trainee / Participant
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Mobile App Endpoint (used by mobile client).

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `FeedbackCreate`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `lms_experience` | `any` | No | `None` | - |
| `lms_ease` | `any` | No | `None` | - |
| `useful_modules` | `array` | No | `None` | - |
| `mood_answers` | `array` | No | `None` | - |
| `form_answers` | `object` | No | `None` | - |

**Example Request Payload:**
```json
{
  "lms_experience": "sample_lms_experience",
  "lms_ease": "sample_lms_ease",
  "useful_modules": [],
  "mood_answers": [],
  "form_answers": "sample_form_answers"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `FeedbackResponse`

**Example Success Response:**
```json
{
  "feedback_id": 1,
  "message": "sample_message"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `INSERT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

Dedicated mobile app endpoint (not invoked by web dashboard).

---

### `GET` /mobile/feedback/form

- **Summary**: Get Feedback Form
- **Description**: Returns the full 10-question feedback form
in the selected language.
- **Router / Handler**: [`get_feedback_form`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/mobile/feedback/routes.py#L38) in `Backend\app\modules\mobile\feedback\routes.py` (Line 38)
- **Authentication**: `Bearer Token (Participant JWT)`
- **Allowed Roles**: Trainee / Participant
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Mobile App Endpoint (used by mobile client).

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `integer` | No | `1` | language_master.language_id (1 = English, 2 = Hindi, 3 = Bangla, 4 = Tamil) |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[FeedbackFormField]`

**Example Success Response:**
```json
[
  {
    "field": "sample_field",
    "question": "sample_question",
    "type": "sample_type",
    "options": []
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `participant_feedback`
- **SQLAlchemy Models**: `ParticipantFeedback`
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

Dedicated mobile app endpoint (not invoked by web dashboard).

---

### `GET` /mobile/feedback/questions

- **Summary**: Get Feedback Questions
- **Description**: Returns the mood questions shown after login
in the selected language.
- **Router / Handler**: [`get_feedback_questions`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/mobile/feedback/routes.py#L60) in `Backend\app\modules\mobile\feedback\routes.py` (Line 60)
- **Authentication**: `Bearer Token (Participant JWT)`
- **Allowed Roles**: Trainee / Participant
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Mobile App Endpoint (used by mobile client).

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `integer` | No | `1` | language_master.language_id (1 = English, 2 = Hindi, 3 = Bangla, 4 = Tamil) |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[MoodQuestionResponse]`

**Example Success Response:**
```json
[
  {
    "question_id": 1,
    "question_name": "sample_question_name",
    "question_description": "sample_question_description",
    "question_type": "sample_question_type",
    "language_id": 1,
    "options": []
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

Dedicated mobile app endpoint (not invoked by web dashboard).

---

## Mobile Media

Total endpoints in module: **3**

### `GET` /media/pptx/info

- **Summary**: N/A
- **Description**: Render a deck (once, then cached) and report where its slides live, so
the app can show them inline instead of handing the file to another app.
- **Router / Handler**: [`get_pptx_info`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/mobile/media/routes.py#L44) in `Backend\app\modules\mobile\media\routes.py` (Line 44)
- **Authentication**: `Public (None)`
- **Allowed Roles**: Public / Open
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Unused by Web Frontend (no frontend service or page calls this endpoint).

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `404`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

No matching frontend service call found in `Frontend/src` (Backend-only / Unused by web frontend).

---

### `GET` /media/pptx/slide/{number}

- **Summary**: N/A
- **Description**: One rendered slide as a PNG.
- **Router / Handler**: [`get_pptx_slide`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/mobile/media/routes.py#L69) in `Backend\app\modules\mobile\media\routes.py` (Line 69)
- **Authentication**: `Public (None)`
- **Allowed Roles**: Public / Open
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Unused by Web Frontend (no frontend service or page calls this endpoint).

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `404`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

No matching frontend service call found in `Frontend/src` (Backend-only / Unused by web frontend).

---

### `GET` /media/{file_path:path}

- **Summary**: N/A
- **Description**: Stream a stored file.

Honours the Range header, which is what lets a video player seek and
what some players require before they will start at all.
- **Router / Handler**: [`get_media`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/mobile/media/routes.py#L95) in `Backend\app\modules\mobile\media\routes.py` (Line 95)
- **Authentication**: `Public (None)`
- **Allowed Roles**: Public / Open
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Unused by Web Frontend (no frontend service or page calls this endpoint).

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `404`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

No matching frontend service call found in `Frontend/src` (Backend-only / Unused by web frontend).

---

## Mobile Module

Total endpoints in module: **4**

### `GET` /mobile/module/list

- **Summary**: List Modules
- **Router / Handler**: [`list_modules`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/mobile/module/routes.py#L37) in `Backend\app\modules\mobile\module\routes.py` (Line 37)
- **Authentication**: `Bearer Token (Participant JWT)`
- **Allowed Roles**: Trainee / Participant
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Mobile App Endpoint (used by mobile client).

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `integer` | No | `1` | language_master.language_id (1 = English) |
| `module_type` | `any` | No | `None` | module_type.module_type_id (1 = Technical) |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `ModuleListResponse`

**Example Success Response:**
```json
{
  "language_id": 1,
  "total": 1,
  "completed": 1,
  "modules": []
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

Dedicated mobile app endpoint (not invoked by web dashboard).

---

### `GET` /mobile/module/types

- **Summary**: List Module Types
- **Router / Handler**: [`list_module_types`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/mobile/module/routes.py#L63) in `Backend\app\modules\mobile\module\routes.py` (Line 63)
- **Authentication**: `Bearer Token (Participant JWT)`
- **Allowed Roles**: Trainee / Participant
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Mobile App Endpoint (used by mobile client).

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[ModuleTypeItem]`

**Example Success Response:**
```json
[
  {
    "module_type_id": 1,
    "module_type": "sample_module_type"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `language_master`, `module_masters`, `module_type`, `participant_module`
- **SQLAlchemy Models**: `LanguageMaster`, `ModuleMaster`, `ModuleType`, `ParticipantModule`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `module_masters.module_type`, `module_type.module_type`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

Dedicated mobile app endpoint (not invoked by web dashboard).

---

### `GET` /mobile/module/languages

- **Summary**: List Languages
- **Description**: Languages the participant can switch the app content to. Lives under the
module prefix because language selection only affects module content.
- **Router / Handler**: [`list_languages`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/mobile/module/routes.py#L74) in `Backend\app\modules\mobile\module\routes.py` (Line 74)
- **Authentication**: `Bearer Token (Participant JWT)`
- **Allowed Roles**: Trainee / Participant
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Mobile App Endpoint (used by mobile client).

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[LanguageItem]`

**Example Success Response:**
```json
[
  {
    "language_id": 1,
    "language_code": "sample_language_code",
    "language_name": "sample_language_name"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `language_master`, `module_masters`, `module_type`, `participant_module`
- **SQLAlchemy Models**: `LanguageMaster`, `ModuleMaster`, `ModuleType`, `ParticipantModule`
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

Dedicated mobile app endpoint (not invoked by web dashboard).

---

### `GET` /mobile/module/{module_id}/topics

- **Summary**: List Module Topics
- **Router / Handler**: [`list_module_topics`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/mobile/module/routes.py#L89) in `Backend\app\modules\mobile\module\routes.py` (Line 89)
- **Authentication**: `Bearer Token (Participant JWT)`
- **Allowed Roles**: Trainee / Participant
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Mobile App Endpoint (used by mobile client).

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `module_id` | `integer` | Yes | - |

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `integer` | No | `1` | language_master.language_id (1 = English) |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `ModuleTopicsResponse`

**Example Success Response:**
```json
{
  "module_id": 1,
  "language_id": 1,
  "total": 1,
  "module": "sample_module",
  "self_paced_topics": [],
  "topics": []
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `assessment_mapping`, `document_masters`, `module_masters`, `pdf_masters`, `ppt_masters`, `pre_session_assessment`, `self_paced_learning`, `topic_mapping`, `topic_master`, `video_masters`
- **SQLAlchemy Models**: `AssessmentMapping`, `DocumentMaster`, `ModuleMaster`, `PdfMaster`, `PptMaster`, `PreSessionAssessment`, `SelfPacedLearning`, `TopicMapping`, `TopicMaster`, `VideoMaster`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `document_masters.language_id`, `document_masters.module_id`, `module_masters.language_id`, `module_masters.module_id`, `pdf_masters.language_id`, `ppt_masters.language_id`, `pre_session_assessment.module_id`, `self_paced_learning.module_id`, `topic_mapping.module_id`, `topic_master.language_id`, `topic_master.module_id`, `video_masters.language_id`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

Dedicated mobile app endpoint (not invoked by web dashboard).

---

## Mobile Profile

Total endpoints in module: **1**

### `POST` /profile/photo

- **Summary**: N/A
- **Description**: Replace the signed-in participant's profile photo.
- **Router / Handler**: [`upload_photo`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/mobile/profile/routes.py#L18) in `Backend\app\modules\mobile\profile\routes.py` (Line 18)
- **Authentication**: `Bearer Token (Participant JWT)`
- **Allowed Roles**: Trainee / Participant
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Unused by Web Frontend (no frontend service or page calls this endpoint).

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `INSERT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: Yes (Multipart)

#### Frontend Integration

No matching frontend service call found in `Frontend/src` (Backend-only / Unused by web frontend).

---

## Module Master

Total endpoints in module: **24**

### `GET` /modules

- **Summary**: Get Modules
- **Router / Handler**: [`get_modules`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/module/router.py#L42) in `Backend\app\modules\module\router.py` (Line 42)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `integer` | Yes | `None` | - |
| `search` | `any` | No | `None` | - |
| `page` | `integer` | No | `1` | - |
| `limit` | `integer` | No | `10` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `assessment_mapping`, `assessment_master`, `document_masters`, `drop_bucket_masters`, `language_master`, `match_making_masters`, `mcq_master`, `module_masters`, `module_type`, `post_session_assessment`, `pre_session_assessment`, `scq_master`, `self_paced_learning`, `topic_mapping`, `topic_master`
- **SQLAlchemy Models**: `AssessmentMapping`, `AssessmentMaster`, `DocumentMaster`, `DropBucketMaster`, `LanguageMaster`, `MatchMakingMaster`, `McqMaster`, `ModuleMaster`, `ModuleType`, `PostSessionAssessment`, `PreSessionAssessment`, `ScqMaster`, `SelfPacedLearning`, `TopicMapping`, `TopicMaster`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `document_masters.language_id`, `drop_bucket_masters.language_id`, `language_master.language_id`, `match_making_masters.language_id`, `mcq_master.language_id`, `module_masters.language_id`, `scq_master.language_id`, `topic_master.language_id`
- **Pagination Supported**: Yes
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\course\services\CourseService.js` (Line 21)
  - Snippet: `API.get("/modules", { //             params: { //                 la`
- File: `features\module\ListModule\services\ListService.js` (Line 11)
  - Snippet: `API.get("/modules", {             params,         });          retur`

---

### `GET` /modules/export

- **Summary**: Export Modules
- **Router / Handler**: [`export_modules`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/module/router.py#L59) in `Backend\app\modules\module\router.py` (Line 59)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `integer` | Yes | `None` | - |
| `search` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `assessment_mapping`, `assessment_master`, `document_masters`, `drop_bucket_masters`, `language_master`, `match_making_masters`, `mcq_master`, `module_masters`, `module_type`, `post_session_assessment`, `pre_session_assessment`, `scq_master`, `self_paced_learning`, `topic_mapping`, `topic_master`
- **SQLAlchemy Models**: `AssessmentMapping`, `AssessmentMaster`, `DocumentMaster`, `DropBucketMaster`, `LanguageMaster`, `MatchMakingMaster`, `McqMaster`, `ModuleMaster`, `ModuleType`, `PostSessionAssessment`, `PreSessionAssessment`, `ScqMaster`, `SelfPacedLearning`, `TopicMapping`, `TopicMaster`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `document_masters.language_id`, `drop_bucket_masters.language_id`, `language_master.language_id`, `match_making_masters.language_id`, `mcq_master.language_id`, `module_masters.language_id`, `scq_master.language_id`, `topic_master.language_id`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\module\ListModule\services\ListService.js` (Line 146)
  - Snippet: `API.get(             "/modules/export",             {                 params,           `

---

### `POST` /modules

- **Summary**: Create Module
- **Router / Handler**: [`create_module`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/module/router.py#L82) in `Backend\app\modules\module\router.py` (Line 82)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `multipart/form-data`
- **Schema**: `Body_create_module_modules_post`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `fk_course_id` | `integer` | Yes | `None` | - |
| `module_name` | `string` | Yes | `None` | - |
| `module_description` | `string` | Yes | `None` | - |
| `module_type` | `integer` | Yes | `None` | - |
| `module_duration` | `string` | Yes | `None` | - |
| `publishing_status` | `string` | Yes | `None` | - |
| `status` | `integer` | Yes | `None` | - |
| `module_overview` | `string` | Yes | `None` | - |
| `module_objective` | `string` | Yes | `None` | - |
| `module_icon` | `string` | Yes | `None` | - |
| `language_id` | `integer` | No | `1` | - |

**Example Request Payload:**
```json
{
  "fk_course_id": 1,
  "module_name": "sample_module_name",
  "module_description": "sample_module_description",
  "module_type": 1,
  "module_duration": "sample_module_duration",
  "publishing_status": "sample_publishing_status",
  "status": 1,
  "module_overview": "sample_module_overview",
  "module_objective": "sample_module_objective",
  "module_icon": "sample_module_icon",
  "language_id": 1
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `assessment_mapping`, `assessment_master`, `document_masters`, `drop_bucket_masters`, `language_master`, `match_making_masters`, `mcq_master`, `module_masters`, `module_type`, `post_session_assessment`, `pre_session_assessment`, `scq_master`, `self_paced_learning`, `topic_mapping`, `topic_master`
- **SQLAlchemy Models**: `AssessmentMapping`, `AssessmentMaster`, `DocumentMaster`, `DropBucketMaster`, `LanguageMaster`, `MatchMakingMaster`, `McqMaster`, `ModuleMaster`, `ModuleType`, `PostSessionAssessment`, `PreSessionAssessment`, `ScqMaster`, `SelfPacedLearning`, `TopicMapping`, `TopicMaster`
- **Operations Performed**: `INSERT`
- **Key Columns Referenced**: `document_masters.language_id`, `document_masters.status`, `drop_bucket_masters.language_id`, `drop_bucket_masters.status`, `language_master.language_id`, `match_making_masters.language_id`, `match_making_masters.status`, `mcq_master.language_id`, `mcq_master.status`, `module_masters.fk_course_id`, `module_masters.language_id`, `module_masters.module_description`, `module_masters.module_duration`, `module_masters.module_icon`, `module_masters.module_name`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: Yes (Multipart)

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\module\ListModule\services\ListService.js` (Line 58)
  - Snippet: `API.post(             "/modules",             formData,             {             `

---

### `GET` /modules/{module_id}

- **Summary**: Get Module By Id
- **Router / Handler**: [`get_module_by_id`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/module/router.py#L118) in `Backend\app\modules\module\router.py` (Line 118)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `module_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `assessment_mapping`, `assessment_master`, `document_masters`, `drop_bucket_masters`, `language_master`, `match_making_masters`, `mcq_master`, `module_masters`, `module_type`, `post_session_assessment`, `pre_session_assessment`, `scq_master`, `self_paced_learning`, `topic_mapping`, `topic_master`
- **SQLAlchemy Models**: `AssessmentMapping`, `AssessmentMaster`, `DocumentMaster`, `DropBucketMaster`, `LanguageMaster`, `MatchMakingMaster`, `McqMaster`, `ModuleMaster`, `ModuleType`, `PostSessionAssessment`, `PreSessionAssessment`, `ScqMaster`, `SelfPacedLearning`, `TopicMapping`, `TopicMaster`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `assessment_master.module_id`, `document_masters.module_id`, `module_masters.module_id`, `post_session_assessment.module_id`, `pre_session_assessment.module_id`, `self_paced_learning.module_id`, `topic_mapping.module_id`, `topic_master.module_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\module\ListModule\services\ListService.js` (Line 35)
  - Snippet: `API.get(`/modules/${moduleId}`);          return response.data;     } catch (err`

---

### `PUT` /modules/{module_id}

- **Summary**: Update Module
- **Router / Handler**: [`update_module`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/module/router.py#L134) in `Backend\app\modules\module\router.py` (Line 134)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `module_id` | `integer` | Yes | - |

#### Request Body

- **Content-Type**: `multipart/form-data`
- **Schema**: `Body_update_module_modules__module_id__put`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `fk_course_id` | `integer` | Yes | `None` | - |
| `module_name` | `string` | Yes | `None` | - |
| `module_description` | `string` | Yes | `None` | - |
| `module_type` | `integer` | Yes | `None` | - |
| `module_duration` | `string` | Yes | `None` | - |
| `publishing_status` | `string` | Yes | `None` | - |
| `status` | `integer` | Yes | `None` | - |
| `module_overview` | `string` | Yes | `None` | - |
| `module_objective` | `string` | Yes | `None` | - |
| `module_icon` | `any` | No | `None` | - |

**Example Request Payload:**
```json
{
  "fk_course_id": 1,
  "module_name": "sample_module_name",
  "module_description": "sample_module_description",
  "module_type": 1,
  "module_duration": "sample_module_duration",
  "publishing_status": "sample_publishing_status",
  "status": 1,
  "module_overview": "sample_module_overview",
  "module_objective": "sample_module_objective",
  "module_icon": "sample_module_icon"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `assessment_mapping`, `assessment_master`, `document_masters`, `drop_bucket_masters`, `language_master`, `match_making_masters`, `mcq_master`, `module_masters`, `module_type`, `post_session_assessment`, `pre_session_assessment`, `scq_master`, `self_paced_learning`, `topic_mapping`, `topic_master`
- **SQLAlchemy Models**: `AssessmentMapping`, `AssessmentMaster`, `DocumentMaster`, `DropBucketMaster`, `LanguageMaster`, `MatchMakingMaster`, `McqMaster`, `ModuleMaster`, `ModuleType`, `PostSessionAssessment`, `PreSessionAssessment`, `ScqMaster`, `SelfPacedLearning`, `TopicMapping`, `TopicMaster`
- **Operations Performed**: `UPDATE`
- **Key Columns Referenced**: `assessment_master.module_id`, `document_masters.module_id`, `document_masters.status`, `drop_bucket_masters.status`, `match_making_masters.status`, `mcq_master.status`, `module_masters.fk_course_id`, `module_masters.module_description`, `module_masters.module_duration`, `module_masters.module_icon`, `module_masters.module_id`, `module_masters.module_name`, `module_masters.module_objective`, `module_masters.module_overview`, `module_masters.module_type`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: Yes (Multipart)

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\module\ListModule\services\ListService.js` (Line 90)
  - Snippet: `API.put(             `/modules/${moduleId}`,             formData,             {             `

---

### `DELETE` /modules/{module_id}

- **Summary**: Delete Module
- **Router / Handler**: [`delete_module`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/module/router.py#L169) in `Backend\app\modules\module\router.py` (Line 169)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `module_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `assessment_mapping`, `assessment_master`, `document_masters`, `drop_bucket_masters`, `language_master`, `match_making_masters`, `mcq_master`, `module_masters`, `module_type`, `post_session_assessment`, `pre_session_assessment`, `scq_master`, `self_paced_learning`, `topic_mapping`, `topic_master`
- **SQLAlchemy Models**: `AssessmentMapping`, `AssessmentMaster`, `DocumentMaster`, `DropBucketMaster`, `LanguageMaster`, `MatchMakingMaster`, `McqMaster`, `ModuleMaster`, `ModuleType`, `PostSessionAssessment`, `PreSessionAssessment`, `ScqMaster`, `SelfPacedLearning`, `TopicMapping`, `TopicMaster`
- **Operations Performed**: `DELETE`
- **Key Columns Referenced**: `assessment_master.module_id`, `document_masters.module_id`, `module_masters.module_id`, `post_session_assessment.module_id`, `pre_session_assessment.module_id`, `self_paced_learning.module_id`, `topic_mapping.module_id`, `topic_master.module_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\module\ListModule\services\ListService.js` (Line 120)
  - Snippet: `API.delete(             `/modules/${moduleId}`         );          return response.data;     } c`

---

### `POST` /modules/{module_id}/translation

- **Summary**: Save Translation
- **Router / Handler**: [`save_translation`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/module/router.py#L183) in `Backend\app\modules\module\router.py` (Line 183)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `module_id` | `integer` | Yes | - |

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `ModuleTranslation`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `integer` | Yes | `None` | - |
| `module_name` | `string` | Yes | `None` | - |
| `module_description` | `any` | No | `None` | - |
| `module_overview` | `any` | No | `None` | - |
| `module_objective` | `any` | No | `None` | - |

**Example Request Payload:**
```json
{
  "language_id": 1,
  "module_name": "sample_module_name",
  "module_description": "sample_module_description",
  "module_overview": "sample_module_overview",
  "module_objective": "sample_module_objective"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `assessment_mapping`, `assessment_master`, `document_masters`, `drop_bucket_masters`, `language_master`, `match_making_masters`, `mcq_master`, `module_masters`, `module_type`, `post_session_assessment`, `pre_session_assessment`, `scq_master`, `self_paced_learning`, `topic_mapping`, `topic_master`
- **SQLAlchemy Models**: `AssessmentMapping`, `AssessmentMaster`, `DocumentMaster`, `DropBucketMaster`, `LanguageMaster`, `MatchMakingMaster`, `McqMaster`, `ModuleMaster`, `ModuleType`, `PostSessionAssessment`, `PreSessionAssessment`, `ScqMaster`, `SelfPacedLearning`, `TopicMapping`, `TopicMaster`
- **Operations Performed**: `INSERT`
- **Key Columns Referenced**: `assessment_master.module_id`, `document_masters.module_id`, `module_masters.module_id`, `post_session_assessment.module_id`, `pre_session_assessment.module_id`, `self_paced_learning.module_id`, `topic_mapping.module_id`, `topic_master.module_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\module\ListModule\services\ListService.js` (Line 179)
  - Snippet: `API.post(             `/modules/${moduleId}/translation`,             data         );          retur`

---

### `GET` /modules/{module_id}/translation

- **Summary**: Get Translation
- **Router / Handler**: [`get_translation`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/module/router.py#L196) in `Backend\app\modules\module\router.py` (Line 196)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `module_id` | `integer` | Yes | - |

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `integer` | Yes | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `assessment_mapping`, `assessment_master`, `document_masters`, `drop_bucket_masters`, `language_master`, `match_making_masters`, `mcq_master`, `module_masters`, `module_type`, `post_session_assessment`, `pre_session_assessment`, `scq_master`, `self_paced_learning`, `topic_mapping`, `topic_master`
- **SQLAlchemy Models**: `AssessmentMapping`, `AssessmentMaster`, `DocumentMaster`, `DropBucketMaster`, `LanguageMaster`, `MatchMakingMaster`, `McqMaster`, `ModuleMaster`, `ModuleType`, `PostSessionAssessment`, `PreSessionAssessment`, `ScqMaster`, `SelfPacedLearning`, `TopicMapping`, `TopicMaster`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `assessment_master.module_id`, `document_masters.language_id`, `document_masters.module_id`, `drop_bucket_masters.language_id`, `language_master.language_id`, `match_making_masters.language_id`, `mcq_master.language_id`, `module_masters.language_id`, `module_masters.module_id`, `post_session_assessment.module_id`, `pre_session_assessment.module_id`, `scq_master.language_id`, `self_paced_learning.module_id`, `topic_mapping.module_id`, `topic_master.language_id`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\module\ListModule\services\ListService.js` (Line 207)
  - Snippet: `API.get(             `/modules/${moduleId}/translation`,             {                 params: {    `

---

### `GET` /modules/modules/{module_id}/post-assessments

- **Summary**: Get Post Assessments
- **Router / Handler**: [`get_post_assessments`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/module/router.py#L209) in `Backend\app\modules\module\router.py` (Line 209)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Quirk / Duplicate Prefix Bug**
- **Detected Issues / Notes**:
  - Route path has duplicated prefix (/modules/modules/{module_id}/post-assessments). Frontend accommodates this with matching double prefix.

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `module_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `ModulePostAssessmentResponse`

**Example Success Response:**
```json
{
  "module_id": 1,
  "assessments": []
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `assessment_mapping`, `assessment_master`, `document_masters`, `drop_bucket_masters`, `language_master`, `match_making_masters`, `mcq_master`, `module_masters`, `module_type`, `post_session_assessment`, `pre_session_assessment`, `scq_master`, `self_paced_learning`, `topic_mapping`, `topic_master`
- **SQLAlchemy Models**: `AssessmentMapping`, `AssessmentMaster`, `DocumentMaster`, `DropBucketMaster`, `LanguageMaster`, `MatchMakingMaster`, `McqMaster`, `ModuleMaster`, `ModuleType`, `PostSessionAssessment`, `PreSessionAssessment`, `ScqMaster`, `SelfPacedLearning`, `TopicMapping`, `TopicMaster`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `assessment_master.module_id`, `document_masters.module_id`, `module_masters.module_id`, `post_session_assessment.module_id`, `pre_session_assessment.module_id`, `self_paced_learning.module_id`, `topic_mapping.module_id`, `topic_master.module_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\module\ListModule\services\ConfigurationService.js` (Line 194)
  - Snippet: `API.get(             `/modules/modules/${moduleId}/post-assessments`         );          return resp`

---

### `GET` /modules/modules/{module_id}/pre-assessments

- **Summary**: Get Pre Assessments
- **Router / Handler**: [`get_pre_assessments`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/module/router.py#L216) in `Backend\app\modules\module\router.py` (Line 216)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Quirk / Duplicate Prefix Bug**
- **Detected Issues / Notes**:
  - Route path has duplicated prefix (/modules/modules/{module_id}/pre-assessments). Frontend accommodates this with matching double prefix.

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `module_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `ModulePostAssessmentResponse`

**Example Success Response:**
```json
{
  "module_id": 1,
  "assessments": []
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `assessment_mapping`, `assessment_master`, `document_masters`, `drop_bucket_masters`, `language_master`, `match_making_masters`, `mcq_master`, `module_masters`, `module_type`, `post_session_assessment`, `pre_session_assessment`, `scq_master`, `self_paced_learning`, `topic_mapping`, `topic_master`
- **SQLAlchemy Models**: `AssessmentMapping`, `AssessmentMaster`, `DocumentMaster`, `DropBucketMaster`, `LanguageMaster`, `MatchMakingMaster`, `McqMaster`, `ModuleMaster`, `ModuleType`, `PostSessionAssessment`, `PreSessionAssessment`, `ScqMaster`, `SelfPacedLearning`, `TopicMapping`, `TopicMaster`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `assessment_master.module_id`, `document_masters.module_id`, `module_masters.module_id`, `post_session_assessment.module_id`, `pre_session_assessment.module_id`, `self_paced_learning.module_id`, `topic_mapping.module_id`, `topic_master.module_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\module\ListModule\services\ConfigurationService.js` (Line 216)
  - Snippet: `API.get(             `/modules/modules/${moduleId}/pre-assessments`         );          return respo`

---

### `GET` /modules/assessments/{assessment_id}/scqs

- **Summary**: Get Scq Assessment Mapping
- **Router / Handler**: [`get_scq_assessment_mapping`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/module/router.py#L223) in `Backend\app\modules\module\router.py` (Line 223)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Unused by Web Frontend (no frontend service or page calls this endpoint).

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `assessment_id` | `integer` | Yes | - |

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `assessment_mapping`, `assessment_master`, `document_masters`, `drop_bucket_masters`, `language_master`, `match_making_masters`, `mcq_master`, `module_masters`, `module_type`, `post_session_assessment`, `pre_session_assessment`, `scq_master`, `self_paced_learning`, `topic_mapping`, `topic_master`
- **SQLAlchemy Models**: `AssessmentMapping`, `AssessmentMaster`, `DocumentMaster`, `DropBucketMaster`, `LanguageMaster`, `MatchMakingMaster`, `McqMaster`, `ModuleMaster`, `ModuleType`, `PostSessionAssessment`, `PreSessionAssessment`, `ScqMaster`, `SelfPacedLearning`, `TopicMapping`, `TopicMaster`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `assessment_mapping.assessment_id`, `assessment_master.assessment_id`, `document_masters.language_id`, `drop_bucket_masters.language_id`, `language_master.language_id`, `match_making_masters.language_id`, `mcq_master.language_id`, `module_masters.language_id`, `post_session_assessment.assessment_id`, `pre_session_assessment.assessment_id`, `scq_master.language_id`, `topic_master.language_id`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

No matching frontend service call found in `Frontend/src` (Backend-only / Unused by web frontend).

---

### `GET` /modules/assessments/{assessment_id}/mcqs

- **Summary**: Get Mcq Assessment Mapping
- **Router / Handler**: [`get_mcq_assessment_mapping`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/module/router.py#L234) in `Backend\app\modules\module\router.py` (Line 234)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Unused by Web Frontend (no frontend service or page calls this endpoint).

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `assessment_id` | `integer` | Yes | - |

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `assessment_mapping`, `assessment_master`, `document_masters`, `drop_bucket_masters`, `language_master`, `match_making_masters`, `mcq_master`, `module_masters`, `module_type`, `post_session_assessment`, `pre_session_assessment`, `scq_master`, `self_paced_learning`, `topic_mapping`, `topic_master`
- **SQLAlchemy Models**: `AssessmentMapping`, `AssessmentMaster`, `DocumentMaster`, `DropBucketMaster`, `LanguageMaster`, `MatchMakingMaster`, `McqMaster`, `ModuleMaster`, `ModuleType`, `PostSessionAssessment`, `PreSessionAssessment`, `ScqMaster`, `SelfPacedLearning`, `TopicMapping`, `TopicMaster`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `assessment_mapping.assessment_id`, `assessment_master.assessment_id`, `document_masters.language_id`, `drop_bucket_masters.language_id`, `language_master.language_id`, `match_making_masters.language_id`, `mcq_master.language_id`, `module_masters.language_id`, `post_session_assessment.assessment_id`, `pre_session_assessment.assessment_id`, `scq_master.language_id`, `topic_master.language_id`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

No matching frontend service call found in `Frontend/src` (Backend-only / Unused by web frontend).

---

### `GET` /modules/assessments/{assessment_id}/match-makings

- **Summary**: Get Match Making Assessment Mapping
- **Router / Handler**: [`get_match_making_assessment_mapping`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/module/router.py#L245) in `Backend\app\modules\module\router.py` (Line 245)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Unused by Web Frontend (no frontend service or page calls this endpoint).

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `assessment_id` | `integer` | Yes | - |

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[MatchMakingAssessmentMappingResponse]`

**Example Success Response:**
```json
[
  {
    "match_making_id": 1,
    "match_making_question_title": "sample_match_making_question_title",
    "match_making_question_description": "sample_match_making_question_description",
    "image_url": "sample_image_url",
    "status": 1,
    "marks": "sample_marks",
    "language_id": 1,
    "language_name": "sample_language_name",
    "is_checked": true
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `assessment_mapping`, `assessment_master`, `document_masters`, `drop_bucket_masters`, `language_master`, `match_making_masters`, `mcq_master`, `module_masters`, `module_type`, `post_session_assessment`, `pre_session_assessment`, `scq_master`, `self_paced_learning`, `topic_mapping`, `topic_master`
- **SQLAlchemy Models**: `AssessmentMapping`, `AssessmentMaster`, `DocumentMaster`, `DropBucketMaster`, `LanguageMaster`, `MatchMakingMaster`, `McqMaster`, `ModuleMaster`, `ModuleType`, `PostSessionAssessment`, `PreSessionAssessment`, `ScqMaster`, `SelfPacedLearning`, `TopicMapping`, `TopicMaster`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `assessment_mapping.assessment_id`, `assessment_master.assessment_id`, `document_masters.language_id`, `drop_bucket_masters.language_id`, `language_master.language_id`, `match_making_masters.language_id`, `mcq_master.language_id`, `module_masters.language_id`, `post_session_assessment.assessment_id`, `pre_session_assessment.assessment_id`, `scq_master.language_id`, `topic_master.language_id`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

No matching frontend service call found in `Frontend/src` (Backend-only / Unused by web frontend).

---

### `GET` /modules/assessments/{assessment_id}/drop-buckets

- **Summary**: Get Drop Bucket Assessment Mapping
- **Router / Handler**: [`get_drop_bucket_assessment_mapping`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/module/router.py#L259) in `Backend\app\modules\module\router.py` (Line 259)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Unused by Web Frontend (no frontend service or page calls this endpoint).

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `assessment_id` | `integer` | Yes | - |

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[DropBucketAssessmentMappingResponse]`

**Example Success Response:**
```json
[
  {
    "drop_bucket_id": 1,
    "drop_bucket_question_title": "sample_drop_bucket_question_title",
    "drop_bucket_question_description": "sample_drop_bucket_question_description",
    "image_url": "sample_image_url",
    "status": 1,
    "marks": "sample_marks",
    "language_id": 1,
    "language_name": "sample_language_name",
    "is_checked": true
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `assessment_mapping`, `assessment_master`, `document_masters`, `drop_bucket_masters`, `language_master`, `match_making_masters`, `mcq_master`, `module_masters`, `module_type`, `post_session_assessment`, `pre_session_assessment`, `scq_master`, `self_paced_learning`, `topic_mapping`, `topic_master`
- **SQLAlchemy Models**: `AssessmentMapping`, `AssessmentMaster`, `DocumentMaster`, `DropBucketMaster`, `LanguageMaster`, `MatchMakingMaster`, `McqMaster`, `ModuleMaster`, `ModuleType`, `PostSessionAssessment`, `PreSessionAssessment`, `ScqMaster`, `SelfPacedLearning`, `TopicMapping`, `TopicMaster`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `assessment_mapping.assessment_id`, `assessment_master.assessment_id`, `document_masters.language_id`, `drop_bucket_masters.language_id`, `language_master.language_id`, `match_making_masters.language_id`, `mcq_master.language_id`, `module_masters.language_id`, `post_session_assessment.assessment_id`, `pre_session_assessment.assessment_id`, `scq_master.language_id`, `topic_master.language_id`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

No matching frontend service call found in `Frontend/src` (Backend-only / Unused by web frontend).

---

### `POST` /modules/assessment-mapping

- **Summary**: Save Assessment Mapping
- **Router / Handler**: [`save_assessment_mapping`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/module/router.py#L273) in `Backend\app\modules\module\router.py` (Line 273)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `AssessmentMappingCreateRequest`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `assessment_type` | `string` | Yes | `None` | - |
| `assessments` | `array` | Yes | `None` | - |

**Example Request Payload:**
```json
{
  "assessment_type": "sample_assessment_type",
  "assessments": []
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `assessment_mapping`, `assessment_master`, `document_masters`, `drop_bucket_masters`, `language_master`, `match_making_masters`, `mcq_master`, `module_masters`, `module_type`, `post_session_assessment`, `pre_session_assessment`, `scq_master`, `self_paced_learning`, `topic_mapping`, `topic_master`
- **SQLAlchemy Models**: `AssessmentMapping`, `AssessmentMaster`, `DocumentMaster`, `DropBucketMaster`, `LanguageMaster`, `MatchMakingMaster`, `McqMaster`, `ModuleMaster`, `ModuleType`, `PostSessionAssessment`, `PreSessionAssessment`, `ScqMaster`, `SelfPacedLearning`, `TopicMapping`, `TopicMaster`
- **Operations Performed**: `INSERT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\module\ListModule\services\ConfigurationService.js` (Line 279)
  - Snippet: `API.post(             "/modules/assessment-mapping",             payload         );          return `

---

### `GET` /modules/main-content/topics/{module_id}

- **Summary**: Get Topics For Main Content
- **Router / Handler**: [`get_topics_for_main_content`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/module/router.py#L280) in `Backend\app\modules\module\router.py` (Line 280)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `module_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[TopicDropdownResponse]`

**Example Success Response:**
```json
[
  {
    "topic_id": 1,
    "topic_name": "sample_topic_name",
    "module_id": "sample_module_id",
    "language_name": "sample_language_name"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `assessment_mapping`, `assessment_master`, `document_masters`, `drop_bucket_masters`, `language_master`, `match_making_masters`, `mcq_master`, `module_masters`, `module_type`, `post_session_assessment`, `pre_session_assessment`, `scq_master`, `self_paced_learning`, `topic_mapping`, `topic_master`
- **SQLAlchemy Models**: `AssessmentMapping`, `AssessmentMaster`, `DocumentMaster`, `DropBucketMaster`, `LanguageMaster`, `MatchMakingMaster`, `McqMaster`, `ModuleMaster`, `ModuleType`, `PostSessionAssessment`, `PreSessionAssessment`, `ScqMaster`, `SelfPacedLearning`, `TopicMapping`, `TopicMaster`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `assessment_master.module_id`, `document_masters.module_id`, `module_masters.module_id`, `post_session_assessment.module_id`, `pre_session_assessment.module_id`, `self_paced_learning.module_id`, `topic_mapping.module_id`, `topic_master.module_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\module\ListModule\hook\ConfigureModule.js` (Line 360)
  - Snippet: `API.get(                     `/modules/main-content/topics/${moduleId}`                 ),          `
- File: `features\module\ListModule\services\ConfigurationService.js` (Line 28)
  - Snippet: `API.get(             `/modules/main-content/topics/${moduleId}`,             {                 param`

---

### `GET` /modules/main-content/documents

- **Summary**: Get Documents For Main Content
- **Router / Handler**: [`get_documents_for_main_content`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/module/router.py#L287) in `Backend\app\modules\module\router.py` (Line 287)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[DocumentDropdownResponse]`

**Example Success Response:**
```json
[
  {
    "doc_id": 1,
    "doc_title": "sample_doc_title",
    "doc_description": "sample_doc_description",
    "doc_type": "sample_doc_type",
    "language_name": "sample_language_name"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `assessment_mapping`, `assessment_master`, `document_masters`, `drop_bucket_masters`, `language_master`, `match_making_masters`, `mcq_master`, `module_masters`, `module_type`, `post_session_assessment`, `pre_session_assessment`, `scq_master`, `self_paced_learning`, `topic_mapping`, `topic_master`
- **SQLAlchemy Models**: `AssessmentMapping`, `AssessmentMaster`, `DocumentMaster`, `DropBucketMaster`, `LanguageMaster`, `MatchMakingMaster`, `McqMaster`, `ModuleMaster`, `ModuleType`, `PostSessionAssessment`, `PreSessionAssessment`, `ScqMaster`, `SelfPacedLearning`, `TopicMapping`, `TopicMaster`
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\module\ListModule\hook\ConfigureModule.js` (Line 364)
  - Snippet: `API.get(                     `/modules/main-content/documents`                 ),             ]);   `
- File: `features\module\ListModule\services\ConfigurationService.js` (Line 54)
  - Snippet: `API.get(             "/modules/main-content/documents"         );          return response.data;    `

---

### `POST` /modules/main-content

- **Summary**: Create Main Content
- **Router / Handler**: [`create_main_content`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/module/router.py#L292) in `Backend\app\modules\module\router.py` (Line 292)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `MainContentCreateRequest`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `module_id` | `integer` | Yes | `None` | - |
| `topic_id` | `integer` | Yes | `None` | - |
| `doc_id` | `integer` | Yes | `None` | - |

**Example Request Payload:**
```json
{
  "module_id": 1,
  "topic_id": 1,
  "doc_id": 1
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `MainContentResponse`

**Example Success Response:**
```json
{
  "success": true,
  "message": "sample_message"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `assessment_mapping`, `assessment_master`, `document_masters`, `drop_bucket_masters`, `language_master`, `match_making_masters`, `mcq_master`, `module_masters`, `module_type`, `post_session_assessment`, `pre_session_assessment`, `scq_master`, `self_paced_learning`, `topic_mapping`, `topic_master`
- **SQLAlchemy Models**: `AssessmentMapping`, `AssessmentMaster`, `DocumentMaster`, `DropBucketMaster`, `LanguageMaster`, `MatchMakingMaster`, `McqMaster`, `ModuleMaster`, `ModuleType`, `PostSessionAssessment`, `PreSessionAssessment`, `ScqMaster`, `SelfPacedLearning`, `TopicMapping`, `TopicMaster`
- **Operations Performed**: `INSERT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\module\ListModule\hook\ConfigureModule.js` (Line 432)
  - Snippet: `API.post(                 "/modules/main-content",                 {                     module_id:`
- File: `features\module\ListModule\services\ConfigurationService.js` (Line 76)
  - Snippet: `API.post(             "/modules/main-content",             payload         );          return r`

---

### `GET` /modules/main-content/{module_id}

- **Summary**: Get Main Content List
- **Router / Handler**: [`get_main_content_list`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/module/router.py#L299) in `Backend\app\modules\module\router.py` (Line 299)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `module_id` | `integer` | Yes | - |

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[MainContentListResponse]`

**Example Success Response:**
```json
[
  {
    "self_paced_learning_id": 1,
    "module_id": 1,
    "topic_id": 1,
    "doc_id": 1,
    "topic_name": "sample_topic_name",
    "doc_title": "sample_doc_title",
    "doc_type": "sample_doc_type",
    "doc_ref_id": "sample_doc_ref_id",
    "language_id": "sample_language_id",
    "language_name": "sample_language_name",
    "is_active": "sample_is_active"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `assessment_mapping`, `assessment_master`, `document_masters`, `drop_bucket_masters`, `language_master`, `match_making_masters`, `mcq_master`, `module_masters`, `module_type`, `post_session_assessment`, `pre_session_assessment`, `scq_master`, `self_paced_learning`, `topic_mapping`, `topic_master`
- **SQLAlchemy Models**: `AssessmentMapping`, `AssessmentMaster`, `DocumentMaster`, `DropBucketMaster`, `LanguageMaster`, `MatchMakingMaster`, `McqMaster`, `ModuleMaster`, `ModuleType`, `PostSessionAssessment`, `PreSessionAssessment`, `ScqMaster`, `SelfPacedLearning`, `TopicMapping`, `TopicMaster`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `assessment_master.module_id`, `document_masters.language_id`, `document_masters.module_id`, `drop_bucket_masters.language_id`, `language_master.language_id`, `match_making_masters.language_id`, `mcq_master.language_id`, `module_masters.language_id`, `module_masters.module_id`, `post_session_assessment.module_id`, `pre_session_assessment.module_id`, `scq_master.language_id`, `self_paced_learning.module_id`, `topic_mapping.module_id`, `topic_master.language_id`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\module\ListModule\hook\ConfigureModule.js` (Line 356)
  - Snippet: `API.get(                     `/modules/main-content/${moduleId}`                 ),                 `
- File: `features\module\ListModule\services\ConfigurationService.js` (Line 6)
  - Snippet: `API.get(             `/modules/main-content/${moduleId}`,             {                 params: lang`

---

### `POST` /modules/self-paced

- **Summary**: Create Self Paced Content
- **Router / Handler**: [`create_self_paced_content`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/module/router.py#L315) in `Backend\app\modules\module\router.py` (Line 315)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `MainContentCreateRequest`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `module_id` | `integer` | Yes | `None` | - |
| `topic_id` | `integer` | Yes | `None` | - |
| `doc_id` | `integer` | Yes | `None` | - |

**Example Request Payload:**
```json
{
  "module_id": 1,
  "topic_id": 1,
  "doc_id": 1
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `MainContentResponse`

**Example Success Response:**
```json
{
  "success": true,
  "message": "sample_message"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `INSERT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\module\ListModule\services\ConfigurationService.js` (Line 165)
  - Snippet: `API.post(             "/modules/self-paced",             payload         );          return r`

---

### `GET` /modules/self-paced/{module_id}

- **Summary**: Get Self Paced List
- **Router / Handler**: [`get_self_paced_list`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/module/router.py#L330) in `Backend\app\modules\module\router.py` (Line 330)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `module_id` | `integer` | Yes | - |

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[MainContentListResponse]`

**Example Success Response:**
```json
[
  {
    "self_paced_learning_id": 1,
    "module_id": 1,
    "topic_id": 1,
    "doc_id": 1,
    "topic_name": "sample_topic_name",
    "doc_title": "sample_doc_title",
    "doc_type": "sample_doc_type",
    "doc_ref_id": "sample_doc_ref_id",
    "language_id": "sample_language_id",
    "language_name": "sample_language_name",
    "is_active": "sample_is_active"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\module\ListModule\services\ConfigurationService.js` (Line 143)
  - Snippet: `API.get(             `/modules/self-paced/${moduleId}`,             {                 params: langua`

---

### `PATCH` /modules/main-content/{self_paced_learning_id}/deactivate

- **Summary**: Deactivate Main Content
- **Router / Handler**: [`deactivate_main_content`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/module/router.py#L351) in `Backend\app\modules\module\router.py` (Line 351)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `self_paced_learning_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `assessment_mapping`, `assessment_master`, `document_masters`, `drop_bucket_masters`, `language_master`, `match_making_masters`, `mcq_master`, `module_masters`, `module_type`, `post_session_assessment`, `pre_session_assessment`, `scq_master`, `self_paced_learning`, `topic_mapping`, `topic_master`
- **SQLAlchemy Models**: `AssessmentMapping`, `AssessmentMaster`, `DocumentMaster`, `DropBucketMaster`, `LanguageMaster`, `MatchMakingMaster`, `McqMaster`, `ModuleMaster`, `ModuleType`, `PostSessionAssessment`, `PreSessionAssessment`, `ScqMaster`, `SelfPacedLearning`, `TopicMapping`, `TopicMaster`
- **Operations Performed**: `UPDATE`
- **Key Columns Referenced**: `document_masters.self_paced_learning`, `module_masters.self_paced_learning`, `self_paced_learning.self_paced_learning_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\module\ListModule\services\ConfigurationService.js` (Line 98)
  - Snippet: `API.patch(             `/modules/main-content/${selfPacedLearningId}/deactivate`         );         `

---

### `PATCH` /modules/main-content/{self_paced_learning_id}/activate

- **Summary**: Activate Main Content
- **Router / Handler**: [`activate_main_content`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/module/router.py#L366) in `Backend\app\modules\module\router.py` (Line 366)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `self_paced_learning_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `assessment_mapping`, `assessment_master`, `document_masters`, `drop_bucket_masters`, `language_master`, `match_making_masters`, `mcq_master`, `module_masters`, `module_type`, `post_session_assessment`, `pre_session_assessment`, `scq_master`, `self_paced_learning`, `topic_mapping`, `topic_master`
- **SQLAlchemy Models**: `AssessmentMapping`, `AssessmentMaster`, `DocumentMaster`, `DropBucketMaster`, `LanguageMaster`, `MatchMakingMaster`, `McqMaster`, `ModuleMaster`, `ModuleType`, `PostSessionAssessment`, `PreSessionAssessment`, `ScqMaster`, `SelfPacedLearning`, `TopicMapping`, `TopicMaster`
- **Operations Performed**: `UPDATE`
- **Key Columns Referenced**: `document_masters.self_paced_learning`, `module_masters.self_paced_learning`, `self_paced_learning.self_paced_learning_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\module\ListModule\services\ConfigurationService.js` (Line 119)
  - Snippet: `API.patch(             `/modules/main-content/${selfPacedLearningId}/activate`         );          r`

---

### `PATCH` /modules/assessment-mapping/deactivate

- **Summary**: Deactivate Assessment Mapping
- **Router / Handler**: [`deactivate_assessment_mapping`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/module/router.py#L381) in `Backend\app\modules\module\router.py` (Line 381)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `AssessmentMappingDeactivateRequest`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `assessment_id` | `integer` | Yes | `None` | - |
| `assessment_type` | `string` | Yes | `None` | - |
| `assessment_ref_id` | `integer` | Yes | `None` | - |

**Example Request Payload:**
```json
{
  "assessment_id": 1,
  "assessment_type": "sample_assessment_type",
  "assessment_ref_id": 1
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `assessment_mapping`, `assessment_master`, `document_masters`, `drop_bucket_masters`, `language_master`, `match_making_masters`, `mcq_master`, `module_masters`, `module_type`, `post_session_assessment`, `pre_session_assessment`, `scq_master`, `self_paced_learning`, `topic_mapping`, `topic_master`
- **SQLAlchemy Models**: `AssessmentMapping`, `AssessmentMaster`, `DocumentMaster`, `DropBucketMaster`, `LanguageMaster`, `MatchMakingMaster`, `McqMaster`, `ModuleMaster`, `ModuleType`, `PostSessionAssessment`, `PreSessionAssessment`, `ScqMaster`, `SelfPacedLearning`, `TopicMapping`, `TopicMaster`
- **Operations Performed**: `UPDATE`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\module\ListModule\services\ConfigurationService.js` (Line 302)
  - Snippet: `API.patch(             "/modules/assessment-mapping/deactivate",             payload         );     `

---

## PDF Master

Total endpoints in module: **7**

### `GET` /pdf-masters

- **Summary**: List Pdfs
- **Router / Handler**: [`list_pdfs`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/pdf/router.py#L21) in `Backend\app\modules\pdf\router.py` (Line 21)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: DOCUMENT_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `search` | `any` | No | `None` | - |
| `page` | `integer` | No | `1` | - |
| `limit` | `integer` | No | `10` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `language_master`, `pdf_masters`
- **SQLAlchemy Models**: `LanguageMaster`, `PdfMaster`
- **Operations Performed**: `SELECT`
- **Pagination Supported**: Yes
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\document\pdf\services\PdfService.js` (Line 13)
  - Snippet: `API.get("/pdf-masters", { params });         return response.data;     }`

---

### `GET` /pdf-masters/export/csv

- **Summary**: Export Pdfs
- **Router / Handler**: [`export_pdfs`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/pdf/router.py#L40) in `Backend\app\modules\pdf\router.py` (Line 40)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: DOCUMENT_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `search` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\document\pdf\services\PdfService.js` (Line 93)
  - Snippet: `API.get("/pdf-masters/export/csv", {             params,             responseType: `

---

### `GET` /pdf-masters/{pdf_id}/archived-versions

- **Summary**: Get Archived Versions
- **Router / Handler**: [`get_archived_versions`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/pdf/router.py#L51) in `Backend\app\modules\pdf\router.py` (Line 51)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: DOCUMENT_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `pdf_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `language_master`, `pdf_masters`
- **SQLAlchemy Models**: `LanguageMaster`, `PdfMaster`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `pdf_masters.pdf_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\document\pdf\services\PdfService.js` (Line 73)
  - Snippet: `API.get(             `/pdf-masters/${pdfId}/archived-versions`         );         return response.da`

---

### `GET` /pdf-masters/{pdf_id}

- **Summary**: Get Pdf
- **Router / Handler**: [`get_pdf`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/pdf/router.py#L62) in `Backend\app\modules\pdf\router.py` (Line 62)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: DOCUMENT_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `pdf_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `language_master`, `pdf_masters`
- **SQLAlchemy Models**: `LanguageMaster`, `PdfMaster`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `pdf_masters.pdf_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\document\pdf\services\PdfService.js` (Line 37)
  - Snippet: `API.get(`/pdf-masters/${pdfId}`);         return response.data;     } catch (erro`

---

### `POST` /pdf-masters

- **Summary**: Create Pdf
- **Router / Handler**: [`create_pdf`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/pdf/router.py#L73) in `Backend\app\modules\pdf\router.py` (Line 73)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: DOCUMENT_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `multipart/form-data`
- **Schema**: `Body_create_pdf_pdf_masters_post`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `pdf_name` | `string` | Yes | `None` | - |
| `pdf_description` | `any` | No | `None` | - |
| `cloud_url` | `any` | No | `None` | - |
| `language_id` | `any` | No | `None` | - |
| `status` | `any` | No | `1` | - |
| `media_file` | `any` | No | `None` | - |

**Example Request Payload:**
```json
{
  "pdf_name": "sample_pdf_name",
  "pdf_description": "sample_pdf_description",
  "cloud_url": "sample_cloud_url",
  "language_id": "sample_language_id",
  "status": "sample_status",
  "media_file": "sample_media_file"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `language_master`, `pdf_masters`
- **SQLAlchemy Models**: `LanguageMaster`, `PdfMaster`
- **Operations Performed**: `INSERT`
- **Key Columns Referenced**: `language_master.language_id`, `pdf_masters.cloud_url`, `pdf_masters.language_id`, `pdf_masters.pdf_description`, `pdf_masters.pdf_name`, `pdf_masters.status`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: Yes (Multipart)

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\document\pdf\services\PdfService.js` (Line 24)
  - Snippet: `API.post("/pdf-masters", formData, {             headers: { "Content-Type`

---

### `PUT` /pdf-masters/{pdf_id}

- **Summary**: Update Pdf
- **Router / Handler**: [`update_pdf`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/pdf/router.py#L100) in `Backend\app\modules\pdf\router.py` (Line 100)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: DOCUMENT_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `pdf_id` | `integer` | Yes | - |

#### Request Body

- **Content-Type**: `multipart/form-data`
- **Schema**: `Body_update_pdf_pdf_masters__pdf_id__put`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `pdf_name` | `any` | No | `None` | - |
| `pdf_description` | `any` | No | `None` | - |
| `cloud_url` | `any` | No | `None` | - |
| `language_id` | `any` | No | `None` | - |
| `status` | `any` | No | `None` | - |
| `media_file` | `any` | No | `None` | - |

**Example Request Payload:**
```json
{
  "pdf_name": "sample_pdf_name",
  "pdf_description": "sample_pdf_description",
  "cloud_url": "sample_cloud_url",
  "language_id": "sample_language_id",
  "status": "sample_status",
  "media_file": "sample_media_file"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `language_master`, `pdf_masters`
- **SQLAlchemy Models**: `LanguageMaster`, `PdfMaster`
- **Operations Performed**: `UPDATE`
- **Key Columns Referenced**: `language_master.language_id`, `pdf_masters.cloud_url`, `pdf_masters.language_id`, `pdf_masters.pdf_description`, `pdf_masters.pdf_id`, `pdf_masters.pdf_name`, `pdf_masters.status`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: Yes (Multipart)

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\document\pdf\services\PdfService.js` (Line 49)
  - Snippet: `API.put(`/pdf-masters/${pdfId}`, formData, {             headers: { "Content-Type`

---

### `DELETE` /pdf-masters/{pdf_id}

- **Summary**: Delete Pdf
- **Router / Handler**: [`delete_pdf`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/pdf/router.py#L129) in `Backend\app\modules\pdf\router.py` (Line 129)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: DOCUMENT_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `pdf_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `language_master`, `pdf_masters`
- **SQLAlchemy Models**: `LanguageMaster`, `PdfMaster`
- **Operations Performed**: `DELETE`
- **Key Columns Referenced**: `pdf_masters.pdf_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\document\pdf\services\PdfService.js` (Line 62)
  - Snippet: `API.delete(`/pdf-masters/${pdfId}`);         return response.data;     } catch (erro`

---

## PPT Master

Total endpoints in module: **7**

### `GET` /ppt-masters

- **Summary**: List Ppts
- **Router / Handler**: [`list_ppts`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/ppt/router.py#L21) in `Backend\app\modules\ppt\router.py` (Line 21)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: DOCUMENT_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `search` | `any` | No | `None` | - |
| `page` | `integer` | No | `1` | - |
| `limit` | `integer` | No | `10` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `language_master`, `ppt_masters`
- **SQLAlchemy Models**: `LanguageMaster`, `PptMaster`
- **Operations Performed**: `SELECT`
- **Pagination Supported**: Yes
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\document\ppt\services\PptService.js` (Line 13)
  - Snippet: `API.get("/ppt-masters", { params });         return response.data;     }`

---

### `GET` /ppt-masters/export/csv

- **Summary**: Export Ppts
- **Router / Handler**: [`export_ppts`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/ppt/router.py#L40) in `Backend\app\modules\ppt\router.py` (Line 40)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: DOCUMENT_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `search` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\document\ppt\services\PptService.js` (Line 93)
  - Snippet: `API.get("/ppt-masters/export/csv", {             params,             responseType: `

---

### `GET` /ppt-masters/{ppt_id}/archived-versions

- **Summary**: Get Archived Versions
- **Router / Handler**: [`get_archived_versions`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/ppt/router.py#L51) in `Backend\app\modules\ppt\router.py` (Line 51)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: DOCUMENT_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `ppt_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `language_master`, `ppt_masters`
- **SQLAlchemy Models**: `LanguageMaster`, `PptMaster`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `ppt_masters.ppt_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\document\ppt\services\PptService.js` (Line 73)
  - Snippet: `API.get(             `/ppt-masters/${pptId}/archived-versions`         );         return response.da`

---

### `GET` /ppt-masters/{ppt_id}

- **Summary**: Get Ppt
- **Router / Handler**: [`get_ppt`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/ppt/router.py#L62) in `Backend\app\modules\ppt\router.py` (Line 62)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: DOCUMENT_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `ppt_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `language_master`, `ppt_masters`
- **SQLAlchemy Models**: `LanguageMaster`, `PptMaster`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `ppt_masters.ppt_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\document\ppt\services\PptService.js` (Line 37)
  - Snippet: `API.get(`/ppt-masters/${pptId}`);         return response.data;     } catch (erro`

---

### `POST` /ppt-masters

- **Summary**: Create Ppt
- **Router / Handler**: [`create_ppt`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/ppt/router.py#L73) in `Backend\app\modules\ppt\router.py` (Line 73)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: DOCUMENT_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `multipart/form-data`
- **Schema**: `Body_create_ppt_ppt_masters_post`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `ppt_name` | `string` | Yes | `None` | - |
| `ppt_description` | `any` | No | `None` | - |
| `cloud_url` | `any` | No | `None` | - |
| `language_id` | `any` | No | `None` | - |
| `status` | `any` | No | `1` | - |
| `media_file` | `any` | No | `None` | - |

**Example Request Payload:**
```json
{
  "ppt_name": "sample_ppt_name",
  "ppt_description": "sample_ppt_description",
  "cloud_url": "sample_cloud_url",
  "language_id": "sample_language_id",
  "status": "sample_status",
  "media_file": "sample_media_file"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `language_master`, `ppt_masters`
- **SQLAlchemy Models**: `LanguageMaster`, `PptMaster`
- **Operations Performed**: `INSERT`
- **Key Columns Referenced**: `language_master.language_id`, `ppt_masters.cloud_url`, `ppt_masters.language_id`, `ppt_masters.ppt_description`, `ppt_masters.ppt_name`, `ppt_masters.status`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: Yes (Multipart)

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\document\ppt\services\PptService.js` (Line 24)
  - Snippet: `API.post("/ppt-masters", formData, {             headers: { "Content-Type`

---

### `PUT` /ppt-masters/{ppt_id}

- **Summary**: Update Ppt
- **Router / Handler**: [`update_ppt`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/ppt/router.py#L100) in `Backend\app\modules\ppt\router.py` (Line 100)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: DOCUMENT_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `ppt_id` | `integer` | Yes | - |

#### Request Body

- **Content-Type**: `multipart/form-data`
- **Schema**: `Body_update_ppt_ppt_masters__ppt_id__put`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `ppt_name` | `any` | No | `None` | - |
| `ppt_description` | `any` | No | `None` | - |
| `cloud_url` | `any` | No | `None` | - |
| `language_id` | `any` | No | `None` | - |
| `status` | `any` | No | `None` | - |
| `media_file` | `any` | No | `None` | - |

**Example Request Payload:**
```json
{
  "ppt_name": "sample_ppt_name",
  "ppt_description": "sample_ppt_description",
  "cloud_url": "sample_cloud_url",
  "language_id": "sample_language_id",
  "status": "sample_status",
  "media_file": "sample_media_file"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `language_master`, `ppt_masters`
- **SQLAlchemy Models**: `LanguageMaster`, `PptMaster`
- **Operations Performed**: `UPDATE`
- **Key Columns Referenced**: `language_master.language_id`, `ppt_masters.cloud_url`, `ppt_masters.language_id`, `ppt_masters.ppt_description`, `ppt_masters.ppt_id`, `ppt_masters.ppt_name`, `ppt_masters.status`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: Yes (Multipart)

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\document\ppt\services\PptService.js` (Line 49)
  - Snippet: `API.put(`/ppt-masters/${pptId}`, formData, {             headers: { "Content-Type`

---

### `DELETE` /ppt-masters/{ppt_id}

- **Summary**: Delete Ppt
- **Router / Handler**: [`delete_ppt`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/ppt/router.py#L129) in `Backend\app\modules\ppt\router.py` (Line 129)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: DOCUMENT_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `ppt_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `language_master`, `ppt_masters`
- **SQLAlchemy Models**: `LanguageMaster`, `PptMaster`
- **Operations Performed**: `DELETE`
- **Key Columns Referenced**: `ppt_masters.ppt_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\document\ppt\services\PptService.js` (Line 62)
  - Snippet: `API.delete(`/ppt-masters/${pptId}`);         return response.data;     } catch (erro`

---

## Participants

Total endpoints in module: **18**

### `GET` /participants/states

- **Summary**: Get States
- **Router / Handler**: [`get_states`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/users/router.py#L132) in `Backend\app\modules\users\router.py` (Line 132)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: CREATE_PARTICIPANT
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[app__modules__users__schema__StateResponse]`

**Example Success Response:**
```json
[
  {
    "state_lgd_code": 1,
    "state_name": "sample_state_name"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `assessment_mapping`, `batch_masters`, `batch_participant`, `block_master`, `centre_masters`, `district_master`, `drop_bucket_items`, `drop_bucket_masters`, `drop_buckets`, `match_correct_answers`, `match_left_items`, `match_making_masters`, `match_right_items`, `mcq_master`, `mcq_question_options`, `module_masters`, `module_type`, `participant_dbs`, `participant_mcqs`, `participant_mm`, `participant_module`, `participant_scs`, `participantmasters`, `post_session_assessment`, `scq_master`, `scq_question_options`, `state_master`, `time_spent_module_log`, `users`
- **SQLAlchemy Models**: `AssessmentMapping`, `BatchMaster`, `BatchParticipant`, `BlockMaster`, `CentreMaster`, `DistrictMaster`, `DropBucket`, `DropBucketItem`, `DropBucketMaster`, `MatchCorrectAnswer`, `MatchLeftItem`, `MatchMakingMaster`, `MatchRightItem`, `McqMaster`, `McqQuestionOption`, `ModuleMaster`, `ModuleType`, `ParticipantDb`, `ParticipantMaster`, `ParticipantMcq`, `ParticipantMm`, `ParticipantModule`, `ParticipantScq`, `PostSessionAssessment`, `ScqMaster`, `ScqQuestionOption`, `StateMaster`, `TimeSpentModuleLog`, `User`
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\participant\services\ParticipantService.js` (Line 67)
  - Snippet: `API.get('/participants/states');         return response.data;     } catch (erro`
- File: `features\users\services\UserService.js` (Line 36)
  - Snippet: `API.get("/participants/states");     return data; };  export const getDistricts `

---

### `GET` /participants/districts/{state_lgd_code}

- **Summary**: Get Districts
- **Router / Handler**: [`get_districts`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/users/router.py#L139) in `Backend\app\modules\users\router.py` (Line 139)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: CREATE_PARTICIPANT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `state_lgd_code` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[app__modules__users__schema__DistrictResponse]`

**Example Success Response:**
```json
[
  {
    "district_lgd_code": 1,
    "district_name": "sample_district_name"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `assessment_mapping`, `batch_masters`, `batch_participant`, `block_master`, `centre_masters`, `district_master`, `drop_bucket_items`, `drop_bucket_masters`, `drop_buckets`, `match_correct_answers`, `match_left_items`, `match_making_masters`, `match_right_items`, `mcq_master`, `mcq_question_options`, `module_masters`, `module_type`, `participant_dbs`, `participant_mcqs`, `participant_mm`, `participant_module`, `participant_scs`, `participantmasters`, `post_session_assessment`, `scq_master`, `scq_question_options`, `state_master`, `time_spent_module_log`, `users`
- **SQLAlchemy Models**: `AssessmentMapping`, `BatchMaster`, `BatchParticipant`, `BlockMaster`, `CentreMaster`, `DistrictMaster`, `DropBucket`, `DropBucketItem`, `DropBucketMaster`, `MatchCorrectAnswer`, `MatchLeftItem`, `MatchMakingMaster`, `MatchRightItem`, `McqMaster`, `McqQuestionOption`, `ModuleMaster`, `ModuleType`, `ParticipantDb`, `ParticipantMaster`, `ParticipantMcq`, `ParticipantMm`, `ParticipantModule`, `ParticipantScq`, `PostSessionAssessment`, `ScqMaster`, `ScqQuestionOption`, `StateMaster`, `TimeSpentModuleLog`, `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `district_master.state_lgd_code`, `state_master.state_lgd_code`, `users.state_lgd_code`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\participant\services\ParticipantService.js` (Line 77)
  - Snippet: `API.get(`/participants/districts/${stateLgdCode}`);         return response.data;     } catch (erro`
- File: `features\users\services\UserService.js` (Line 41)
  - Snippet: `API.get(`/participants/districts/${stateLgdCode}`);     return data; };  export const getBlocks = a`

---

### `GET` /participants/blocks/{district_lgd_code}

- **Summary**: Get Blocks
- **Router / Handler**: [`get_blocks`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/users/router.py#L149) in `Backend\app\modules\users\router.py` (Line 149)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: CREATE_PARTICIPANT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `district_lgd_code` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[BlockResponse]`

**Example Success Response:**
```json
[
  {
    "block_lgd_code": 1,
    "block_name": "sample_block_name"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `assessment_mapping`, `batch_masters`, `batch_participant`, `block_master`, `centre_masters`, `district_master`, `drop_bucket_items`, `drop_bucket_masters`, `drop_buckets`, `match_correct_answers`, `match_left_items`, `match_making_masters`, `match_right_items`, `mcq_master`, `mcq_question_options`, `module_masters`, `module_type`, `participant_dbs`, `participant_mcqs`, `participant_mm`, `participant_module`, `participant_scs`, `participantmasters`, `post_session_assessment`, `scq_master`, `scq_question_options`, `state_master`, `time_spent_module_log`, `users`
- **SQLAlchemy Models**: `AssessmentMapping`, `BatchMaster`, `BatchParticipant`, `BlockMaster`, `CentreMaster`, `DistrictMaster`, `DropBucket`, `DropBucketItem`, `DropBucketMaster`, `MatchCorrectAnswer`, `MatchLeftItem`, `MatchMakingMaster`, `MatchRightItem`, `McqMaster`, `McqQuestionOption`, `ModuleMaster`, `ModuleType`, `ParticipantDb`, `ParticipantMaster`, `ParticipantMcq`, `ParticipantMm`, `ParticipantModule`, `ParticipantScq`, `PostSessionAssessment`, `ScqMaster`, `ScqQuestionOption`, `StateMaster`, `TimeSpentModuleLog`, `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `block_master.district_lgd_code`, `district_master.district_lgd_code`, `users.district_lgd_code`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\participant\services\ParticipantService.js` (Line 87)
  - Snippet: `API.get(`/participants/blocks/${districtLgdCode}`);         return response.data;     } catch (erro`
- File: `features\users\services\UserService.js` (Line 46)
  - Snippet: `API.get(`/participants/blocks/${districtLgdCode}`);     return data; };  export const getCentres = `

---

### `GET` /participants/centres/{block_id}

- **Summary**: Get Centres
- **Router / Handler**: [`get_centres`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/users/router.py#L162) in `Backend\app\modules\users\router.py` (Line 162)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: CREATE_PARTICIPANT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `block_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[app__modules__users__schema__CentreResponse]`

**Example Success Response:**
```json
[
  {
    "centre_id": 1,
    "centre_name": "sample_centre_name"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `assessment_mapping`, `batch_masters`, `batch_participant`, `block_master`, `centre_masters`, `district_master`, `drop_bucket_items`, `drop_bucket_masters`, `drop_buckets`, `match_correct_answers`, `match_left_items`, `match_making_masters`, `match_right_items`, `mcq_master`, `mcq_question_options`, `module_masters`, `module_type`, `participant_dbs`, `participant_mcqs`, `participant_mm`, `participant_module`, `participant_scs`, `participantmasters`, `post_session_assessment`, `scq_master`, `scq_question_options`, `state_master`, `time_spent_module_log`, `users`
- **SQLAlchemy Models**: `AssessmentMapping`, `BatchMaster`, `BatchParticipant`, `BlockMaster`, `CentreMaster`, `DistrictMaster`, `DropBucket`, `DropBucketItem`, `DropBucketMaster`, `MatchCorrectAnswer`, `MatchLeftItem`, `MatchMakingMaster`, `MatchRightItem`, `McqMaster`, `McqQuestionOption`, `ModuleMaster`, `ModuleType`, `ParticipantDb`, `ParticipantMaster`, `ParticipantMcq`, `ParticipantMm`, `ParticipantModule`, `ParticipantScq`, `PostSessionAssessment`, `ScqMaster`, `ScqQuestionOption`, `StateMaster`, `TimeSpentModuleLog`, `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `centre_masters.block_id`, `participantmasters.block_id`, `time_spent_module_log.id`, `users.id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\participant\services\ParticipantService.js` (Line 97)
  - Snippet: `API.get(`/participants/centres/${blockId}`);         return response.data;     } catch (erro`
- File: `features\users\services\UserService.js` (Line 51)
  - Snippet: `API.get(`/participants/centres/${blockId}`);     return data; }; `

---

### `GET` /participants/participants/all-centres

- **Summary**: Get All Centres
- **Router / Handler**: [`get_all_centres`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/users/router.py#L173) in `Backend\app\modules\users\router.py` (Line 173)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: CREATE_PARTICIPANT
- **Status / Health**: **Quirk / Duplicate Prefix Bug**
- **Detected Issues / Notes**:
  - Route path has duplicated prefix (/participants/participants/all-centres). Frontend accommodates this with matching double prefix.

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[app__modules__users__schema__CentreResponse]`

**Example Success Response:**
```json
[
  {
    "centre_id": 1,
    "centre_name": "sample_centre_name"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `assessment_mapping`, `batch_masters`, `batch_participant`, `block_master`, `centre_masters`, `district_master`, `drop_bucket_items`, `drop_bucket_masters`, `drop_buckets`, `match_correct_answers`, `match_left_items`, `match_making_masters`, `match_right_items`, `mcq_master`, `mcq_question_options`, `module_masters`, `module_type`, `participant_dbs`, `participant_mcqs`, `participant_mm`, `participant_module`, `participant_scs`, `participantmasters`, `post_session_assessment`, `scq_master`, `scq_question_options`, `state_master`, `time_spent_module_log`, `users`
- **SQLAlchemy Models**: `AssessmentMapping`, `BatchMaster`, `BatchParticipant`, `BlockMaster`, `CentreMaster`, `DistrictMaster`, `DropBucket`, `DropBucketItem`, `DropBucketMaster`, `MatchCorrectAnswer`, `MatchLeftItem`, `MatchMakingMaster`, `MatchRightItem`, `McqMaster`, `McqQuestionOption`, `ModuleMaster`, `ModuleType`, `ParticipantDb`, `ParticipantMaster`, `ParticipantMcq`, `ParticipantMm`, `ParticipantModule`, `ParticipantScq`, `PostSessionAssessment`, `ScqMaster`, `ScqQuestionOption`, `StateMaster`, `TimeSpentModuleLog`, `User`
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\participant\services\ParticipantService.js` (Line 107)
  - Snippet: `API.get('/participants/participants/all-centres');         return response.data;     } catch (erro`

---

### `GET` /participants/participants/batches

- **Summary**: Get Batches
- **Router / Handler**: [`get_batches`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/users/router.py#L182) in `Backend\app\modules\users\router.py` (Line 182)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: CREATE_PARTICIPANT
- **Status / Health**: **Quirk / Duplicate Prefix Bug**
- **Detected Issues / Notes**:
  - Route path has duplicated prefix (/participants/participants/batches). Frontend accommodates this with matching double prefix.

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `centre_id` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[app__modules__users__schema__BatchResponse]`

**Example Success Response:**
```json
[
  {
    "batch_id": 1,
    "batch_name": "sample_batch_name",
    "fy_year": "sample_fy_year",
    "centre_name": "sample_centre_name"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `assessment_mapping`, `batch_masters`, `batch_participant`, `block_master`, `centre_masters`, `district_master`, `drop_bucket_items`, `drop_bucket_masters`, `drop_buckets`, `match_correct_answers`, `match_left_items`, `match_making_masters`, `match_right_items`, `mcq_master`, `mcq_question_options`, `module_masters`, `module_type`, `participant_dbs`, `participant_mcqs`, `participant_mm`, `participant_module`, `participant_scs`, `participantmasters`, `post_session_assessment`, `scq_master`, `scq_question_options`, `state_master`, `time_spent_module_log`, `users`
- **SQLAlchemy Models**: `AssessmentMapping`, `BatchMaster`, `BatchParticipant`, `BlockMaster`, `CentreMaster`, `DistrictMaster`, `DropBucket`, `DropBucketItem`, `DropBucketMaster`, `MatchCorrectAnswer`, `MatchLeftItem`, `MatchMakingMaster`, `MatchRightItem`, `McqMaster`, `McqQuestionOption`, `ModuleMaster`, `ModuleType`, `ParticipantDb`, `ParticipantMaster`, `ParticipantMcq`, `ParticipantMm`, `ParticipantModule`, `ParticipantScq`, `PostSessionAssessment`, `ScqMaster`, `ScqQuestionOption`, `StateMaster`, `TimeSpentModuleLog`, `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `batch_masters.centre_id`, `centre_masters.centre_id`, `time_spent_module_log.id`, `users.centre_id`, `users.id`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\participant\services\ParticipantService.js` (Line 117)
  - Snippet: `API.get('/participants/participants/batches', {             params: centreId ? { centre_id: ce`

---

### `GET` /participants/enrollment/{batch_id}

- **Summary**: Get Enrollment
- **Router / Handler**: [`get_enrollment`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/users/router.py#L190) in `Backend\app\modules\users\router.py` (Line 190)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: CREATE_PARTICIPANT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `batch_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[EnrollmentResponse]`

**Example Success Response:**
```json
[
  {
    "participant_id": 1,
    "enrollment_no": "sample_enrollment_no",
    "participant_name": "sample_participant_name"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `assessment_mapping`, `batch_masters`, `batch_participant`, `block_master`, `centre_masters`, `district_master`, `drop_bucket_items`, `drop_bucket_masters`, `drop_buckets`, `match_correct_answers`, `match_left_items`, `match_making_masters`, `match_right_items`, `mcq_master`, `mcq_question_options`, `module_masters`, `module_type`, `participant_dbs`, `participant_mcqs`, `participant_mm`, `participant_module`, `participant_scs`, `participantmasters`, `post_session_assessment`, `scq_master`, `scq_question_options`, `state_master`, `time_spent_module_log`, `users`
- **SQLAlchemy Models**: `AssessmentMapping`, `BatchMaster`, `BatchParticipant`, `BlockMaster`, `CentreMaster`, `DistrictMaster`, `DropBucket`, `DropBucketItem`, `DropBucketMaster`, `MatchCorrectAnswer`, `MatchLeftItem`, `MatchMakingMaster`, `MatchRightItem`, `McqMaster`, `McqQuestionOption`, `ModuleMaster`, `ModuleType`, `ParticipantDb`, `ParticipantMaster`, `ParticipantMcq`, `ParticipantMm`, `ParticipantModule`, `ParticipantScq`, `PostSessionAssessment`, `ScqMaster`, `ScqQuestionOption`, `StateMaster`, `TimeSpentModuleLog`, `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `batch_masters.batch_id`, `batch_participant.batch_id`, `time_spent_module_log.id`, `users.id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\participant\services\ParticipantService.js` (Line 129)
  - Snippet: `API.get(`/participants/enrollment/${batchId}`);         return response.data;     } catch (erro`

---

### `POST` /participants/

- **Summary**: Create Participant
- **Router / Handler**: [`create_participant`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/users/router.py#L208) in `Backend\app\modules\users\router.py` (Line 208)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: CREATE_PARTICIPANT, Location Scope Hierarchy Assertion (State/District/Centre)
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `multipart/form-data`
- **Schema**: `Body_create_participant_participants__post`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `state_id` | `integer` | Yes | `None` | - |
| `district_id` | `integer` | Yes | `None` | - |
| `block_id` | `integer` | Yes | `None` | - |
| `centre_id` | `integer` | Yes | `None` | - |
| `batch_id` | `integer` | Yes | `None` | - |
| `participant_name` | `string` | Yes | `None` | - |
| `enrollment_no` | `string` | Yes | `None` | - |
| `username` | `string` | Yes | `None` | - |
| `password` | `string` | Yes | `None` | - |
| `gender` | `string` | Yes | `None` | - |
| `age` | `integer` | Yes | `None` | - |
| `email` | `any` | No | `None` | - |
| `mobile_no` | `any` | No | `None` | - |
| `pin` | `string` | Yes | `None` | - |
| `aadhaar_number` | `any` | No | `None` | - |
| `location` | `string` | Yes | `None` | - |
| `address` | `any` | No | `None` | - |
| `image` | `any` | No | `None` | - |

**Example Request Payload:**
```json
{
  "state_id": 1,
  "district_id": 1,
  "block_id": 1,
  "centre_id": 1,
  "batch_id": 1,
  "participant_name": "sample_participant_name",
  "enrollment_no": "sample_enrollment_no",
  "username": "sample_username",
  "password": "SecurePassword123",
  "gender": "sample_gender",
  "age": 1,
  "email": "user@example.com",
  "mobile_no": "9876543210",
  "pin": "sample_pin",
  "aadhaar_number": "sample_aadhaar_number",
  "location": "sample_location",
  "address": "sample_address",
  "image": "sample_image"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `INSERT`
- **Key Columns Referenced**: `users.block_lgd_code`, `users.centre_id`, `users.district_lgd_code`, `users.email`, `users.id`, `users.name`, `users.password`, `users.state_lgd_code`, `users.status`, `users.username`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: Yes (Multipart)

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\participant\services\ParticipantService.js` (Line 51)
  - Snippet: `API.post('/participants/', formData, {             headers: { 'Content-Type`

---

### `GET` /participants

- **Summary**: Get Participants
- **Router / Handler**: [`get_participants`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/users/router.py#L281) in `Backend\app\modules\users\router.py` (Line 281)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: CREATE_PARTICIPANT, Location Scope Clamping (State/District/Centre)
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `state_id` | `any` | No | `None` | - |
| `district_id` | `any` | No | `None` | - |
| `centre_id` | `any` | No | `None` | - |
| `batch_id` | `any` | No | `None` | - |
| `search` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[ParticipantListResponse]`

**Example Success Response:**
```json
[
  {
    "participant_id": 1,
    "participant_name": "sample_participant_name",
    "enrollment_no": "sample_enrollment_no",
    "image": "sample_image",
    "state_name": "sample_state_name",
    "district_name": "sample_district_name",
    "centre_name": "sample_centre_name",
    "batch_name": "sample_batch_name",
    "status": "sample_status",
    "course_progress": "sample_course_progress",
    "performance_status": "sample_performance_status"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `users.centre_id`, `users.id`, `users.role`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\participant\services\ParticipantService.js` (Line 9)
  - Snippet: `API.get('/participants', { params });         return response.data;     }`

---

### `GET` /participants/{participant_id}/report

- **Summary**: Get Participant Report
- **Router / Handler**: [`get_participant_report`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/users/router.py#L307) in `Backend\app\modules\users\router.py` (Line 307)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: CREATE_PARTICIPANT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `participant_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `ParticipantReportResponse`

**Example Success Response:**
```json
{
  "participant": "sample_participant",
  "attempt_wise_result": "sample_attempt_wise_result",
  "assessment_summary": "sample_assessment_summary"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `users.id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\participant\services\ParticipantService.js` (Line 143)
  - Snippet: `API.get(             `/participants/${participantId}/report`         );          return response.dat`

---

### `GET` /participants/{participant_id}/modules

- **Summary**: Get Participant Modules
- **Router / Handler**: [`get_participant_modules`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/users/router.py#L327) in `Backend\app\modules\users\router.py` (Line 327)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: CREATE_PARTICIPANT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `participant_id` | `integer` | Yes | - |

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `integer` | No | `1` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `users.id`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\participant\services\ParticipantService.js` (Line 159)
  - Snippet: `API.get(         `/participants/${participantId}/modules`,         { params: { language_id: Number(l`

---

### `POST` /participants/assign

- **Summary**: Assign Module
- **Router / Handler**: [`assign_module`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/users/router.py#L342) in `Backend\app\modules\users\router.py` (Line 342)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: CREATE_PARTICIPANT
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `ParticipantModuleActionRequest`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `participant_id` | `integer` | Yes | `None` | - |
| `module_id` | `integer` | Yes | `None` | - |
| `action` | `any` | No | `None` | - |

**Example Request Payload:**
```json
{
  "participant_id": 1,
  "module_id": 1,
  "action": "sample_action"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `MessageResponse`

**Example Success Response:**
```json
{
  "message": "sample_message"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `INSERT`
- **Key Columns Referenced**: `users.id`, `users.status`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\participant\services\ParticipantService.js` (Line 167)
  - Snippet: `API.post("/participants/assign", {         participant_id: participantId,        `

---

### `POST` /participants/unassign

- **Summary**: Unassign Module
- **Router / Handler**: [`unassign_module`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/users/router.py#L360) in `Backend\app\modules\users\router.py` (Line 360)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: CREATE_PARTICIPANT
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `ParticipantModuleActionRequest`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `participant_id` | `integer` | Yes | `None` | - |
| `module_id` | `integer` | Yes | `None` | - |
| `action` | `any` | No | `None` | - |

**Example Request Payload:**
```json
{
  "participant_id": 1,
  "module_id": 1,
  "action": "sample_action"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `MessageResponse`

**Example Success Response:**
```json
{
  "message": "sample_message"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `INSERT`
- **Key Columns Referenced**: `users.id`, `users.status`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\participant\services\ParticipantService.js` (Line 175)
  - Snippet: `API.post("/participants/unassign", {         participant_id: participantId,        `

---

### `GET` /participants/{participant_id}/key-details

- **Summary**: Get Participant Key Details
- **Router / Handler**: [`get_participant_key_details`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/users/router.py#L383) in `Backend\app\modules\users\router.py` (Line 383)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: CREATE_PARTICIPANT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `participant_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `users.id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\participant\services\ParticipantService.js` (Line 187)
  - Snippet: `API.get(         `/participants/${participantId}/key-details`     );     return response.data; };  e`

---

### `PUT` /participants/{participant_id}/change-password

- **Summary**: Change Participant Password
- **Router / Handler**: [`change_participant_password`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/users/router.py#L396) in `Backend\app\modules\users\router.py` (Line 396)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: CREATE_PARTICIPANT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `participant_id` | `integer` | Yes | - |

#### Request Body

- **Content-Type**: `application/x-www-form-urlencoded`
- **Schema**: `Body_change_participant_password_participants__participant_id__change_password_put`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `new_password` | `string` | Yes | `None` | - |

**Example Request Payload:**
```json
{
  "new_password": "SecurePassword123"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `UPDATE`
- **Key Columns Referenced**: `users.id`, `users.password`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\participant\services\ParticipantService.js` (Line 226)
  - Snippet: `API.put(             `/participants/${participantId}/change-password`,             formData,        `

---

### `GET` /participants/{participant_id}/time-spent

- **Summary**: Get Participant Time Spent
- **Router / Handler**: [`get_participant_time_spent`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/users/router.py#L416) in `Backend\app\modules\users\router.py` (Line 416)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: CREATE_PARTICIPANT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `participant_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `users.id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\participant\services\ParticipantService.js` (Line 194)
  - Snippet: `API.get(         `/participants/${participantId}/time-spent`     );     return response.data; };  //`

---

### `GET` /participants/{participant_id}/edit

- **Summary**: Get Participant Edit
- **Router / Handler**: [`get_participant_edit`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/users/router.py#L434) in `Backend\app\modules\users\router.py` (Line 434)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: CREATE_PARTICIPANT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `participant_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `users.id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\participant\services\ParticipantService.js` (Line 205)
  - Snippet: `API.get(`/participants/${participantId}/edit`);     return response.data; };  export const upda`

---

### `PUT` /participants/{participant_id}

- **Summary**: Update Participant
- **Router / Handler**: [`update_participant`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/users/router.py#L444) in `Backend\app\modules\users\router.py` (Line 444)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: CREATE_PARTICIPANT, Location Scope Hierarchy Assertion (State/District/Centre)
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `participant_id` | `integer` | Yes | - |

#### Request Body

- **Content-Type**: `multipart/form-data`
- **Schema**: `Body_update_participant_participants__participant_id__put`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `participant_name` | `string` | Yes | `None` | - |
| `age` | `integer` | Yes | `None` | - |
| `gender` | `string` | Yes | `None` | - |
| `email` | `any` | No | `None` | - |
| `mobile_no` | `any` | No | `None` | - |
| `pin` | `string` | Yes | `None` | - |
| `aadhaar_number` | `any` | No | `None` | - |
| `location` | `string` | Yes | `None` | - |
| `address` | `any` | No | `None` | - |
| `state_id` | `any` | No | `None` | - |
| `district_id` | `any` | No | `None` | - |
| `block_id` | `any` | No | `None` | - |
| `centre_id` | `any` | No | `None` | - |
| `batch_id` | `any` | No | `None` | - |
| `enrollment_no` | `any` | No | `None` | - |
| `image` | `any` | No | `None` | - |

**Example Request Payload:**
```json
{
  "participant_name": "sample_participant_name",
  "age": 1,
  "gender": "sample_gender",
  "email": "user@example.com",
  "mobile_no": "9876543210",
  "pin": "sample_pin",
  "aadhaar_number": "sample_aadhaar_number",
  "location": "sample_location",
  "address": "sample_address",
  "state_id": "sample_state_id",
  "district_id": "sample_district_id",
  "block_id": "sample_block_id",
  "centre_id": "sample_centre_id",
  "batch_id": "sample_batch_id",
  "enrollment_no": "sample_enrollment_no",
  "image": "sample_image"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `UPDATE`
- **Key Columns Referenced**: `users.block_lgd_code`, `users.centre_id`, `users.district_lgd_code`, `users.email`, `users.id`, `users.name`, `users.state_lgd_code`, `users.status`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: Yes (Multipart)

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\participant\services\ParticipantService.js` (Line 210)
  - Snippet: `API.put(`/participants/${participantId}`, formData, {         headers: { 'Content-Type': '`

---

## Reference Data

Total endpoints in module: **3**

### `GET` /reference/states

- **Summary**: Get States
- **Router / Handler**: [`get_states`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/reference_data/router.py#L23) in `Backend\app\modules\reference_data\router.py` (Line 23)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: REFERENCE_DATA
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[ReferenceStateResponse]`

**Example Success Response:**
```json
[
  {
    "code": 1,
    "name": "sample_name"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\master\state\services\StateService.js` (Line 88)
  - Snippet: `API.get("/reference/states");          return response.data.map(({ code, name`

---

### `GET` /reference/districts

- **Summary**: Get Districts
- **Router / Handler**: [`get_districts`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/reference_data/router.py#L31) in `Backend\app\modules\reference_data\router.py` (Line 31)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: REFERENCE_DATA
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Unused by Web Frontend (no frontend service or page calls this endpoint).

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `state_id` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[ReferenceDistrictResponse]`

**Example Success Response:**
```json
[
  {
    "code": 1,
    "name": "sample_name",
    "parent_code": 1
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `users.id`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

No matching frontend service call found in `Frontend/src` (Backend-only / Unused by web frontend).

---

### `GET` /reference/centres

- **Summary**: Get Centres
- **Router / Handler**: [`get_centres`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/reference_data/router.py#L40) in `Backend\app\modules\reference_data\router.py` (Line 40)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2, 3, 4, 5
- **Required Permissions / Scopes**: Module: REFERENCE_DATA
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - Unused by Web Frontend (no frontend service or page calls this endpoint).

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `state_id` | `any` | No | `None` | - |
| `district_id` | `any` | No | `None` | - |
| `search` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[ReferenceCentreResponse]`

**Example Success Response:**
```json
[
  {
    "id": 1,
    "name": "sample_name",
    "parent_code": "sample_parent_code"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `users.id`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

No matching frontend service call found in `Frontend/src` (Backend-only / Unused by web frontend).

---

## State Masters

Total endpoints in module: **5**

### `GET` /states

- **Summary**: Get States
- **Router / Handler**: [`get_states`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/master/state/router.py#L44) in `Backend\app\modules\master\state\router.py` (Line 44)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1
- **Required Permissions / Scopes**: Module: MASTER
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `state_name` | `any` | No | `None` | - |
| `status` | `any` | No | `None` | - |
| `page` | `integer` | No | `1` | - |
| `per_page` | `integer` | No | `10` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `StateListResponse`

**Example Success Response:**
```json
{
  "data": [],
  "total": 1,
  "page": 1,
  "per_page": 1,
  "total_pages": 1
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `users.name`, `users.status`
- **Pagination Supported**: Yes
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\master\state\services\StateService.js` (Line 8)
  - Snippet: `API.get("/states");         return response.data;     } catch (erro`

---

### `POST` /states

- **Summary**: Create State
- **Router / Handler**: [`create_state`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/master/state/router.py#L72) in `Backend\app\modules\master\state\router.py` (Line 72)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1
- **Required Permissions / Scopes**: Module: MASTER
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `StateCreateRequest`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `state_lgd_code` | `integer` | Yes | `None` | - |
| `state_name` | `string` | Yes | `None` | - |
| `status` | `string` | Yes | `None` | - |

**Example Request Payload:**
```json
{
  "state_lgd_code": 1,
  "state_name": "sample_state_name",
  "status": "sample_status"
}
```

#### Responses

- **Success Status Code**: `201`
- **Response Model**: `app__modules__master__state__schema__StateResponse`

**Example Success Response:**
```json
{
  "state_lgd_code": 1,
  "state_name": "sample_state_name",
  "status": "sample_status"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `INSERT`
- **Key Columns Referenced**: `users.role`, `users.status`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\master\state\services\StateService.js` (Line 37)
  - Snippet: `API.post("/states", data);         return response.data;     } catch`

---

### `GET` /states/{state_lgd_code}

- **Summary**: Get State
- **Router / Handler**: [`get_state`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/master/state/router.py#L94) in `Backend\app\modules\master\state\router.py` (Line 94)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1
- **Required Permissions / Scopes**: Module: MASTER
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `state_lgd_code` | `string` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `app__modules__master__state__schema__StateResponse`

**Example Success Response:**
```json
{
  "state_lgd_code": 1,
  "state_name": "sample_state_name",
  "status": "sample_status"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `users.state_lgd_code`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\master\state\services\StateService.js` (Line 21)
  - Snippet: `API.get(`/states/${id}`);         return response.data;     } catch (erro`

---

### `PUT` /states/{state_lgd_code}

- **Summary**: Update State
- **Router / Handler**: [`update_state`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/master/state/router.py#L110) in `Backend\app\modules\master\state\router.py` (Line 110)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1
- **Required Permissions / Scopes**: Module: MASTER
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `state_lgd_code` | `string` | Yes | - |

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `StateUpdateRequest`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `state_name` | `any` | No | `None` | - |
| `status` | `any` | No | `None` | - |

**Example Request Payload:**
```json
{
  "state_name": "sample_state_name",
  "status": "sample_status"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `app__modules__master__state__schema__StateResponse`

**Example Success Response:**
```json
{
  "state_lgd_code": 1,
  "state_name": "sample_state_name",
  "status": "sample_status"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `UPDATE`
- **Key Columns Referenced**: `users.role`, `users.state_lgd_code`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\master\state\services\StateService.js` (Line 50)
  - Snippet: `API.put(             `/states/${id}`,             data         );          return resp`

---

### `DELETE` /states/{state_lgd_code}

- **Summary**: Delete State
- **Router / Handler**: [`delete_state`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/master/state/router.py#L133) in `Backend\app\modules\master\state\router.py` (Line 133)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1
- **Required Permissions / Scopes**: Module: MASTER
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `state_lgd_code` | `string` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `DeleteStateResponse`

**Example Success Response:**
```json
{
  "message": "sample_message"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `DELETE`
- **Key Columns Referenced**: `users.role`, `users.state_lgd_code`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\master\state\services\StateService.js` (Line 70)
  - Snippet: `API.delete(             `/states/${id}`         );          return response.data;     } c`

---

## Topic Master

Total endpoints in module: **7**

### `GET` /topics

- **Summary**: Get Topics
- **Router / Handler**: [`get_topics`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/module/Topic/router.py#L21) in `Backend\app\modules\module\Topic\router.py` (Line 21)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `integer` | Yes | `None` | - |
| `search` | `any` | No | `None` | - |
| `page` | `integer` | No | `1` | - |
| `limit` | `integer` | No | `10` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `module_masters`, `self_paced_learning`, `topic_mapping`, `topic_master`
- **SQLAlchemy Models**: `ModuleMaster`, `SelfPacedLearning`, `TopicMapping`, `TopicMaster`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `module_masters.language_id`, `topic_master.language_id`
- **Pagination Supported**: Yes
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\module\Topic\services\TopicService.js` (Line 5)
  - Snippet: `API.get('/topics', { params });         return response.data;     }`
- File: `features\module\Topic\services\TopicService.js` (Line 88)
  - Snippet: `API.get("/topics", {         params: {             module_id: modul`

---

### `GET` /topics/{topic_id}

- **Summary**: Get Topic
- **Router / Handler**: [`get_topic`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/module/Topic/router.py#L44) in `Backend\app\modules\module\Topic\router.py` (Line 44)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `topic_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `module_masters`, `self_paced_learning`, `topic_mapping`, `topic_master`
- **SQLAlchemy Models**: `ModuleMaster`, `SelfPacedLearning`, `TopicMapping`, `TopicMaster`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `self_paced_learning.topic_id`, `topic_mapping.topic_id`, `topic_master.topic_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\module\Topic\services\TopicService.js` (Line 16)
  - Snippet: `API.get(`/topics/${topicId}`);         return response.data;     } catch (erro`

---

### `DELETE` /topics/{topic_id}

- **Summary**: Delete Topic
- **Router / Handler**: [`delete_topic`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/module/Topic/router.py#L59) in `Backend\app\modules\module\Topic\router.py` (Line 59)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `topic_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `module_masters`, `self_paced_learning`, `topic_mapping`, `topic_master`
- **SQLAlchemy Models**: `ModuleMaster`, `SelfPacedLearning`, `TopicMapping`, `TopicMaster`
- **Operations Performed**: `DELETE`
- **Key Columns Referenced**: `self_paced_learning.topic_id`, `topic_mapping.topic_id`, `topic_master.topic_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\module\Topic\services\TopicService.js` (Line 47)
  - Snippet: `API.delete(`/topics/${topicId}`);         return response.data;     } catch (erro`

---

### `POST` /topics

- **Summary**: Create Topics
- **Router / Handler**: [`create_topics`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/module/Topic/router.py#L75) in `Backend\app\modules\module\Topic\router.py` (Line 75)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `CreateTopicRequest`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `module_id` | `integer` | Yes | `None` | - |
| `topics` | `array` | Yes | `None` | - |
| `language_id` | `integer` | No | `1` | - |

**Example Request Payload:**
```json
{
  "module_id": 1,
  "topics": [],
  "language_id": 1
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `module_masters`, `self_paced_learning`, `topic_mapping`, `topic_master`
- **SQLAlchemy Models**: `ModuleMaster`, `SelfPacedLearning`, `TopicMapping`, `TopicMaster`
- **Operations Performed**: `INSERT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\module\Topic\services\TopicService.js` (Line 26)
  - Snippet: `API.post('/topics', topicData);         return response.data;     } `

---

### `POST` /topics/{topic_id}/translation

- **Summary**: Save Translation
- **Router / Handler**: [`save_translation`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/module/Topic/router.py#L92) in `Backend\app\modules\module\Topic\router.py` (Line 92)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `topic_id` | `integer` | Yes | - |

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `TopicTranslationRequest`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `language_id` | `integer` | Yes | `None` | - |
| `topic_name` | `string` | Yes | `None` | - |
| `is_active` | `string` | No | `1` | - |

**Example Request Payload:**
```json
{
  "language_id": 1,
  "topic_name": "sample_topic_name",
  "is_active": "sample_is_active"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `module_masters`, `self_paced_learning`, `topic_mapping`, `topic_master`
- **SQLAlchemy Models**: `ModuleMaster`, `SelfPacedLearning`, `TopicMapping`, `TopicMaster`
- **Operations Performed**: `INSERT`
- **Key Columns Referenced**: `self_paced_learning.topic_id`, `topic_mapping.topic_id`, `topic_master.topic_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\module\Topic\services\TopicService.js` (Line 75)
  - Snippet: `API.post(             `/topics/${topicId}/translation`,             payload         );          retu`

---

### `PUT` /topics/{topic_id}

- **Summary**: Update Topic
- **Router / Handler**: [`update_topic`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/module/Topic/router.py#L112) in `Backend\app\modules\module\Topic\router.py` (Line 112)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `topic_id` | `integer` | Yes | - |

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `UpdateTopicRequest`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `module_id` | `integer` | Yes | `None` | - |
| `topic_name` | `string` | Yes | `None` | - |
| `is_active` | `string` | Yes | `None` | - |

**Example Request Payload:**
```json
{
  "module_id": 1,
  "topic_name": "sample_topic_name",
  "is_active": "sample_is_active"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `module_masters`, `self_paced_learning`, `topic_mapping`, `topic_master`
- **SQLAlchemy Models**: `ModuleMaster`, `SelfPacedLearning`, `TopicMapping`, `TopicMaster`
- **Operations Performed**: `UPDATE`
- **Key Columns Referenced**: `self_paced_learning.topic_id`, `topic_mapping.topic_id`, `topic_master.topic_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\module\Topic\services\TopicService.js` (Line 37)
  - Snippet: `API.put(`/topics/${topicId}`, topicData);         return response.data;     } `

---

### `GET` /topics/{topic_id}/translation/{language_id}

- **Summary**: Get Topic Translation
- **Router / Handler**: [`get_topic_translation`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/module/Topic/router.py#L132) in `Backend\app\modules\module\Topic\router.py` (Line 132)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: MODULE_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `topic_id` | `integer` | Yes | - |
| `language_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `module_masters`, `self_paced_learning`, `topic_mapping`, `topic_master`
- **SQLAlchemy Models**: `ModuleMaster`, `SelfPacedLearning`, `TopicMapping`, `TopicMaster`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `module_masters.language_id`, `self_paced_learning.topic_id`, `topic_mapping.topic_id`, `topic_master.language_id`, `topic_master.topic_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\module\Topic\services\TopicService.js` (Line 62)
  - Snippet: `API.get(             `/topics/${topicId}/translation/${languageId}`         );          return respo`

---

## Users

Total endpoints in module: **6**

### `GET` /users/creatable-roles

- **Summary**: Get Creatable Roles
- **Router / Handler**: [`get_creatable_roles`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/users/router.py#L55) in `Backend\app\modules\users\router.py` (Line 55)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: CREATE_USER
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[CreatableRoleResponse]`

**Example Success Response:**
```json
[
  {
    "id": 1,
    "name": "sample_name"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `users.role`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\users\services\UserService.js` (Line 31)
  - Snippet: `API.get("/users/creatable-roles");     return data; };  export const getStates = a`

---

### `POST` /users

- **Summary**: Create User
- **Router / Handler**: [`create_user`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/users/router.py#L62) in `Backend\app\modules\users\router.py` (Line 62)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: CREATE_USER
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `UserCreateRequest`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `name` | `string` | Yes | `None` | - |
| `username` | `any` | No | `None` | - |
| `email` | `string` | Yes | `None` | - |
| `password` | `string` | Yes | `None` | - |
| `role` | `integer` | Yes | `None` | - |
| `responsibility` | `any` | No | `None` | - |
| `state_lgd_code` | `any` | No | `None` | - |
| `district_lgd_code` | `any` | No | `None` | - |
| `block_lgd_code` | `any` | No | `None` | - |
| `centre_id` | `any` | No | `None` | - |
| `status` | `string` | No | `1` | - |

**Example Request Payload:**
```json
{
  "name": "sample_name",
  "username": "sample_username",
  "email": "user@example.com",
  "password": "SecurePassword123",
  "role": 1,
  "responsibility": "sample_responsibility",
  "state_lgd_code": "sample_state_lgd_code",
  "district_lgd_code": "sample_district_lgd_code",
  "block_lgd_code": "sample_block_lgd_code",
  "centre_id": "sample_centre_id",
  "status": "sample_status"
}
```

#### Responses

- **Success Status Code**: `201`
- **Response Model**: `app__modules__users__schema__UserResponse`

**Example Success Response:**
```json
{
  "id": 1,
  "name": "sample_name",
  "username": "sample_username",
  "email": "user@example.com",
  "role": "sample_role",
  "responsibility": "sample_responsibility",
  "state_lgd_code": "sample_state_lgd_code",
  "district_lgd_code": "sample_district_lgd_code",
  "block_lgd_code": "sample_block_lgd_code",
  "centre_id": "sample_centre_id",
  "status": "sample_status",
  "created_at": "sample_created_at",
  "updated_at": "sample_updated_at"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `INSERT`
- **Key Columns Referenced**: `users.status`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\users\services\UserService.js` (Line 6)
  - Snippet: `API.post("/users", payload);     return data; };  export const getA`

---

### `GET` /users

- **Summary**: Get Users
- **Router / Handler**: [`get_users`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/users/router.py#L79) in `Backend\app\modules\users\router.py` (Line 79)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: CREATE_USER
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `list[UserListItemResponse]`

**Example Success Response:**
```json
[
  {
    "id": 1,
    "name": "sample_name",
    "email": "user@example.com",
    "role": "sample_role",
    "role_name": "sample_role_name",
    "responsibility": "sample_responsibility",
    "status": "sample_status"
  }
]
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\users\services\UserService.js` (Line 11)
  - Snippet: `API.get("/users");     return data; }  export const getUserById = `

---

### `GET` /users/{user_id}

- **Summary**: Get User By Id
- **Router / Handler**: [`get_user_by_id`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/users/router.py#L87) in `Backend\app\modules\users\router.py` (Line 87)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: CREATE_USER
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `user_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `UserDetailResponse`

**Example Success Response:**
```json
{
  "id": 1,
  "name": "sample_name",
  "username": "sample_username",
  "email": "user@example.com",
  "role": "sample_role",
  "role_name": "sample_role_name",
  "responsibility": "sample_responsibility",
  "state_lgd_code": "sample_state_lgd_code",
  "state_name": "sample_state_name",
  "district_lgd_code": "sample_district_lgd_code",
  "district_name": "sample_district_name",
  "block_lgd_code": "sample_block_lgd_code",
  "block_name": "sample_block_name",
  "centre_id": "sample_centre_id",
  "centre_name": "sample_centre_name",
  "status": "sample_status",
  "created_at": "sample_created_at",
  "updated_at": "sample_updated_at"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `users.id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\users\services\UserService.js` (Line 16)
  - Snippet: `API.get(`/users/${userId}`);     return data; }  export const updateUser = a`

---

### `PUT` /users/{user_id}

- **Summary**: Update User
- **Router / Handler**: [`update_user`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/users/router.py#L99) in `Backend\app\modules\users\router.py` (Line 99)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: CREATE_USER
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `user_id` | `integer` | Yes | - |

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `UserUpdateRequest`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `name` | `string` | Yes | `None` | - |
| `username` | `any` | No | `None` | - |
| `email` | `string` | Yes | `None` | - |
| `role` | `integer` | Yes | `None` | - |
| `responsibility` | `any` | No | `None` | - |
| `state_lgd_code` | `any` | No | `None` | - |
| `district_lgd_code` | `any` | No | `None` | - |
| `block_lgd_code` | `any` | No | `None` | - |
| `centre_id` | `any` | No | `None` | - |
| `status` | `string` | Yes | `None` | - |
| `password` | `any` | No | `None` | - |

**Example Request Payload:**
```json
{
  "name": "sample_name",
  "username": "sample_username",
  "email": "user@example.com",
  "role": 1,
  "responsibility": "sample_responsibility",
  "state_lgd_code": "sample_state_lgd_code",
  "district_lgd_code": "sample_district_lgd_code",
  "block_lgd_code": "sample_block_lgd_code",
  "centre_id": "sample_centre_id",
  "status": "sample_status",
  "password": "SecurePassword123"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `app__modules__users__schema__UserResponse`

**Example Success Response:**
```json
{
  "id": 1,
  "name": "sample_name",
  "username": "sample_username",
  "email": "user@example.com",
  "role": "sample_role",
  "responsibility": "sample_responsibility",
  "state_lgd_code": "sample_state_lgd_code",
  "district_lgd_code": "sample_district_lgd_code",
  "block_lgd_code": "sample_block_lgd_code",
  "centre_id": "sample_centre_id",
  "status": "sample_status",
  "created_at": "sample_created_at",
  "updated_at": "sample_updated_at"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `UPDATE`
- **Key Columns Referenced**: `users.id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\users\services\UserService.js` (Line 21)
  - Snippet: `API.put(`/users/${userId}`, payload);     return data; }  export const delet`

---

### `DELETE` /users/{user_id}

- **Summary**: Delete User
- **Router / Handler**: [`delete_user`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/users/router.py#L114) in `Backend\app\modules\users\router.py` (Line 114)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: CREATE_USER
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `user_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `MessageResponse`

**Example Success Response:**
```json
{
  "message": "sample_message"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `users`
- **SQLAlchemy Models**: `User`
- **Operations Performed**: `DELETE`
- **Key Columns Referenced**: `users.id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\users\services\UserService.js` (Line 26)
  - Snippet: `API.delete(`/users/${userId}`);     return data; };  export const getCreatableR`

---

## VIDEO Master

Total endpoints in module: **7**

### `GET` /video-masters

- **Summary**: List Videos
- **Router / Handler**: [`list_videos`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/video/router.py#L21) in `Backend\app\modules\video\router.py` (Line 21)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: DOCUMENT_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `search` | `any` | No | `None` | - |
| `page` | `integer` | No | `1` | - |
| `limit` | `integer` | No | `10` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `language_master`, `video_masters`
- **SQLAlchemy Models**: `LanguageMaster`, `VideoMaster`
- **Operations Performed**: `SELECT`
- **Pagination Supported**: Yes
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\document\video\services\VideoService.js` (Line 13)
  - Snippet: `API.get("/video-masters", { params });         return response.data;     }`

---

### `GET` /video-masters/export/csv

- **Summary**: Export Videos
- **Router / Handler**: [`export_videos`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/video/router.py#L40) in `Backend\app\modules\video\router.py` (Line 40)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: DOCUMENT_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Query Parameters:**

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `search` | `any` | No | `None` | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `SELECT`
- **Pagination Supported**: No
- **Filtering Supported**: Yes
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\document\video\services\VideoService.js` (Line 93)
  - Snippet: `API.get("/video-masters/export/csv", {             params,             responseType: `

---

### `GET` /video-masters/{video_id}/archived-versions

- **Summary**: Get Archived Versions
- **Router / Handler**: [`get_archived_versions`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/video/router.py#L51) in `Backend\app\modules\video\router.py` (Line 51)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: DOCUMENT_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `video_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `language_master`, `video_masters`
- **SQLAlchemy Models**: `LanguageMaster`, `VideoMaster`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `video_masters.video_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\document\video\services\VideoService.js` (Line 73)
  - Snippet: `API.get(             `/video-masters/${videoId}/archived-versions`         );         return respons`

---

### `GET` /video-masters/{video_id}

- **Summary**: Get Video
- **Router / Handler**: [`get_video`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/video/router.py#L62) in `Backend\app\modules\video\router.py` (Line 62)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: DOCUMENT_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `video_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `language_master`, `video_masters`
- **SQLAlchemy Models**: `LanguageMaster`, `VideoMaster`
- **Operations Performed**: `SELECT`
- **Key Columns Referenced**: `video_masters.video_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\document\video\services\VideoService.js` (Line 37)
  - Snippet: `API.get(`/video-masters/${videoId}`);         return response.data;     } catch (erro`

---

### `POST` /video-masters

- **Summary**: Create Video
- **Router / Handler**: [`create_video`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/video/router.py#L73) in `Backend\app\modules\video\router.py` (Line 73)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: DOCUMENT_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

No path, query, or custom header parameters required.

#### Request Body

- **Content-Type**: `multipart/form-data`
- **Schema**: `Body_create_video_video_masters_post`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `video_name` | `string` | Yes | `None` | - |
| `video_description` | `any` | No | `None` | - |
| `youtube_url` | `any` | No | `None` | - |
| `language_id` | `any` | No | `None` | - |
| `status` | `any` | No | `1` | - |
| `media_file` | `any` | No | `None` | - |

**Example Request Payload:**
```json
{
  "video_name": "sample_video_name",
  "video_description": "sample_video_description",
  "youtube_url": "sample_youtube_url",
  "language_id": "sample_language_id",
  "status": "sample_status",
  "media_file": "sample_media_file"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `language_master`, `video_masters`
- **SQLAlchemy Models**: `LanguageMaster`, `VideoMaster`
- **Operations Performed**: `INSERT`
- **Key Columns Referenced**: `language_master.language_id`, `video_masters.language_id`, `video_masters.status`, `video_masters.video_description`, `video_masters.video_name`, `video_masters.youtube_url`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: Yes (Multipart)

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\document\video\services\VideoService.js` (Line 24)
  - Snippet: `API.post("/video-masters", formData, {             headers: { "Content-Type`

---

### `PUT` /video-masters/{video_id}

- **Summary**: Update Video
- **Router / Handler**: [`update_video`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/video/router.py#L100) in `Backend\app\modules\video\router.py` (Line 100)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: DOCUMENT_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `video_id` | `integer` | Yes | - |

#### Request Body

- **Content-Type**: `multipart/form-data`
- **Schema**: `Body_update_video_video_masters__video_id__put`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `video_name` | `any` | No | `None` | - |
| `video_description` | `any` | No | `None` | - |
| `youtube_url` | `any` | No | `None` | - |
| `language_id` | `any` | No | `None` | - |
| `status` | `any` | No | `None` | - |
| `media_file` | `any` | No | `None` | - |

**Example Request Payload:**
```json
{
  "video_name": "sample_video_name",
  "video_description": "sample_video_description",
  "youtube_url": "sample_youtube_url",
  "language_id": "sample_language_id",
  "status": "sample_status",
  "media_file": "sample_media_file"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `language_master`, `video_masters`
- **SQLAlchemy Models**: `LanguageMaster`, `VideoMaster`
- **Operations Performed**: `UPDATE`
- **Key Columns Referenced**: `language_master.language_id`, `video_masters.language_id`, `video_masters.status`, `video_masters.video_description`, `video_masters.video_id`, `video_masters.video_name`, `video_masters.youtube_url`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: Yes (Multipart)

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\document\video\services\VideoService.js` (Line 49)
  - Snippet: `API.put(`/video-masters/${videoId}`, formData, {             headers: { "Content-Type`

---

### `DELETE` /video-masters/{video_id}

- **Summary**: Delete Video
- **Router / Handler**: [`delete_video`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/video/router.py#L129) in `Backend\app\modules\video\router.py` (Line 129)
- **Authentication**: `Bearer Token (User JWT)`
- **Allowed Roles**: 1, 2
- **Required Permissions / Scopes**: Module: DOCUMENT_MANAGEMENT
- **Status / Health**: **Active / Healthy**

#### Parameters

**Path Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `video_id` | `integer` | Yes | - |

#### Request Body

No request body expected.

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `401`: Unauthorized (Missing, expired, or invalid JWT Bearer token)
  - `403`: Forbidden (User lacks required role or module permission)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: `language_master`, `video_masters`
- **SQLAlchemy Models**: `LanguageMaster`, `VideoMaster`
- **Operations Performed**: `DELETE`
- **Key Columns Referenced**: `video_masters.video_id`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

**Called by Frontend Client:**

- File: `features\document\video\services\VideoService.js` (Line 62)
  - Snippet: `API.delete(`/video-masters/${videoId}`);         return response.data;     } catch (erro`

---

## WWW Integration

Total endpoints in module: **1**

### `POST` /integrations/www/trainee

- **Summary**: Create Www Trainee
- **Router / Handler**: [`create_www_trainee`](file:///C:/Users/sagar/OneDrive/Desktop/Azad-LMS/Backend/app/modules/Integration/router.py#L17) in `Backend\app\modules\Integration\router.py` (Line 17)
- **Authentication**: `API Key / Custom Token (WWW Integration)`
- **Allowed Roles**: WWW External Integration Service
- **Required Permissions / Scopes**: None
- **Status / Health**: **Active / Healthy**
- **Detected Issues / Notes**:
  - External Integration Endpoint (used by third-party webhook/service).

#### Parameters

**Header Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `authorization` | `string` | Yes | - |

#### Request Body

- **Content-Type**: `application/json`
- **Schema**: `WWWTraineeCreateRequest`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `enrollment_no` | `string` | Yes | `None` | - |
| `participant_name` | `string` | Yes | `None` | - |
| `gender` | `string` | Yes | `None` | - |
| `age` | `integer` | Yes | `None` | - |
| `mobile_no` | `any` | No | `None` | - |
| `email` | `any` | No | `None` | - |
| `address` | `any` | No | `None` | - |
| `state_code` | `string` | Yes | `None` | - |
| `district_code` | `string` | Yes | `None` | - |
| `centre_code` | `string` | Yes | `None` | - |
| `batch_id` | `string` | Yes | `None` | - |
| `username` | `string` | Yes | `None` | - |
| `password` | `string` | Yes | `None` | - |
| `pin` | `any` | No | `None` | - |
| `location` | `any` | No | `None` | - |

**Example Request Payload:**
```json
{
  "enrollment_no": "sample_enrollment_no",
  "participant_name": "sample_participant_name",
  "gender": "sample_gender",
  "age": 1,
  "mobile_no": "9876543210",
  "email": "user@example.com",
  "address": "sample_address",
  "state_code": "sample_state_code",
  "district_code": "sample_district_code",
  "centre_code": "sample_centre_code",
  "batch_id": "sample_batch_id",
  "username": "sample_username",
  "password": "SecurePassword123",
  "pin": "sample_pin",
  "location": "sample_location"
}
```

#### Responses

- **Success Status Code**: `200`
- **Response Model**: `dict`

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Operation completed successfully"
}
```

- **Possible Error Status Codes**: `400`, `401`, `403`, `404`, `409`, `422`, `500`
  - `400`: Bad Request (Validation / Business logic violation)
  - `404`: Not Found (Target record does not exist)
  - `409`: Conflict (Unique constraint violation, e.g. duplicate email/username)
  - `422`: Unprocessable Entity (Request body / query parameter schema validation failure)
  - `500`: Internal Server Error (Unhandled exception)

#### Database Operations & Architecture

- **Database Tables Accessed**: None direct
- **SQLAlchemy Models**: None direct
- **Operations Performed**: `INSERT`
- **Pagination Supported**: No
- **Filtering Supported**: No
- **Sorting Supported**: No
- **File Upload Handling**: No

#### Frontend Integration

External service integration endpoint (webhook / batch ingestion).

---

