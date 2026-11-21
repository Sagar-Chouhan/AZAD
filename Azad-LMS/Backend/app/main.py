import logging
import os
from typing import Callable, Awaitable

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles


# Routers
from app.modules.Integration.router import router as integration_router
from app.modules.users.router import router as user_router
from app.modules.auth.router import router as auth_router
from app.modules.centres.router import router as centres_router
from app.modules.master.state.router import router as state_router
from app.modules.master.district.router import router as district_router
from app.modules.audit_log.router import router as audit_log_router
from app.modules.batch.router import router as batch_router
from app.modules.document.router import router as document_router
from app.modules.reference_data.router import router as reference_data_router
from app.modules.course.router import router as course_router
from app.modules.module.Topic.router import topic_router as topic_router
from app.modules.module.router import router as module_router
from app.modules.pdf.router import router as pdf_router
from app.modules.ppt.router import router as ppt_router
from app.modules.video.router import router as video_router
from app.modules.dashboard.router import router as dashboard_router

from app.modules.assessment.router.mcq_route import router as mcq_router
from app.modules.assessment.router.scq_route import router as scq_router
from app.modules.assessment.router.drop_bucket_route import (
    router as drop_bucket_router,
)
from app.modules.assessment.router.match_making_route import (
    router as match_making_router,
)
from app.modules.assessment.router.match_correct_answer_route import (
    router as match_correct_answer_router,
)
from app.modules.assessment.router.upload_route import (
    router as assessment_upload_router,
)

from app.modules.mobile.auth.router import router as mobile_auth_router
from app.modules.mobile.dashboard.routes import router as mobile_dashboard_router
from app.modules.mobile.module.routes import router as mobile_module_router
from app.modules.mobile.feedback.routes import router as feedback_router

from app.modules.users.exceptions import (
    EmailAlreadyExistsError,
    UserNotFoundError,
)


# ============================================================
# Application
# ============================================================

app = FastAPI(
    title="Azad LMS",
    description="Azad LMS API",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

_DEFAULT_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://lms.azadfoundation.com",
    "https://demo-azadlms.indevconsultancy.in",
    "http://localhost:8066",
    "http://127.0.0.1:8066",
    "http://localhost:4173",
    "http://192.168.10.19:4173",
)

_raw_origins = os.getenv("ALLOWED_ORIGINS")

if _raw_origins:
    origins = [
        origin.strip()
        for origin in _raw_origins.split(",")
        if origin.strip()
    ]
else:
    origins = list(_DEFAULT_ORIGINS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Request Validation Exception Handler
# ============================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
        },
    )


# ============================================================
# Security Headers + Global Exception Logging
# ============================================================

@app.middleware("http")
async def security_headers(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    try:
        response: Response = await call_next(request)

    except Exception:
        logging.getLogger("uvicorn.error").exception(
            "Unhandled error on %s %s",
            request.method,
            request.url.path,
        )

        response = JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error.",
            },
        )

    response.headers.setdefault(
        "X-Content-Type-Options",
        "nosniff",
    )

    if not request.url.path.startswith("/uploads"):
        response.headers.setdefault(
            "X-Frame-Options",
            "DENY",
        )

    response.headers.setdefault(
        "Referrer-Policy",
        "strict-origin-when-cross-origin",
    )

    return response


# ============================================================
# Static Upload Directories (Multi-directory Support)
# ============================================================

from pathlib import Path
from fastapi.responses import FileResponse

class MultiDirectoryStaticFiles(StaticFiles):
    def __init__(self, directories: list[str | Path], **kwargs):
        self.candidate_dirs = [Path(d).resolve() for d in directories if Path(d).exists()]
        first_dir = str(self.candidate_dirs[0]) if self.candidate_dirs else "."
        super().__init__(directory=first_dir, **kwargs)

    def lookup_file(self, path: str) -> Path | None:
        clean_rel = path.lstrip("/\\").replace("\\", "/")

        for d in self.candidate_dirs:
            candidate = (d / clean_rel).resolve()
            if str(candidate).startswith(str(d)) and candidate.is_file():
                return candidate

        if clean_rel.startswith("uploads/"):
            sub_rel = clean_rel[8:]
            for d in self.candidate_dirs:
                candidate = (d / sub_rel).resolve()
                if str(candidate).startswith(str(d)) and candidate.is_file():
                    return candidate

        filename = Path(clean_rel).name
        if filename:
            for d in self.candidate_dirs:
                matches = list(d.glob(f"**/{filename}"))
                if matches and matches[0].is_file():
                    return matches[0]

        return None

    async def get_response(self, path: str, scope) -> Response:
        found_file = self.lookup_file(path)
        if found_file:
            return FileResponse(str(found_file))
        return await super().get_response(path, scope)

_APP_DIR = os.path.dirname(os.path.abspath(__file__))
_BASE_DIR = os.path.dirname(_APP_DIR)
_UPLOAD_DIR = os.path.join(_BASE_DIR, "uploads")
os.makedirs(_UPLOAD_DIR, exist_ok=True)

_STATIC_DIRS = [
    _UPLOAD_DIR,
    os.path.join(_APP_DIR, "storage", "app", "uploads"),
    os.path.join(_APP_DIR, "storage", "uploads"),
    os.path.join(_APP_DIR, "storage", "app", "public"),
    os.path.join(_APP_DIR, "storage", "app", "images"),
]

app.mount(
    "/uploads",
    MultiDirectoryStaticFiles(directories=_STATIC_DIRS),
    name="uploads",
)

app.mount(
    "/app/storage/app/uploads",
    MultiDirectoryStaticFiles(directories=_STATIC_DIRS),
    name="storage_app_uploads",
)


# ============================================================
# Application Exception Handlers
# ============================================================

@app.exception_handler(UserNotFoundError)
async def user_not_found_exception_handler(
    request: Request,
    exc: UserNotFoundError,
):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "detail": "User not found.",
        },
    )


@app.exception_handler(EmailAlreadyExistsError)
async def email_already_exists_exception_handler(
    request: Request,
    exc: EmailAlreadyExistsError,
):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": "A user with this email already exists.",
        },
    )


# ============================================================
# Application Routers
# ============================================================

app.include_router(user_router)
app.include_router(auth_router)
app.include_router(integration_router)
app.include_router(centres_router)

app.include_router(state_router)
app.include_router(district_router)

app.include_router(audit_log_router)

app.include_router(document_router)
app.include_router(reference_data_router)

app.include_router(course_router)
app.include_router(batch_router)

app.include_router(topic_router)
app.include_router(module_router)

app.include_router(pdf_router)
app.include_router(ppt_router)
app.include_router(video_router)

app.include_router(dashboard_router)

app.include_router(mcq_router)
app.include_router(scq_router)
app.include_router(drop_bucket_router)
app.include_router(match_making_router)
app.include_router(match_correct_answer_router)
app.include_router(assessment_upload_router)

# Mobile APIs
app.include_router(mobile_auth_router)
app.include_router(mobile_dashboard_router)
app.include_router(mobile_module_router)
app.include_router(feedback_router)