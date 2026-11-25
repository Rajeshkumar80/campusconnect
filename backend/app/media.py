"""Media upload validation and storage for post attachments.

Files are stored under a flat directory with random names. The stored name is
the only thing persisted; the original filename is kept for display only.
"""

from __future__ import annotations

import re
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

from werkzeug.utils import secure_filename

if TYPE_CHECKING:
    from werkzeug.datastructures import FileStorage

IMAGE_MAX_BYTES = 10 * 1024 * 1024
VIDEO_MAX_BYTES = 50 * 1024 * 1024
DOCUMENT_MAX_BYTES = 20 * 1024 * 1024
IMAGE_SIZE_HINT = "up to 10 MB"
VIDEO_SIZE_HINT = "up to 50 MB"

# extension -> (kind, mime type, max bytes)
MEDIA_TYPES: dict[str, tuple[str, str, int]] = {
    ".jpg": ("image", "image/jpeg", IMAGE_MAX_BYTES),
    ".jpeg": ("image", "image/jpeg", IMAGE_MAX_BYTES),
    ".png": ("image", "image/png", IMAGE_MAX_BYTES),
    ".gif": ("image", "image/gif", IMAGE_MAX_BYTES),
    ".webp": ("image", "image/webp", IMAGE_MAX_BYTES),
    ".mp4": ("video", "video/mp4", VIDEO_MAX_BYTES),
    ".webm": ("video", "video/webm", VIDEO_MAX_BYTES),
    ".mov": ("video", "video/quicktime", VIDEO_MAX_BYTES),
    ".pdf": ("document", "application/pdf", DOCUMENT_MAX_BYTES),
    ".mp3": ("audio", "audio/mpeg", DOCUMENT_MAX_BYTES),
    ".wav": ("audio", "audio/wav", DOCUMENT_MAX_BYTES),
    ".ogg": ("audio", "audio/ogg", DOCUMENT_MAX_BYTES),
    ".m4a": ("audio", "audio/mp4", DOCUMENT_MAX_BYTES),
    ".weba": ("audio", "audio/webm", DOCUMENT_MAX_BYTES),
}

POST_KINDS = {"image", "video"}
MESSAGE_KINDS = {"image", "document", "audio"}

_STORED_NAME = re.compile(
    r"^[0-9a-f]{32}\.(?:" + "|".join(ext[1:] for ext in MEDIA_TYPES) + r")$"
)


class MediaError(ValueError):
    """Raised when an uploaded file is not an accepted image or video."""


def _signature_matches(head: bytes, ext: str) -> bool:
    """Check the file header so a renamed executable cannot pass as media."""
    if ext in {".jpg", ".jpeg"}:
        return head.startswith(b"\xff\xd8\xff")
    if ext == ".png":
        return head.startswith(b"\x89PNG\r\n\x1a\n")
    if ext == ".gif":
        return head[:6] in {b"GIF87a", b"GIF89a"}
    if ext in {".webp"}:
        return head[:4] == b"RIFF" and head[8:12] == b"WEBP"
    if ext in {".mp4", ".mov", ".m4a"}:
        return head[4:8] == b"ftyp"
    if ext in {".webm", ".weba"}:
        return head[:4] == b"\x1a\x45\xdf\xa3"
    if ext == ".pdf":
        return head.startswith(b"%PDF")
    if ext == ".mp3":
        return head[:3] == b"ID3" or head[:1] == b"\xff"
    if ext == ".wav":
        return head[:4] == b"RIFF" and head[8:12] == b"WAVE"
    if ext == ".ogg":
        return head[:4] == b"OggS"
    return False


def _save_media(
    file: FileStorage,
    upload_folder: str,
    allowed_kinds: set[str],
    type_hint: str,
) -> dict[str, object]:
    """Validate and store one upload restricted to the given media kinds."""
    original_name = secure_filename(file.filename or "")
    ext = Path(original_name).suffix.lower()
    spec = MEDIA_TYPES.get(ext)
    if not spec or spec[0] not in allowed_kinds:
        raise MediaError(f"Unsupported file type. Use {type_hint}.")
    kind, mime, max_bytes = spec

    stream = file.stream
    stream.seek(0, 2)
    size = stream.tell()
    stream.seek(0)
    if size <= 0:
        raise MediaError("The selected file is empty.")
    if size > max_bytes:
        if kind == "image":
            hint = IMAGE_SIZE_HINT
        elif kind == "video":
            hint = VIDEO_SIZE_HINT
        else:
            hint = "up to 20 MB"
        raise MediaError(f"{kind.title()} is too large ({hint}).")

    head = stream.read(16)
    stream.seek(0)
    if not _signature_matches(head, ext):
        raise MediaError("The file content does not match its extension.")

    folder = Path(upload_folder)
    folder.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}{ext}"
    file.save(folder / stored_name)

    return {
        "url": f"/api/v1/media/{stored_name}",
        "type": kind,
        "mime": mime,
        "name": original_name[:120] or f"attachment{ext}",
        "size": size,
    }


def save_post_media(file: FileStorage, upload_folder: str) -> dict[str, object]:
    """Validate and store a post attachment (image or video)."""
    return _save_media(
        file, upload_folder, POST_KINDS, "JPG, PNG, GIF, WebP, MP4, WebM or MOV"
    )


def save_message_media(file: FileStorage, upload_folder: str) -> dict[str, object]:
    """Validate and store a message attachment (image, PDF or voice note)."""
    return _save_media(
        file,
        upload_folder,
        MESSAGE_KINDS,
        "JPG, PNG, GIF, WebP, PDF, MP3, WAV, OGG, M4A or voice recording",
    )


def resolve_media(filename: str, upload_folder: str) -> tuple[Path, str] | None:
    """Map a stored filename to an on-disk path and safe MIME type."""
    if not _STORED_NAME.fullmatch(filename):
        return None
    path = Path(upload_folder) / filename
    if not path.is_file():
        return None
    ext = path.suffix.lower()
    spec = MEDIA_TYPES.get(ext)
    if not spec:
        return None
    return path, spec[1]


def delete_media_file(media: dict | None, upload_folder: str) -> None:
    """Best-effort removal of a post's stored attachment."""
    if not media:
        return
    filename = str(media.get("url", "")).rsplit("/", 1)[-1]
    if not _STORED_NAME.fullmatch(filename):
        return
    with suppress(OSError):
        (Path(upload_folder) / filename).unlink(missing_ok=True)
