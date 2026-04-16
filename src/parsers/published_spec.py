"""
Parser for fetching and parsing the published OpenAPI spec from api.doorspot.com.
"""

import json
from typing import Optional
import urllib.request
import urllib.error

from ..models.endpoint import DocumentedEndpoint

PUBLISHED_SPEC_URL = "https://api.doorspot.com/docs"


def fetch_published_spec(url: str = PUBLISHED_SPEC_URL) -> Optional[dict]:
    """
    Fetch the published OpenAPI spec from the live API.

    Args:
        url: URL to fetch the spec from

    Returns:
        Parsed JSON spec or None if fetch fails
    """
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            content = response.read().decode('utf-8')
            return json.loads(content)
    except (urllib.error.URLError, json.JSONDecodeError) as e:
        return None


def parse_published_spec(url: str = PUBLISHED_SPEC_URL) -> list[DocumentedEndpoint]:
    """
    Fetch and parse the published OpenAPI spec.

    Args:
        url: URL to fetch the spec from

    Returns:
        List of DocumentedEndpoint objects (public endpoints only)
    """
    spec = fetch_published_spec(url)
    if not spec:
        return []

    endpoints = []
    paths = spec.get("paths", {})

    for path, path_item in paths.items():
        for method in ["get", "post", "put", "patch", "delete"]:
            if method in path_item:
                operation = path_item[method]
                # Published spec should only contain public endpoints
                endpoint = DocumentedEndpoint(
                    method=method.upper(),
                    path=path,
                    operation_id=operation.get("operationId"),
                    summary=operation.get("summary"),
                    description=operation.get("description"),
                    tags=operation.get("tags", []),
                    parameters=operation.get("parameters", []),
                    request_body=operation.get("requestBody"),
                    responses=operation.get("responses", {}),
                    security=operation.get("security", []),
                    is_internal=False,
                )
                endpoints.append(endpoint)

    return endpoints
