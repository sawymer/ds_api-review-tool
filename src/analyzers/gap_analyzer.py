"""
Gap analyzer - compares routes, documentation, and UI configuration.

Identifies discrepancies between what's implemented, documented, and
exposed to users.
"""

from dataclasses import dataclass, field
from typing import Optional

from ..models.endpoint import ParsedEndpoint, DocumentedEndpoint
from ..models.scope import ScopeGroup


@dataclass
class Gap:
    """A single identified gap or issue."""
    severity: str  # "High", "Medium", "Low"
    category: str  # "missing_ui", "undocumented", "scope_mismatch", etc.
    title: str
    details: str
    recommendation: str = ""
    affected_endpoints: list[str] = field(default_factory=list)


@dataclass
class GapReport:
    """Complete gap analysis report."""
    total_endpoints: int = 0
    documented_endpoints: int = 0
    ui_accessible_scopes: int = 0
    api_scopes: int = 0
    critical_gaps: list[Gap] = field(default_factory=list)
    warnings: list[Gap] = field(default_factory=list)
    info: list[Gap] = field(default_factory=list)

    @property
    def has_critical_gaps(self) -> bool:
        return len(self.critical_gaps) > 0


def analyze_gaps(
    parsed_endpoints: list[ParsedEndpoint],
    documented_endpoints: list[DocumentedEndpoint],
    ui_scope_groups: list[ScopeGroup],
    api_scopes: set[str],
) -> GapReport:
    """
    Analyze gaps between routes, documentation, and UI.

    Args:
        parsed_endpoints: Endpoints from routes file
        documented_endpoints: Endpoints from OpenAPI spec
        ui_scope_groups: Scope groups from Angular UI
        api_scopes: All scopes defined in API (from ApiKey model)

    Returns:
        GapReport with all identified issues
    """
    report = GapReport(total_endpoints=len(parsed_endpoints))

    # Build lookup sets
    documented_paths = {e.endpoint_id for e in documented_endpoints}
    ui_scopes = set()
    for group in ui_scope_groups:
        ui_scopes.update(group.scopes)

    route_scopes = set()
    for endpoint in parsed_endpoints:
        route_scopes.update(endpoint.scopes)

    report.documented_endpoints = len(documented_endpoints)
    report.ui_accessible_scopes = len(ui_scopes)
    report.api_scopes = len(api_scopes)

    # Check 1: Routes without documentation
    undocumented = []
    for endpoint in parsed_endpoints:
        if endpoint.endpoint_id not in documented_paths:
            undocumented.append(endpoint)

    if undocumented:
        report.warnings.append(Gap(
            severity="Medium",
            category="undocumented",
            title="Undocumented Endpoints",
            details=f"{len(undocumented)} endpoints have no OpenAPI documentation",
            recommendation="Add OpenAPI annotations to these controllers",
            affected_endpoints=[e.endpoint_id for e in undocumented],
        ))

    # Check 2: API scopes not in UI
    missing_from_ui = api_scopes - ui_scopes
    if missing_from_ui:
        # Group by resource
        missing_resources = set()
        for scope in missing_from_ui:
            resource = scope.split(":")[0]
            missing_resources.add(resource)

        for resource in missing_resources:
            resource_scopes = [s for s in missing_from_ui if s.startswith(resource)]
            report.critical_gaps.append(Gap(
                severity="High",
                category="missing_ui",
                title=f"'{resource}' scope missing from UI",
                details=f"API has scopes {resource_scopes} but UI doesn't expose them",
                recommendation=f"Add {resource} to scopeGroups in developer-settings.component.ts",
            ))

    # Check 3: UI scopes without API endpoints
    ui_only_scopes = ui_scopes - route_scopes - api_scopes
    # Note: This might include scopes that exist but aren't used in routes
    # e.g., invoices:write in UI but no write endpoints

    # Check 4: Scope mismatch - UI shows write but API has no write endpoints
    for group in ui_scope_groups:
        if group.write_scope and not group.read_only:
            # Check if any endpoints use this write scope
            has_write_endpoints = any(
                group.write_scope in e.scopes for e in parsed_endpoints
            )
            if not has_write_endpoints:
                report.warnings.append(Gap(
                    severity="Low",
                    category="scope_mismatch",
                    title=f"UI shows '{group.write_scope}' but no endpoints use it",
                    details=f"The UI allows users to grant {group.write_scope} but there are no API endpoints requiring this scope",
                    recommendation=f"Either remove {group.write_scope} from UI or add write endpoints for {group.resource}",
                ))

    # Check 5: Partial CRUD - resources with read but no write (when write scope exists)
    resources_with_read_only = set()
    for endpoint in parsed_endpoints:
        resource = endpoint.resource_group
        if endpoint.scopes:
            scope = endpoint.scopes[0]
            if ":read" in scope and resource:
                # Check if there are write endpoints for this resource
                has_write = any(
                    e.resource_group == resource and e.requires_write_scope
                    for e in parsed_endpoints
                )
                if not has_write:
                    resources_with_read_only.add(resource)

    # This is informational, not necessarily a gap
    if resources_with_read_only:
        report.info.append(Gap(
            severity="Info",
            category="read_only_resources",
            title="Read-only API resources",
            details=f"These resources only have read endpoints: {', '.join(sorted(resources_with_read_only))}",
            recommendation="Intentional for V1 - document this limitation",
        ))

    return report


def compare_endpoint_lists(
    routes: list[ParsedEndpoint],
    docs: list[DocumentedEndpoint],
) -> tuple[list[ParsedEndpoint], list[DocumentedEndpoint]]:
    """
    Compare routes and documentation to find mismatches.

    Returns:
        Tuple of (routes_not_documented, docs_not_in_routes)
    """
    route_ids = {e.endpoint_id for e in routes}
    doc_ids = {e.endpoint_id for e in docs}

    routes_not_documented = [e for e in routes if e.endpoint_id not in doc_ids]
    docs_not_in_routes = [e for e in docs if e.endpoint_id not in route_ids]

    return routes_not_documented, docs_not_in_routes
