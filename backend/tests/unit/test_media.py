"""Unit tests for upload validation and storage."""

from __future__ import annotations

from io import BytesIO

from werkzeug.datastructures import FileStorage

from app.media import MediaError, delete_media_file, resolve_media, save_post_media

# Smallest valid PNG header + IHDR chunk; enough for signature checking.
PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
    b"\x1f\x15\xc4\x89"
)


def _upload(data: bytes, filename: str) -> FileStorage:
    return FileStorage(stream=BytesIO(data), filename=filename)


def test_saves_valid_image_with_random_name(tmp_path):
    media = save_post_media(_upload(PNG_BYTES, "my photo.png"), str(tmp_path))

    assert media["type"] == "image"
    assert media["name"] == "my_photo.png"
    assert media["url"].startswith("/api/v1/media/")
    stored = media["url"].rsplit("/", 1)[-1]
    assert (tmp_path / stored).read_bytes() == PNG_BYTES
    assert resolve_media(stored, str(tmp_path)) == (tmp_path / stored, "image/png")


def test_rejects_extension_content_mismatch(tmp_path):
    try:
        save_post_media(_upload(b"not really a png", "fake.png"), str(tmp_path))
    except MediaError as exc:
        assert "does not match" in str(exc)
    else:
        raise AssertionError("renamed non-image was accepted")


def test_rejects_unsupported_extension(tmp_path):
    try:
        save_post_media(_upload(b"MZ\x90\x00", "payload.exe"), str(tmp_path))
    except MediaError as exc:
        assert "Unsupported file type" in str(exc)
    else:
        raise AssertionError("executable was accepted")


def test_resolve_rejects_path_traversal(tmp_path):
    assert resolve_media("../secret.png", str(tmp_path)) is None


def test_delete_removes_stored_file(tmp_path):
    media = save_post_media(_upload(PNG_BYTES, "photo.png"), str(tmp_path))
    stored = media["url"].rsplit("/", 1)[-1]

    delete_media_file(media, str(tmp_path))

    assert not (tmp_path / stored).exists()
