"""
Markdown report generators for API catalog and gap analysis.
"""

from datetime import datetime
from pathlib import Path

from ..models.endpoint import ParsedEndpoint, DocumentedEndpoint
from ..models.scope import ScopeGroup
from ..analyzers.gap_analyzer import GapReport
from ..analyzers.scope_analyzer import ScopeReport


def generate_catalog_report(
    endpoints: list[ParsedEndpoint],
    documented_endpoints: list[DocumentedEndpoint],
    scope_report: ScopeReport,
    output_path: Path,
) -> Path:
    """
    Generate the main API catalog report in Markdown.

    Args:
        endpoints: Parsed endpoints from routes
        documented_endpoints: Endpoints from OpenAPI spec
        scope_report: Scope analysis report
        output_path: Directory to write the report

    Returns:
        Path to the generated report file
    """
    documented_ids = {e.endpoint_id for e in documented_endpoints}

    # Group endpoints by resource
    by_resource: dict[str, list[ParsedEndpoint]] = {}
    for ep in endpoints:
        resource = ep.resource_group or "root"
        if resource not in by_resource:
            by_resource[resource] = []
        by_resource[resource].append(ep)

    lines = [
        "# DoorSpot External API Catalog",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        "",
        f"- **Total Endpoints:** {len(endpoints)}",
        f"- **Resources:** {len(by_resource)}",
        f"- **Documented:** {len(documented_endpoints)} ({_pct(len(documented_endpoints), len(endpoints))})",
        f"- **Total Scopes:** {scope_report.total_scopes}",
        f"- **Scopes in UI:** {scope_report.scopes_in_ui}",
        "",
        "---",
        "",
        "## Endpoints by Resource",
        "",
    ]

    for resource in sorted(by_resource.keys()):
        resource_endpoints = by_resource[resource]
        lines.append(f"### {resource.title().replace('-', ' ').replace('_', ' ')} ({len(resource_endpoints)} endpoints)")
        lines.append("")
        lines.append("| Method | Path | Scope | Documented |")
        lines.append("|--------|------|-------|------------|")

        for ep in sorted(resource_endpoints, key=lambda x: (x.path, x.method)):
            scope = ep.scopes[0] if ep.scopes else "-"
            documented = "Yes" if ep.endpoint_id in documented_ids else "No"
            lines.append(f"| {ep.method} | {ep.full_path} | {scope} | {documented} |")

        lines.append("")

    # Scope reference
    lines.extend([
        "---",
        "",
        "## Scope Reference",
        "",
        "| Scope | Endpoints | In UI |",
        "|-------|-----------|-------|",
    ])

    for usage in scope_report.scope_usage:
        in_ui = "Yes" if usage.in_ui_config else "**No**"
        lines.append(f"| {usage.scope} | {usage.endpoint_count} | {in_ui} |")

    lines.append("")

    # Write to file
    output_file = output_path / f"catalog-{datetime.now().strftime('%Y-%m-%d')}.md"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("\n".join(lines))

    return output_file


def generate_gap_report(
    gap_report: GapReport,
    scope_report: ScopeReport,
    output_path: Path,
) -> Path:
    """
    Generate the gap analysis report in Markdown.

    Args:
        gap_report: Gap analysis results
        scope_report: Scope analysis results
        output_path: Directory to write the report

    Returns:
        Path to the generated report file
    """
    lines = [
        "# API Gap Analysis Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        "",
        f"- **Total Endpoints:** {gap_report.total_endpoints}",
        f"- **Documented:** {gap_report.documented_endpoints}",
        f"- **Critical Gaps:** {len(gap_report.critical_gaps)}",
        f"- **Warnings:** {len(gap_report.warnings)}",
        "",
    ]

    # Critical gaps
    if gap_report.critical_gaps:
        lines.extend([
            "---",
            "",
            "## Critical Gaps",
            "",
        ])
        for i, gap in enumerate(gap_report.critical_gaps, 1):
            lines.extend([
                f"### {i}. {gap.title}",
                "",
                f"**Severity:** {gap.severity}",
                f"**Category:** {gap.category}",
                "",
                gap.details,
                "",
            ])
            if gap.recommendation:
                lines.append(f"**Recommendation:** {gap.recommendation}")
                lines.append("")
            if gap.affected_endpoints:
                lines.append("**Affected Endpoints:**")
                for ep in gap.affected_endpoints[:10]:  # Limit to first 10
                    lines.append(f"- `{ep}`")
                if len(gap.affected_endpoints) > 10:
                    lines.append(f"- ... and {len(gap.affected_endpoints) - 10} more")
                lines.append("")

    # Warnings
    if gap_report.warnings:
        lines.extend([
            "---",
            "",
            "## Warnings",
            "",
        ])
        for i, gap in enumerate(gap_report.warnings, 1):
            lines.extend([
                f"### {i}. {gap.title}",
                "",
                f"**Severity:** {gap.severity}",
                "",
                gap.details,
                "",
            ])
            if gap.recommendation:
                lines.append(f"**Recommendation:** {gap.recommendation}")
                lines.append("")

    # Info
    if gap_report.info:
        lines.extend([
            "---",
            "",
            "## Information",
            "",
        ])
        for gap in gap_report.info:
            lines.extend([
                f"### {gap.title}",
                "",
                gap.details,
                "",
            ])

    # Scope gaps
    if scope_report.missing_from_ui:
        lines.extend([
            "---",
            "",
            "## Scopes Missing from UI",
            "",
            "These scopes are defined in the API but not exposed in the UI:",
            "",
        ])
        for scope in scope_report.missing_from_ui:
            lines.append(f"- `{scope}`")
        lines.append("")

    # Recommendations summary
    lines.extend([
        "---",
        "",
        "## Recommendations Summary",
        "",
        "1. Add missing scopes to UI configuration",
        "2. Add OpenAPI documentation to undocumented endpoints",
        "3. Review scope mismatches between UI and API capabilities",
        "",
    ])

    # Write to file
    output_file = output_path / f"gaps-{datetime.now().strftime('%Y-%m-%d')}.md"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("\n".join(lines))

    return output_file


def _pct(part: int, total: int) -> str:
    """Calculate percentage string."""
    if total == 0:
        return "0%"
    return f"{(part / total) * 100:.0f}%"
