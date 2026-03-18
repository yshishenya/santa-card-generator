"""Unit tests for persistent print archive storage."""

from io import BytesIO
from zipfile import ZipFile

from src.core.print_archive import PrintArchiveStore


def test_save_asset_creates_and_updates_single_archive_entry(tmp_path) -> None:
    store = PrintArchiveStore(str(tmp_path))

    created = store.save_asset(
        image_bytes=b"\x89PNGoriginal-image",
        full_name="Jane Frost",
        alter_ego="Cyberpunk snow captain",
        session_id="session-1",
        source_image_url="generated://image-1",
    )
    updated = store.save_asset(
        image_bytes=b"\x89PNGoriginal-image",
        full_name="Jane Frost",
        alter_ego="Cyberpunk snow captain",
        session_id="session-1",
        source_image_url="generated://image-1",
        telegram_message_id=12345,
        delivery_env="staging",
    )

    assert created.asset_id == updated.asset_id
    assert created.filename == "Jane Frost.png"
    assert updated.filename == "Jane Frost.png"
    assert updated.telegram_message_id == 12345
    assert updated.delivery_env == "staging"
    assert len(store.list_assets()) == 1

    file_path = store.get_asset_file_path(created.asset_id)
    assert file_path is not None
    assert file_path.read_bytes() == b"\x89PNGoriginal-image"


def test_build_zip_contains_png_and_manifest(tmp_path) -> None:
    store = PrintArchiveStore(str(tmp_path))
    asset = store.save_asset(
        image_bytes=b"\x89PNGzip-image",
        full_name="Kate",
        alter_ego="Captain of a flying bookshop",
        session_id="session-2",
        source_image_url="generated://image-2",
        telegram_message_id=555,
        delivery_env="prod",
    )

    zip_bytes = store.build_zip_bytes()

    with ZipFile(BytesIO(zip_bytes)) as archive:
        names = archive.namelist()
        assert asset.filename in names
        assert "manifest.csv" in names

        manifest = archive.read("manifest.csv").decode("utf-8-sig")
        assert "Captain of a flying bookshop" in manifest
        assert "555" in manifest


def test_duplicate_names_receive_minimal_suffix(tmp_path) -> None:
    store = PrintArchiveStore(str(tmp_path))

    first_asset = store.save_asset(
        image_bytes=b"\x89PNGone",
        full_name="Катя",
        alter_ego="Pilot",
        session_id="session-3",
        source_image_url="generated://image-3",
    )
    second_asset = store.save_asset(
        image_bytes=b"\x89PNGtwo",
        full_name="Катя",
        alter_ego="Diver",
        session_id="session-4",
        source_image_url="generated://image-4",
    )

    assert first_asset.filename == "Катя.png"
    assert second_asset.filename == "Катя (2).png"
