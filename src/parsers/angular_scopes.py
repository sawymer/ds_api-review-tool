"""
Parser for Angular UI scope configuration.

Extracts scope groups from the developer settings component.
"""

import re
from pathlib import Path

from ..models.scope import ScopeGroup


def parse_angular_scopes(component_file: Path) -> list[ScopeGroup]:
    """
    Parse the Angular developer settings component to extract scope groups.

    Args:
        component_file: Path to developer-settings.component.ts

    Returns:
        List of ScopeGroup objects
    """
    if not component_file.exists():
        return []

    content = component_file.read_text()

    # Find the scopeGroups array
    scope_groups = []

    # Pattern to match scope group objects in the array
    # Looking for patterns like: { resource: 'Units', scopes: [...], readOnly: false }
    group_pattern = r"\{\s*resource:\s*['\"]([^'\"]+)['\"].*?scopes:\s*\[(.*?)\].*?(?:readOnly:\s*(true|false))?\s*\}"

    matches = re.findall(group_pattern, content, re.DOTALL)

    for match in matches:
        resource = match[0]
        scopes_str = match[1]
        read_only = match[2] == "true" if match[2] else False

        # Parse the scopes array
        scope_values = re.findall(r"value:\s*['\"]([^'\"]+)['\"]", scopes_str)

        read_scope = ""
        write_scope = ""

        for scope in scope_values:
            if ":read" in scope:
                read_scope = scope
            elif ":write" in scope:
                write_scope = scope

        # Derive resource key from scopes
        resource_key = ""
        if read_scope:
            resource_key = read_scope.replace(":read", "")
        elif write_scope:
            resource_key = write_scope.replace(":write", "")

        scope_groups.append(ScopeGroup(
            resource=resource,
            resource_key=resource_key,
            read_scope=read_scope,
            write_scope=write_scope,
            read_only=read_only,
        ))

    return scope_groups


def get_ui_available_scopes(scope_groups: list[ScopeGroup]) -> set[str]:
    """Get all scopes available in the UI."""
    scopes = set()
    for group in scope_groups:
        scopes.update(group.scopes)
    return scopes


def get_ui_resources(scope_groups: list[ScopeGroup]) -> set[str]:
    """Get all resource keys available in the UI."""
    return {g.resource_key for g in scope_groups}
