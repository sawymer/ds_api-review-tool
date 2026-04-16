"""
Parser for OpenAPI/Swagger specification files.

Extracts all documented endpoints from the OpenAPI spec.
"""

import json
from pathlib import Path
from typing import Optional

from ..models.endpoint import DocumentedEndpoint


def parse_openapi_spec(
    spec_file: Path,
    include_internal: bool = False,
) -> list[DocumentedEndpoint]:
    """
    Parse an OpenAPI spec file and extract all documented endpoints.

    Args:
        spec_file: Path to the OpenAPI spec (JSON or YAML)
        include_internal: If False (default), exclude endpoints marked with x-internal

    Returns:
        List of DocumentedEndpoint objects
    """
    if not spec_file.exists():
        return []

    content = spec_file.read_text()

    # Handle JSON format
    if spec_file.suffix == ".json":
        spec = json.loads(content)
    else:
        # Handle YAML format
        import yaml
        spec = yaml.safe_load(content)

    endpoints = []
    paths = spec.get("paths", {})

    for path, path_item in paths.items():
        for method in ["get", "post", "put", "patch", "delete"]:
            if method in path_item:
                operation = path_item[method]
                is_internal = bool(operation.get("x-internal", False))

                # Skip internal endpoints unless explicitly requested
                if is_internal and not include_internal:
                    continue

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
                    is_internal=is_internal,
                )
                endpoints.append(endpoint)

    return endpoints


def get_spec_info(spec_file: Path) -> Optional[dict]:
    """Get basic info from the OpenAPI spec."""
    if not spec_file.exists():
        return None

    content = spec_file.read_text()

    if spec_file.suffix == ".json":
        spec = json.loads(content)
    else:
        import yaml
        spec = yaml.safe_load(content)

    return spec.get("info", {})


def get_documented_paths(endpoints: list[DocumentedEndpoint]) -> set[str]:
    """Get all unique endpoint IDs from documented endpoints."""
    return {e.endpoint_id for e in endpoints}
