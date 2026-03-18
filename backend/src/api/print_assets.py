"""Protected API for the print-ready originals archive."""

from __future__ import annotations

import hashlib
import hmac
import time
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.api.dependencies import get_print_archive_store
from src.config import settings
from src.core.print_archive import PrintArchiveStore
from src.models import APIResponse, PrintArchiveListResponse

router = APIRouter()

PRINT_ARCHIVE_COOKIE_NAME = "print_archive_auth"
PRINT_ARCHIVE_COOKIE_PATH = "/api/v1/print-assets"


class PrintArchiveAuthRequest(BaseModel):
    """Password verification payload for the print archive."""

    password: str = Field(..., description="Print archive password")


class PrintArchiveAuthStatusResponse(BaseModel):
    """Authentication status for the print archive UI."""

    authenticated: bool = Field(..., description="Whether the print archive cookie is valid")


def _build_print_archive_signature(timestamp: int) -> str:
    return hmac.new(
        settings.print_archive_password.encode("utf-8"),
        str(timestamp).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _create_print_archive_token() -> str:
    timestamp = int(time.time())
    signature = _build_print_archive_signature(timestamp)
    return f"{timestamp}.{signature}"


def _is_valid_print_archive_token(token: str | None) -> bool:
    if not token:
        return False

    try:
        raw_timestamp, signature = token.split(".", 1)
        timestamp = int(raw_timestamp)
    except (TypeError, ValueError):
        return False

    if (time.time() - timestamp) > settings.print_archive_auth_max_age_seconds:
        return False

    expected_signature = _build_print_archive_signature(timestamp)
    return hmac.compare_digest(signature, expected_signature)


def _set_print_archive_cookie(response: Response) -> None:
    response.set_cookie(
        key=PRINT_ARCHIVE_COOKIE_NAME,
        value=_create_print_archive_token(),
        max_age=settings.print_archive_auth_max_age_seconds,
        httponly=True,
        samesite="lax",
        secure=False,
        path=PRINT_ARCHIVE_COOKIE_PATH,
    )


def _clear_print_archive_cookie(response: Response) -> None:
    response.delete_cookie(
        key=PRINT_ARCHIVE_COOKIE_NAME,
        path=PRINT_ARCHIVE_COOKIE_PATH,
    )


def require_print_archive_auth(
    print_archive_auth: Annotated[str | None, Cookie(alias=PRINT_ARCHIVE_COOKIE_NAME)] = None,
) -> None:
    """Block access to the print archive when the cookie is missing or invalid."""
    if _is_valid_print_archive_token(print_archive_auth):
        return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Print archive authentication required",
    )


@router.post("/print-assets/auth/verify", response_model=APIResponse[PrintArchiveAuthStatusResponse])
async def verify_print_archive_password(
    body: PrintArchiveAuthRequest,
    response: Response,
) -> APIResponse[PrintArchiveAuthStatusResponse]:
    """Verify the separate password for the print archive."""
    if body.password != settings.print_archive_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid print archive password",
        )

    _set_print_archive_cookie(response)
    return APIResponse(
        success=True,
        data=PrintArchiveAuthStatusResponse(authenticated=True),
        error=None,
    )


@router.get("/print-assets/auth/status", response_model=APIResponse[PrintArchiveAuthStatusResponse])
async def get_print_archive_auth_status(
    print_archive_auth: Annotated[str | None, Cookie(alias=PRINT_ARCHIVE_COOKIE_NAME)] = None,
) -> APIResponse[PrintArchiveAuthStatusResponse]:
    """Return whether the current request is authenticated for print archive access."""
    return APIResponse(
        success=True,
        data=PrintArchiveAuthStatusResponse(
            authenticated=_is_valid_print_archive_token(print_archive_auth),
        ),
        error=None,
    )


@router.post("/print-assets/auth/logout", response_model=APIResponse[PrintArchiveAuthStatusResponse])
async def logout_print_archive(response: Response) -> APIResponse[PrintArchiveAuthStatusResponse]:
    """Clear the print archive cookie."""
    _clear_print_archive_cookie(response)
    return APIResponse(
        success=True,
        data=PrintArchiveAuthStatusResponse(authenticated=False),
        error=None,
    )


@router.get(
    "/print-assets/assets",
    response_model=APIResponse[PrintArchiveListResponse],
    dependencies=[Depends(require_print_archive_auth)],
)
async def list_print_assets(
    store: Annotated[PrintArchiveStore, Depends(get_print_archive_store)],
) -> APIResponse[PrintArchiveListResponse]:
    """Return all archived original images."""
    return APIResponse(
        success=True,
        data=PrintArchiveListResponse(assets=store.list_assets()),
        error=None,
    )


@router.get(
    "/print-assets/assets/download-all",
    dependencies=[Depends(require_print_archive_auth)],
)
async def download_all_print_assets(
    store: Annotated[PrintArchiveStore, Depends(get_print_archive_store)],
) -> Response:
    """Download the full print archive as a ZIP file."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    filename = f"print-archive-{timestamp}.zip"
    return Response(
        content=store.build_zip_bytes(),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get(
    "/print-assets/assets/{asset_id}/image",
    dependencies=[Depends(require_print_archive_auth)],
)
async def get_print_asset_image(
    asset_id: str,
    store: Annotated[PrintArchiveStore, Depends(get_print_archive_store)],
) -> FileResponse:
    """Return one archived PNG inline for previews."""
    asset = store.get_asset(asset_id)
    file_path = store.get_asset_file_path(asset_id)
    if asset is None or file_path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Print archive asset not found: {asset_id}",
        )

    return FileResponse(
        path=file_path,
        media_type="image/png",
    )


@router.get(
    "/print-assets/assets/{asset_id}/download",
    dependencies=[Depends(require_print_archive_auth)],
)
async def download_print_asset(
    asset_id: str,
    store: Annotated[PrintArchiveStore, Depends(get_print_archive_store)],
) -> FileResponse:
    """Download one archived original PNG."""
    asset = store.get_asset(asset_id)
    file_path = store.get_asset_file_path(asset_id)
    if asset is None or file_path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Print archive asset not found: {asset_id}",
        )

    return FileResponse(
        path=file_path,
        media_type="image/png",
        filename=asset.filename,
    )
