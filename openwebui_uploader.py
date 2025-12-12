"""
Open WebUI Knowledge Uploader - Core Library Module

This module provides a Python client for interacting with Open WebUI's REST API
to manage knowledge collections and upload files.
"""

import os
import logging
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
import requests


logger = logging.getLogger(__name__)


def is_allowed_file(file_path: str) -> bool:
    """
    Check if a file should be processed based on its extension and filename.

    Args:
        file_path: Path to the file to check

    Returns:
        True if file should be processed, False if it should be skipped
    """
    path = Path(file_path)
    filename = path.name.lower()

    # Skip system files
    if filename in [".ds_store", "thumbs.db"]:
        return False

    # Get file extension (case-insensitive)
    extension = path.suffix.lower()

    # Allowed extensions: md, txt, pdf, doc, docx
    allowed_extensions = {".md", ".txt", ".pdf", ".doc", ".docx"}

    return extension in allowed_extensions


class OpenWebUIClient:
    """Client for interacting with Open WebUI REST API."""

    def __init__(self, api_endpoint: str, api_key: str):
        """
        Initialize the Open WebUI client.

        Args:
            api_endpoint: Base URL of the Open WebUI API (e.g., 'http://localhost:3000')
            api_key: API key for authentication
        """
        self.api_endpoint = api_endpoint.rstrip("/")
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        # Upload headers match the captured browser drag-and-drop request pattern.
        # See CAPTURED_REQUEST_DETAILS.md for reference.
        # Note: Content-Type is NOT set here - requests library automatically sets
        # multipart/form-data with boundary when files parameter is used.
        self.upload_headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        }
        self._knowledge_endpoint = None  # Will be discovered on first successful call

    def _make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> Optional[requests.Response]:
        """
        Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path (e.g., '/api/v1/knowledge')
            **kwargs: Additional arguments to pass to requests

        Returns:
            Response object or None if request failed
        """
        url = f"{self.api_endpoint}{endpoint}"
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {method} {url} - {e}")
            return None

    def list_knowledge_collections(self) -> List[Dict[str, Any]]:
        """
        List all knowledge collections.

        Returns:
            List of knowledge collection dictionaries, or empty list on error
        """
        # Try different endpoint variations
        endpoints_to_try = [
            "/api/v1/workspace/knowledge",
            "/api/v1/knowledges",
            "/api/v1/knowledge",
        ]

        for endpoint in endpoints_to_try:
            response = self._make_request("GET", endpoint, headers=self.headers)

            if response:
                # Check if response is HTML (wrong endpoint)
                content_type = response.headers.get("Content-Type", "").lower()
                if "text/html" in content_type:
                    continue  # Try next endpoint

                try:
                    result = response.json()
                    # Store successful endpoint for future use
                    self._knowledge_endpoint = endpoint
                    return result
                except ValueError:
                    continue  # Try next endpoint

        logger.error(
            "Failed to list knowledge collections: all endpoint variations returned non-JSON responses"
        )
        return []

    def get_knowledge_collection_id(self, name: str) -> Optional[str]:
        """
        Get the ID of a knowledge collection by name.

        Args:
            name: Name of the knowledge collection

        Returns:
            Collection ID if found, None otherwise
        """
        collections = self.list_knowledge_collections()
        for collection in collections:
            if collection.get("name") == name:
                return collection.get("id")
        return None

    def create_knowledge_collection(
        self, name: str, description: str = ""
    ) -> Optional[str]:
        """
        Create a new knowledge collection.

        Args:
            name: Name of the knowledge collection
            description: Optional description for the collection

        Returns:
            Collection ID if successful, None otherwise
        """
        # Determine base endpoint - use discovered one or try variations
        if self._knowledge_endpoint:
            base_endpoint = self._knowledge_endpoint
        else:
            base_endpoint = "/api/v1/workspace/knowledge"  # Try workspace first

        endpoints_to_try = [
            f"{base_endpoint}/create",
            "/api/v1/workspace/knowledge/create",
            "/api/v1/knowledges/create",
            "/api/v1/knowledge/create",
        ]

        payload = {"name": name, "description": description}

        for endpoint in endpoints_to_try:
            response = self._make_request(
                "POST", endpoint, headers=self.headers, json=payload
            )
            if response:
                # Check if response is HTML (wrong endpoint)
                content_type = response.headers.get("Content-Type", "").lower()
                if "text/html" in content_type:
                    continue  # Try next endpoint

                try:
                    result = response.json()
                    collection_id = result.get("id")
                    logger.info(
                        f"Created knowledge collection '{name}' with ID: {collection_id}"
                    )
                    # Store successful endpoint base for future use
                    if not self._knowledge_endpoint:
                        self._knowledge_endpoint = endpoint.replace("/create", "")
                    return collection_id
                except ValueError:
                    continue  # Try next endpoint
        logger.error(
            "Failed to create knowledge collection: all endpoint variations failed"
        )
        return None

    def upload_file(self, file_path: str) -> Optional[str]:
        """
        Upload a file to Open WebUI using POST /api/v1/files/.

        This method implements the exact request pattern captured from browser
        drag-and-drop uploads. See CAPTURED_REQUEST_DETAILS.md for complete
        request/response documentation.

        Request pattern:
        - Endpoint: POST /api/v1/files/
        - Headers: Authorization (Bearer token), Accept: application/json
        - Payload: multipart/form-data with form field named "file"
        - Response: JSON with id, user_id, filename, data.status, meta fields

        Args:
            file_path: Path to the file to upload

        Returns:
            File ID if successful, None otherwise
        """
        if not os.path.isfile(file_path):
            logger.error(f"File not found: {file_path}")
            return None

        # Check if file is allowed (skip system files and non-text formats)
        if not is_allowed_file(file_path):
            logger.debug(f"Skipping file (not allowed): {file_path}")
            return None

        try:
            with open(file_path, "rb") as file:
                # Prepare multipart/form-data payload matching browser upload pattern.
                # Form field MUST be named "file" (not "files" or any other name).
                # Tuple format: (filename, file_object) - requests library handles Content-Type.
                files = {"file": (os.path.basename(file_path), file)}
                # POST to /api/v1/files/ endpoint with upload headers.
                # Headers include Authorization (Bearer token) and Accept: application/json.
                response = self._make_request(
                    "POST", "/api/v1/files/", headers=self.upload_headers, files=files
                )
                if response:
                    try:
                        # Parse JSON response matching captured structure:
                        # {id, user_id, filename, data: {status}, meta: {name, size, ...}}
                        result = response.json()
                        file_id = result.get("id")
                        filename = result.get("filename") or result.get("meta", {}).get(
                            "name"
                        )
                        file_size = result.get("meta", {}).get("size")
                        status = result.get("data", {}).get("status", "unknown")

                        logger.info(
                            f"Uploaded file '{file_path}' with ID: {file_id} "
                            f"(filename: {filename}, size: {file_size}, status: {status})"
                        )
                        return file_id
                    except ValueError as e:
                        logger.error(
                            f"Failed to parse response as JSON: {e}. "
                            f"Response status: {response.status_code}, "
                            f"Response text: {response.text[:200]}"
                        )
                        return None
                else:
                    logger.error(
                        f"Upload request failed for '{file_path}'. "
                        f"Check API endpoint and authentication."
                    )
                    return None
        except IOError as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None
        return None

    def add_file_to_knowledge(
        self,
        knowledge_id: str,
        file_id: str,
        retries: int = 3,
        retry_delay: float = 5.0,
    ) -> bool:
        """
        Associate an uploaded file with a knowledge collection.

        Args:
            knowledge_id: ID of the knowledge collection
            file_id: ID of the uploaded file
            retries: Number of retry attempts (default: 3)
            retry_delay: Delay between retries in seconds (default: 1.0)

        Returns:
            True if successful, False otherwise
        """
        # API requires just file_id - metadatas field (even as empty list or None) causes errors
        # The UI sends only {"file_id": "..."} without metadatas field
        # Server-side ChromaDB insert fails if metadatas contains None values
        # Retry logic helps handle transient server-side processing issues
        payload = {"file_id": file_id}

        for attempt in range(retries):
            response = self._make_request(
                "POST",
                f"/api/v1/knowledge/{knowledge_id}/file/add",
                headers=self.headers,
                json=payload,
            )

            if response:
                logger.info(
                    f"Added file {file_id} to knowledge collection {knowledge_id}"
                )
                return True

            # If not the last attempt, wait before retrying
            if attempt < retries - 1:
                logger.debug(
                    f"Retry {attempt + 1}/{retries} failed, waiting {retry_delay}s before retry..."
                )
                time.sleep(retry_delay)

        logger.error(
            f"Failed to add file {file_id} to knowledge collection {knowledge_id} after {retries} attempts"
        )
        return False

    def upload_files_to_knowledge(
        self,
        knowledge_name: str,
        file_paths: List[str],
        create_if_missing: bool = False,
        description: str = "",
    ) -> Dict[str, Any]:
        """
        High-level method to upload multiple files to a knowledge collection.

        Args:
            knowledge_name: Name of the knowledge collection
            file_paths: List of file paths to upload
            create_if_missing: If True, create the collection if it doesn't exist
            description: Optional description for the collection (if creating)

        Returns:
            Dictionary with 'success', 'failed', 'total' counts and 'errors' list
        """
        # Get or create knowledge collection
        knowledge_id = self.get_knowledge_collection_id(knowledge_name)

        if not knowledge_id:
            if create_if_missing:
                knowledge_id = self.create_knowledge_collection(
                    knowledge_name, description
                )
                if not knowledge_id:
                    return {
                        "success": 0,
                        "failed": len(file_paths),
                        "total": len(file_paths),
                        "errors": [
                            f"Failed to create knowledge collection '{knowledge_name}'"
                        ],
                    }
            else:
                return {
                    "success": 0,
                    "failed": len(file_paths),
                    "total": len(file_paths),
                    "errors": [f"Knowledge collection '{knowledge_name}' not found"],
                }

        # Upload files
        results = {"success": 0, "failed": 0, "total": len(file_paths), "errors": []}

        for file_path in file_paths:
            file_id = self.upload_file(file_path)
            if file_id:
                # Small delay to allow server to process the uploaded file
                # This helps avoid race conditions with server-side file processing
                time.sleep(0.5)

                if self.add_file_to_knowledge(knowledge_id, file_id):
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(
                        f"Failed to add {file_path} to knowledge collection"
                    )
            else:
                results["failed"] += 1
                results["errors"].append(f"Failed to upload {file_path}")

        return results
