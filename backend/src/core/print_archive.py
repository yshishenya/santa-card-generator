"""Persistent on-disk storage for print-ready original images."""

from __future__ import annotations

import csv
import io
import json
import re
import threading
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from src.models.print_archive import PrintArchiveAsset, StoredPrintArchiveAsset


class PrintArchiveStore:
    """Store finalized original PNG files and metadata for later printing."""

    def __init__(self, storage_path: str) -> None:
        self._base_path = Path(storage_path)
        self._files_path = self._base_path / "files"
        self._index_path = self._base_path / "index.json"
        self._lock = threading.Lock()
        self._ensure_directories()

    def list_assets(self) -> list[PrintArchiveAsset]:
        """Return public archive items sorted newest first."""
        with self._lock:
            stored_assets = self._load_assets_locked()
            return [self._to_public(asset) for asset in stored_assets]

    def save_asset(
        self,
        *,
        image_bytes: bytes,
        full_name: str,
        alter_ego: str,
        session_id: str,
        source_image_url: str,
        telegram_message_id: int | None = None,
        delivery_env: str | None = None,
    ) -> PrintArchiveAsset:
        """Create or update an archived original image."""
        normalized_name = full_name.strip()
        normalized_alter_ego = alter_ego.strip()
        caption = f"Имя: {normalized_name}\nАльтер-эго: {normalized_alter_ego}"

        with self._lock:
            assets = self._load_assets_locked()
            existing_index = self._find_asset_index(
                assets=assets,
                session_id=session_id,
                source_image_url=source_image_url,
            )

            if existing_index is not None:
                existing_asset = assets[existing_index]
                sibling_assets = [
                    asset for index, asset in enumerate(assets) if index != existing_index
                ]
                updated_asset = existing_asset.model_copy(
                    update={
                        "full_name": normalized_name,
                        "alter_ego": normalized_alter_ego,
                        "caption": caption,
                        "filename": self._build_filename(
                            full_name=normalized_name,
                            existing_assets=sibling_assets,
                        ),
                        "telegram_message_id": (
                            telegram_message_id
                            if telegram_message_id is not None
                            else existing_asset.telegram_message_id
                        ),
                        "delivery_env": delivery_env or existing_asset.delivery_env,
                    }
                )
                assets[existing_index] = updated_asset
                file_path = self._file_path(updated_asset.asset_id)
                if not file_path.exists():
                    file_path.write_bytes(image_bytes)
                self._write_assets_locked(assets)
                return self._to_public(updated_asset)

            created_at = datetime.now(timezone.utc)
            asset_id = str(uuid.uuid4())
            filename = self._build_filename(
                full_name=normalized_name,
                existing_assets=assets,
            )
            stored_asset = StoredPrintArchiveAsset(
                asset_id=asset_id,
                session_id=session_id,
                source_image_url=source_image_url,
                full_name=normalized_name,
                alter_ego=normalized_alter_ego,
                caption=caption,
                filename=filename,
                created_at=created_at,
                telegram_message_id=telegram_message_id,
                delivery_env=delivery_env,
            )
            self._file_path(asset_id).write_bytes(image_bytes)
            assets.insert(0, stored_asset)
            self._write_assets_locked(assets)
            return self._to_public(stored_asset)

    def get_asset(self, asset_id: str) -> PrintArchiveAsset | None:
        """Return one public archive item by ID."""
        with self._lock:
            for asset in self._load_assets_locked():
                if asset.asset_id == asset_id:
                    return self._to_public(asset)
        return None

    def get_asset_file_path(self, asset_id: str) -> Path | None:
        """Return the stored PNG path if the archive entry exists."""
        with self._lock:
            for asset in self._load_assets_locked():
                if asset.asset_id == asset_id:
                    file_path = self._file_path(asset_id)
                    return file_path if file_path.exists() else None
        return None

    def build_zip_bytes(self) -> bytes:
        """Build a ZIP archive with all PNG files and a CSV manifest."""
        with self._lock:
            assets = self._load_assets_locked()
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
                for asset in assets:
                    file_path = self._file_path(asset.asset_id)
                    if file_path.exists():
                        archive.write(file_path, arcname=asset.filename)
                archive.writestr("manifest.csv", self._build_manifest_csv_bytes(assets))
            return buffer.getvalue()

    def _ensure_directories(self) -> None:
        self._files_path.mkdir(parents=True, exist_ok=True)

    def _load_assets_locked(self) -> list[StoredPrintArchiveAsset]:
        if not self._index_path.exists():
            return []

        raw_payload = json.loads(self._index_path.read_text(encoding="utf-8"))
        assets = [
            StoredPrintArchiveAsset.model_validate(item)
            for item in raw_payload
            if self._file_path(str(item.get("asset_id", ""))).exists()
        ]
        assets.sort(key=lambda item: item.created_at, reverse=True)
        return assets

    def _write_assets_locked(self, assets: list[StoredPrintArchiveAsset]) -> None:
        payload = [asset.model_dump(mode="json") for asset in assets]
        temp_path = self._index_path.with_suffix(".tmp")
        temp_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp_path.replace(self._index_path)

    def _file_path(self, asset_id: str) -> Path:
        return self._files_path / f"{asset_id}.png"

    def _build_filename(
        self,
        *,
        full_name: str,
        existing_assets: list[StoredPrintArchiveAsset],
    ) -> str:
        safe_name = re.sub(r'[\\/:*?"<>|]+', " ", full_name, flags=re.UNICODE)
        safe_name = re.sub(r"\s+", " ", safe_name, flags=re.UNICODE).strip()
        stem = safe_name.rstrip(". ") or "photocard"

        candidate = f"{stem}.png"
        existing_filenames = {asset.filename for asset in existing_assets}
        if candidate not in existing_filenames:
            return candidate

        duplicate_index = 2
        while True:
            candidate = f"{stem} ({duplicate_index}).png"
            if candidate not in existing_filenames:
                return candidate
            duplicate_index += 1

    def _build_manifest_csv_bytes(self, assets: list[StoredPrintArchiveAsset]) -> bytes:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "asset_id",
                "filename",
                "created_at",
                "full_name",
                "alter_ego",
                "caption",
                "telegram_message_id",
                "delivery_env",
            ]
        )
        for asset in assets:
            writer.writerow(
                [
                    asset.asset_id,
                    asset.filename,
                    asset.created_at.isoformat(),
                    asset.full_name,
                    asset.alter_ego,
                    asset.caption,
                    asset.telegram_message_id or "",
                    asset.delivery_env or "",
                ]
            )
        return output.getvalue().encode("utf-8-sig")

    def _find_asset_index(
        self,
        *,
        assets: list[StoredPrintArchiveAsset],
        session_id: str,
        source_image_url: str,
    ) -> int | None:
        for index, asset in enumerate(assets):
            if asset.session_id == session_id and asset.source_image_url == source_image_url:
                return index
        return None

    def _to_public(self, asset: StoredPrintArchiveAsset) -> PrintArchiveAsset:
        return PrintArchiveAsset.model_validate(asset.model_dump())
