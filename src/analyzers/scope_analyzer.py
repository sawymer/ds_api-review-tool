"""
Scope analyzer - analyzes API scopes across routes, model, and UI.
"""

from dataclasses import dataclass, field

from ..models.endpoint import ParsedEndpoint
from ..models.scope import Scope, ScopeGroup


@dataclass
class ScopeUsage:
    """Usage information for a single scope."""
    scope: str
    resource: str
    permission: str
    endpoint_count: int = 0
    endpoints: list[str] = field(default_factory=list)
    in_api_model: bool = False
    in_ui_config: bool = False
    in_routes: bool = False


@dataclass
class ScopeReport:
    """Complete scope analysis report."""
    total_scopes: int = 0
    scopes_in_api: int = 0
    scopes_in_ui: int = 0
    scopes_in_routes: int = 0
    scope_usage: list[ScopeUsage] = field(default_factory=list)
    missing_from_ui: list[str] = field(default_factory=list)
    missing_from_routes: list[str] = field(default_factory=list)


def analyze_scopes(
    parsed_endpoints: list[ParsedEndpoint],
    ui_scope_groups: list[ScopeGroup],
    api_scopes: set[str],
) -> ScopeReport:
    """
    Analyze scope usage across the system.

    Args:
        parsed_endpoints: Endpoints from routes file
        ui_scope_groups: Scope groups from Angular UI
        api_scopes: All scopes defined in API (from ApiKey model)

    Returns:
        ScopeReport with detailed scope analysis
    """
    report = ScopeReport()

    # Collect scopes from each source
    route_scopes: dict[str, list[str]] = {}  # scope -> list of endpoints
    for endpoint in parsed_endpoints:
        for scope in endpoint.scopes:
            if scope not in route_scopes:
                route_scopes[scope] = []
            route_scopes[scope].append(endpoint.endpoint_id)

    ui_scopes = set()
    for group in ui_scope_groups:
        ui_scopes.update(group.scopes)

    # All scopes across all sources
    all_scopes = api_scopes | set(route_scopes.keys()) | ui_scopes

    report.total_scopes = len(all_scopes)
    report.scopes_in_api = len(api_scopes)
    report.scopes_in_ui = len(ui_scopes)
    report.scopes_in_routes = len(route_scopes)

    # Build usage report for each scope
    for scope in sorted(all_scopes):
        parsed = Scope.from_string(scope)
        usage = ScopeUsage(
            scope=scope,
            resource=parsed.resource,
            permission=parsed.permission,
            in_api_model=scope in api_scopes,
            in_ui_config=scope in ui_scopes,
            in_routes=scope in route_scopes,
            endpoint_count=len(route_scopes.get(scope, [])),
            endpoints=route_scopes.get(scope, []),
        )
        report.scope_usage.append(usage)

        # Track gaps
        if scope in api_scopes and scope not in ui_scopes:
            report.missing_from_ui.append(scope)
        if scope in api_scopes and scope not in route_scopes:
            report.missing_from_routes.append(scope)

    return report


def get_resource_capabilities(
    parsed_endpoints: list[ParsedEndpoint],
) -> dict[str, dict[str, bool]]:
    """
    Get CRUD capabilities for each resource.

    Returns:
        Dict mapping resource to capabilities:
        {
            "units": {"list": True, "show": True, "create": True, "update": True, "delete": True},
            "invoices": {"list": True, "show": True, "create": False, ...},
        }
    """
    capabilities: dict[str, dict[str, bool]] = {}

    for endpoint in parsed_endpoints:
        resource = endpoint.resource_group
        if not resource:
            continue

        if resource not in capabilities:
            capabilities[resource] = {
                "list": False,
                "show": False,
                "create": False,
                "update": False,
                "delete": False,
            }

        # Map actions to capabilities
        action_map = {
            "index": "list",
            "show": "show",
            "store": "create",
            "update": "update",
            "destroy": "delete",
        }

        if endpoint.action in action_map:
            capabilities[resource][action_map[endpoint.action]] = True

    return capabilities
