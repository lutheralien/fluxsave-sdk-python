from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import requests


def _resolve_error_code(status: int, message: str) -> str:
    m = message.lower()
    if status == 413 and "storage limit" in m:
        return "STORAGE_LIMIT"
    if status == 413:
        return "FILE_TOO_LARGE"
    if status == 415:
        return "MIME_TYPE_NOT_ALLOWED"
    if status == 402:
        return "SUBSCRIPTION_INACTIVE"
    if status == 403 and "compression" in m:
        return "COMPRESSION_NOT_ALLOWED"
    if status == 403 and "folder" in m:
        return "FOLDER_COUNT_LIMIT"
    if status == 403 and ("file" in m or "maximum" in m):
        return "FILE_COUNT_LIMIT"
    if status == 403 and "email" in m:
        return "EMAIL_NOT_VERIFIED"
    if status == 400 and "already registered" in m:
        return "EMAIL_ALREADY_REGISTERED"
    if status == 400 and ("invalid email or password" in m or "invalid credentials" in m):
        return "INVALID_CREDENTIALS"
    if status == 400 and "otp" in m:
        return "INVALID_OTP"
    if status == 401:
        return "UNAUTHORIZED"
    if status == 404:
        return "NOT_FOUND"
    return "UNKNOWN"


@dataclass
class FluxsaveError(Exception):
    """
    Raised when the Fluxsave API returns an error response.

    Attributes:
        message:    Human-readable error description from the API.
        status:     HTTP status code.
        code:       Machine-readable error code (e.g. ``"FILE_TOO_LARGE"``).
        data:       Raw response payload, if any.

    Error codes:
        FILE_TOO_LARGE           – 413: file exceeds plan's maxFileSizeBytes
        STORAGE_LIMIT            – 413: total storage quota exceeded
        FILE_COUNT_LIMIT         – 403: plan's maxFilesCount reached
        MIME_TYPE_NOT_ALLOWED    – 415: file type blocked by plan
        COMPRESSION_NOT_ALLOWED  – 403: compression level not permitted by plan
        SUBSCRIPTION_INACTIVE    – 402: user subscription is not active
        FOLDER_COUNT_LIMIT       – 403: plan's maxFoldersCount reached
        EMAIL_ALREADY_REGISTERED – 400: duplicate email on register
        EMAIL_NOT_VERIFIED       – 403: login before verifying email
        INVALID_CREDENTIALS      – 400: wrong email or password
        INVALID_OTP              – 400: bad/expired verification code
        UNAUTHORIZED             – 401
        NOT_FOUND                – 404
        UNKNOWN                  – anything else
    """

    message: str
    status: int
    data: Optional[Any] = None
    code: str = field(init=False)

    def __post_init__(self) -> None:
        self.code = _resolve_error_code(self.status, self.message)

    def __str__(self) -> str:
        return f"{self.status} [{self.code}]: {self.message}"


class FluxsaveClient:
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        timeout: int = 30,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.api_secret = api_secret
        self.timeout = timeout

    def set_auth(self, api_key: str, api_secret: str) -> None:
        self.api_key = api_key
        self.api_secret = api_secret

    def _headers(self) -> Dict[str, str]:
        if not self.api_key or not self.api_secret:
            raise FluxsaveError("API key and secret are required", 401)
        return {
            "x-api-key": self.api_key,
            "x-api-secret": self.api_secret,
        }

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self.base_url}{path}"
        response = requests.request(method, url, headers=self._headers(), timeout=self.timeout, **kwargs)
        try:
            payload = response.json()
        except ValueError:
            payload = response.text

        if not response.ok:
            message = payload.get("message") if isinstance(payload, dict) else response.reason
            raise FluxsaveError(message or response.reason, response.status_code, payload)

        return payload

    def upload_file(self, file_path: str, name: Optional[str] = None, compression: Optional[str] = None, folder_id: Optional[str] = None) -> Any:
        files = {"file": open(file_path, "rb")}
        data: Dict[str, Any] = {}
        if name:
            data["name"] = name
        if compression is not None:
            data["compression"] = compression
        if folder_id is not None:
            data["folderId"] = folder_id
        try:
            return self._request("POST", "/api/v1/files/upload", files=files, data=data)
        finally:
            files["file"].close()

    def upload_files(self, file_paths: list[str], name: Optional[str] = None, compression: Optional[str] = None, folder_id: Optional[str] = None) -> Any:
        files = [("files", open(path, "rb")) for path in file_paths]
        data: Dict[str, Any] = {}
        if name:
            data["name"] = name
        if compression is not None:
            data["compression"] = compression
        if folder_id is not None:
            data["folderId"] = folder_id
        try:
            return self._request("POST", "/api/v1/files/upload", files=files, data=data)
        finally:
            for _, fh in files:
                fh.close()

    def list_files(self, folder_id: Optional[str] = None) -> Any:
        path = f"/api/v1/files?folderId={folder_id}" if folder_id else "/api/v1/files"
        return self._request("GET", path)

    def list_folders(self) -> Any:
        return self._request("GET", "/api/v1/folders")

    def create_folder(self, name: str, parent_id: Optional[str] = None) -> Any:
        data: Dict[str, Any] = {"name": name}
        if parent_id is not None:
            data["parentId"] = parent_id
        return self._request("POST", "/api/v1/folders", json=data)

    def rename_folder(self, folder_id: str, name: str) -> Any:
        return self._request("PATCH", f"/api/v1/folders/{folder_id}", json={"name": name})

    def delete_folder(self, folder_id: str) -> Any:
        return self._request("DELETE", f"/api/v1/folders/{folder_id}")

    def get_file_metadata(self, file_id: str) -> Any:
        return self._request("GET", f"/api/v1/files/metadata/{file_id}")

    def update_file(
        self,
        file_id: str,
        file_path: str,
        name: Optional[str] = None,
        compression: Optional[str] = None,
    ) -> Any:
        files = {"file": open(file_path, "rb")}
        data: Dict[str, Any] = {}
        if name:
            data["name"] = name
        if compression is not None:
            data["compression"] = compression
        try:
            return self._request("PUT", f"/api/v1/files/{file_id}", files=files, data=data)
        finally:
            files["file"].close()

    def delete_file(self, file_id: str) -> Any:
        return self._request("DELETE", f"/api/v1/files/{file_id}")

    def get_metrics(self) -> Any:
        return self._request("GET", "/api/v1/metrics")

    def build_file_url(self, file_id: str, **options: Any) -> str:
        url = f"{self.base_url}/api/v1/files/{file_id}"
        if options:
            query = "&".join(f"{k}={v}" for k, v in options.items())
            return f"{url}?{query}"
        return url
