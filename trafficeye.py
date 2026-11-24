"""
Minimal Python client for the TrafficEye REST API.

Detects vehicles, reads license plates (ANPR/ALPR) and recognizes vehicle
make, model, color and category from a single image.

Get your API key at https://trafficeye.ai/user/licenses
"""
import json
import mimetypes
import os
import time
from typing import List, Optional
from urllib.parse import unquote, urlparse

import requests

DEFAULT_API_URL = "https://api.trafficeye.ai/v1/"
DEFAULT_TASKS = ["DETECTION", "OCR", "MMR"]
RETRY_STATUS_CODES = (502, 504, 520, 521)


class TrafficEyeError(Exception):
    """Raised when a TrafficEye API request fails."""


def is_valid_url(value: str) -> bool:
    """Return True if the value is an absolute URL (e.g. https://...)."""
    parsed = urlparse(unquote(value))
    return bool(parsed.scheme) and bool(parsed.netloc)


class TrafficEyeClient:
    """Client for the TrafficEye REST API."""

    def __init__(self, api_key: str, server_url: str = DEFAULT_API_URL, timeout: int = 60):
        """
        :param api_key: Your API key, available at https://trafficeye.ai/user/licenses
        :param server_url: Base address of the REST API.
        :param timeout: Request timeout in seconds.
        """
        if not api_key:
            raise ValueError("API key is required.")

        self.api_key = api_key
        self.server_url = server_url if server_url.endswith("/") else server_url + "/"
        self.timeout = timeout
        self.session = requests.Session()

    def _reset_session(self) -> None:
        """Open a fresh HTTP session after a connection failure."""
        self.session.close()
        self.session = requests.Session()

    def info(self) -> dict:
        """Query API status information, including remaining credit."""
        try:
            response = self.session.get(
                self.server_url + "info",
                headers={"apikey": self.api_key},
                timeout=self.timeout,
            )
        except requests.exceptions.RequestException as e:
            self._reset_session()
            raise TrafficEyeError(f"Connection error: {e}") from e

        if response.status_code != 200:
            raise TrafficEyeError(f"{response.status_code}: {response.text}")
        return response.json()

    def _load_image(self, image: str):
        """Return (file_name, content) for a local path or an image URL."""
        if os.path.isfile(image):
            with open(image, "rb") as f:
                return os.path.basename(image), f.read()

        if is_valid_url(image):
            try:
                response = requests.get(image, timeout=self.timeout)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                raise TrafficEyeError(f"Failed to download image: {e}") from e
            name = os.path.basename(urlparse(image).path) or "image"
            return name, response.content

        raise TrafficEyeError(f"Image not found and not a valid URL: {image}")

    def recognition(
        self,
        image: str,
        tasks: Optional[List[str]] = None,
        save_image: bool = False,
        save_plate_text: bool = True,
        ocr_module_id: int = 801,
        retry_attempts: int = 1,
    ) -> dict:
        """
        Analyze an image.

        :param image: Path to a local image file or an image URL.
        :param tasks: Any of "DETECTION", "OCR", "MMR". Defaults to all three.
        :param save_image: If True, the server stores the image in request history.
        :param save_plate_text: If False, plate text is not stored in request history.
        :param ocr_module_id: OCR module to use. 801 is Global OCR.
        :param retry_attempts: Retries on connection errors and 502/504/520/521 responses.
        :return: Parsed JSON response.
        :raises TrafficEyeError: If the request fails.
        """
        file_name, content = self._load_image(image)

        if content.startswith(b"\xff\xd8\xff"):
            content_type = "image/jpeg"
        else:
            content_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"

        request_data = {
            "saveImage": save_image,
            "savePlateText": save_plate_text,
            "tasks": tasks or list(DEFAULT_TASKS),
            "ocrModuleId": ocr_module_id,
        }

        last_error = "Unknown error"
        for _ in range(retry_attempts + 1):
            try:
                response = self.session.post(
                    self.server_url + "recognition",
                    data={"request": json.dumps(request_data)},
                    files={"file": (file_name, content, content_type)},
                    headers={"apikey": self.api_key},
                    timeout=self.timeout,
                )
            except requests.exceptions.RequestException as e:
                last_error = f"Connection error: {e}"
                self._reset_session()
                time.sleep(1)
                continue

            if response.status_code in RETRY_STATUS_CODES:
                last_error = f"{response.status_code}: {response.text}"
                self._reset_session()
                time.sleep(1)
                continue

            if response.status_code != 200:
                raise TrafficEyeError(f"{response.status_code}: {response.text}")

            return response.json()

        raise TrafficEyeError(last_error)
