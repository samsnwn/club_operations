"""The invoice folder: the shared Google Drive folder the owner uploads
invoices to (README §Phase 0.5, owner answer #2 revised 2026-11-23).

Read-only by design: a service account the owner shares the folder with lists
it and downloads new files. Files stay in the folder as the owner's archive;
nothing here ever writes to Drive. Every run lists the whole folder (about 20
invoices a month), so there is no cursor: a file is new when its MD5 is not on
any invoice yet, which also skips duplicate uploads without downloading them.
"""

import json
import logging
import time
from collections.abc import Callable
from pathlib import Path

import httpx
from google.auth import crypt, jwt

from app.ingestion.capture import CapturedFile

log = logging.getLogger(__name__)

TOKEN_URL = "https://oauth2.googleapis.com/token"
FILES_URL = "https://www.googleapis.com/drive/v3/files"
SCOPE = "https://www.googleapis.com/auth/drive.readonly"
ACCEPTED_TYPES = frozenset({"application/pdf", "image/jpeg", "image/png", "image/webp"})
TIMEOUT_SECONDS = 60.0


class DriveUnavailable(Exception):
    """Google Drive could not be reached or failed on its side."""


class DriveAccessRefused(Exception):
    """Credentials or folder sharing are wrong; a person has to fix them."""


class DriveSource:
    name = "drive"

    def __init__(
        self,
        folder_id: str,
        credentials_file: str | Path,
        *,
        max_attachment_bytes: int,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.folder_id = folder_id
        self.credentials_file = Path(credentials_file)
        self.max_attachment_bytes = max_attachment_bytes
        self._transport = transport  # test seam

    def poll(self, is_known: Callable[[str], bool]) -> list[CapturedFile]:
        """Download every acceptable file in the folder whose MD5 is not
        known yet. Listing failures raise; a single failed download is
        logged and retried on the next run."""
        with httpx.Client(timeout=TIMEOUT_SECONDS, transport=self._transport) as client:
            client.headers["Authorization"] = f"Bearer {self._access_token(client)}"
            captures = []
            for item in self._list(client):
                if not self._acceptable(item) or is_known(item["md5Checksum"]):
                    continue
                try:
                    content = self._download(client, item["id"])
                except (DriveUnavailable, DriveAccessRefused):
                    log.exception("Drive download failed: %s", item.get("name"))
                    continue
                captures.append(
                    CapturedFile(
                        source=self.name,
                        filename=item["name"],
                        content=content,
                        source_ref=item["id"],
                    )
                )
            return captures

    def _access_token(self, client: httpx.Client) -> str:
        """OAuth token for the service account (JWT bearer grant)."""
        try:
            info = json.loads(self.credentials_file.read_text())
            signer = crypt.RSASigner.from_service_account_info(info)
            email = info["client_email"]
        except (OSError, ValueError, KeyError) as exc:
            raise DriveAccessRefused(
                "Google Drive credentials file is missing or invalid"
            ) from exc
        now = int(time.time())
        assertion = jwt.encode(
            signer,
            {
                "iss": email,
                "scope": SCOPE,
                "aud": TOKEN_URL,
                "iat": now,
                "exp": now + 3600,
            },
        )
        response = self._send(
            client,
            "POST",
            TOKEN_URL,
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": assertion.decode("ascii"),
            },
        )
        return response.json()["access_token"]

    def _list(self, client: httpx.Client) -> list[dict]:
        folder = self.folder_id.replace("\\", "\\\\").replace("'", "\\'")
        params = {
            "q": f"'{folder}' in parents and trashed = false",
            "fields": "nextPageToken, files(id, name, mimeType, size, md5Checksum)",
            "pageSize": "100",
            "supportsAllDrives": "true",
            "includeItemsFromAllDrives": "true",
        }
        items: list[dict] = []
        while True:
            body = self._send(client, "GET", FILES_URL, params=params).json()
            items.extend(body.get("files", []))
            if not body.get("nextPageToken"):
                return items
            params["pageToken"] = body["nextPageToken"]

    def _acceptable(self, item: dict) -> bool:
        """Top-level PDF/image files within the size limit (subfolders and
        Google-native documents have other MIME types and no MD5)."""
        name = item.get("name", "?")
        if item.get("mimeType") not in ACCEPTED_TYPES or not item.get("md5Checksum"):
            log.info("Drive file skipped (type %s): %s", item.get("mimeType"), name)
            return False
        if int(item.get("size", 0)) > self.max_attachment_bytes:
            log.warning("Drive file skipped (over the size limit): %s", name)
            return False
        return True

    def _download(self, client: httpx.Client, file_id: str) -> bytes:
        response = self._send(
            client,
            "GET",
            f"{FILES_URL}/{file_id}",
            params={"alt": "media", "supportsAllDrives": "true"},
        )
        return response.content

    @staticmethod
    def _send(client: httpx.Client, method: str, url: str, **kwargs) -> httpx.Response:
        try:
            response = client.request(method, url, **kwargs)
        except httpx.RequestError as exc:
            raise DriveUnavailable("Google Drive unavailable") from exc
        if response.status_code in (400, 401, 403, 404):
            log.error("Drive refused %s %s: %s", method, url, response.text[:500])
            raise DriveAccessRefused(
                "Google Drive access refused — check that the invoice folder is "
                "shared with the service account"
            )
        if response.status_code >= 400:
            raise DriveUnavailable("Google Drive unavailable")
        return response
