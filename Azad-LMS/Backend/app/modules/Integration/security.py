import os

from fastapi import Header, HTTPException, status


def verify_www_token(
    authorization: str = Header(...),
):
    expected_token = os.getenv("WWW_LMS_API_TOKEN")

    if not expected_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="WWW LMS API token is not configured.",
        )

    if authorization != f"Bearer {expected_token}":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization token.",
        )

    return True
