"""
Parser for Laravel route files (routes/api/v1.php).

Extracts all route definitions including methods, paths, controllers,
actions, and middleware (especially scopes).
"""

import re
from pathlib import Path

from ..models.endpoint import ParsedEndpoint


def parse_laravel_routes(routes_file: Path) -> list[ParsedEndpoint]:
    """
    Parse a Laravel routes file and extract all endpoint definitions.

    Args:
        routes_file: Path to the routes file (e.g., routes/api/v1.php)

    Returns:
        List of ParsedEndpoint objects
    """
    content = routes_file.read_text()
    endpoints = []

    # First, find all prefix groups and their content
    # Track current prefix for context
    current_prefix = ""

    # Split by route definitions - each Route::method starts a new route
    # Handle multi-line routes by joining lines until we hit a semicolon

    lines = content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]
        line_num = i + 1

        # Check for prefix group
        prefix_match = re.search(r"Route::prefix\(['\"]([^'\"]+)['\"]\)", line)
        if prefix_match:
            current_prefix = prefix_match.group(1)

        # Check for group closing
        if line.strip() == "});" and current_prefix:
            current_prefix = ""

        # Check for route definition start
        route_match = re.search(r"Route::(get|post|patch|put|delete)\s*\(", line, re.IGNORECASE)
        if route_match:
            # Collect the full route definition (may span multiple lines)
            route_block = line
            j = i + 1

            # Keep reading until we hit a line ending with semicolon
            while j < len(lines) and not route_block.rstrip().endswith(';'):
                route_block += '\n' + lines[j]
                j += 1

            # Parse this route block
            endpoint = _parse_route_block(route_block, line_num, current_prefix)
            if endpoint:
                endpoints.append(endpoint)

            # Move to line after the route block
            i = j
            continue

        i += 1

    return endpoints


def _parse_route_block(block: str, line_num: int, current_prefix: str) -> ParsedEndpoint | None:
    """Parse a complete route definition block (may span multiple lines)."""

    # Normalize whitespace for easier parsing
    normalized = ' '.join(block.split())

    # Extract method
    method_match = re.search(r"Route::(get|post|patch|put|delete)", normalized, re.IGNORECASE)
    if not method_match:
        return None
    method = method_match.group(1).upper()

    # Extract path - first string after the method call
    path_match = re.search(r"Route::\w+\s*\(\s*['\"]([^'\"]+)['\"]", normalized)
    if not path_match:
        return None
    path = path_match.group(1)

    # Extract controller and action
    controller_match = re.search(r"\[\s*(\w+)::class\s*,\s*['\"](\w+)['\"]", normalized)
    if not controller_match:
        return None
    controller = controller_match.group(1)
    action = controller_match.group(2)

    # Extract scope from middleware
    scopes = []
    scope_match = re.search(r"->middleware\s*\(\s*['\"]api\.scope:([^'\"]+)['\"]", normalized)
    if scope_match:
        scopes = [scope_match.group(1)]

    # Extract all middleware
    middleware = []
    middleware_matches = re.findall(r"->middleware\s*\(\s*['\"]([^'\"]+)['\"]", normalized)
    middleware = middleware_matches

    # Build normalized path (without /api/v1 prefix, for OpenAPI comparison)
    if current_prefix:
        normalized_path = f"/{current_prefix}/{path}".replace("//", "/")
    else:
        normalized_path = f"/{path}" if not path.startswith("/") else path

    # Clean trailing slashes (but keep root /)
    if normalized_path.endswith("/") and len(normalized_path) > 1:
        normalized_path = normalized_path.rstrip("/")

    # Build full path (with /api/v1 prefix)
    full_path = f"/api/v1{normalized_path}"

    return ParsedEndpoint(
        method=method,
        path=normalized_path,
        full_path=full_path,
        controller=controller,
        action=action,
        scopes=scopes,
        middleware=middleware,
        line_number=line_num,
        resource_group=current_prefix,
    )


def get_all_scopes_from_routes(endpoints: list[ParsedEndpoint]) -> set[str]:
    """Extract all unique scopes from parsed endpoints."""
    scopes = set()
    for endpoint in endpoints:
        scopes.update(endpoint.scopes)
    return scopes


def group_endpoints_by_resource(
    endpoints: list[ParsedEndpoint]
) -> dict[str, list[ParsedEndpoint]]:
    """Group endpoints by their resource (prefix)."""
    groups: dict[str, list[ParsedEndpoint]] = {}
    for endpoint in endpoints:
        resource = endpoint.resource_group or "root"
        if resource not in groups:
            groups[resource] = []
        groups[resource].append(endpoint)
    return groups
