#!/usr/bin/env python3
"""
Standalone analysis runner - no external dependencies required.
Run with: python3 run_analysis.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.parsers.laravel_routes import parse_laravel_routes, group_endpoints_by_resource
from src.parsers.openapi_spec import parse_openapi_spec
from src.parsers.angular_scopes import parse_angular_scopes, get_ui_available_scopes
from src.analyzers.gap_analyzer import analyze_gaps
from src.analyzers.scope_analyzer import analyze_scopes
from datetime import datetime
import csv


# Paths
ROUTES_FILE = Path.home() / "dev" / "rf-api" / "routes" / "api" / "v1.php"
OPENAPI_FILE = Path.home() / "dev" / "rf-api" / "storage" / "api-docs" / "api-docs.json"
UI_CONFIG = Path.home() / "dev" / "rf-ui" / "src" / "app" / "client-layout" / "settings" / "developer-settings" / "developer-settings.component.ts"
OUTPUT_DIR = Path.home() / "dev" / "AI_prod_notes" / "rf-api" / "api-catalog"

# Known API scopes from ApiKey.php
API_SCOPES = {
    "units:read", "units:write",
    "reservations:read", "reservations:write",
    "contacts:read", "contacts:write",
    "invoices:read", "invoices:write",
    "payments:read",
    "service_requests:read", "service_requests:write",
    "tenants:read", "tenants:write",
    "webhooks:read", "webhooks:write",
    "ledger_accounts:read",
    "ledger_entries:read",
    "tasks:read", "tasks:write",
    "communications:read", "communications:write",
    "sales_leads:read",
    "unit_contracts:read",
    "restrictions:read", "restrictions:write",
}


def main():
    print("=" * 60)
    print("DS API Review Tool - Analysis")
    print("=" * 60)
    print()

    # Parse routes
    print(f"Parsing routes from: {ROUTES_FILE}")
    endpoints = parse_laravel_routes(ROUTES_FILE)
    print(f"  Found {len(endpoints)} endpoints")

    # Parse OpenAPI (if exists)
    documented_endpoints = []
    if OPENAPI_FILE.exists():
        print(f"Parsing OpenAPI from: {OPENAPI_FILE}")
        documented_endpoints = parse_openapi_spec(OPENAPI_FILE)
        print(f"  Found {len(documented_endpoints)} documented endpoints")
    else:
        print(f"  [WARN] OpenAPI spec not found: {OPENAPI_FILE}")
        print("  Run: sail artisan l5-swagger:generate")

    # Parse UI config
    ui_scope_groups = []
    if UI_CONFIG.exists():
        print(f"Parsing UI config from: {UI_CONFIG}")
        ui_scope_groups = parse_angular_scopes(UI_CONFIG)
        print(f"  Found {len(ui_scope_groups)} scope groups")
    else:
        print(f"  [WARN] UI config not found: {UI_CONFIG}")

    # Analyze
    print()
    print("Analyzing...")
    gap_report = analyze_gaps(endpoints, documented_endpoints, ui_scope_groups, API_SCOPES)
    scope_report = analyze_scopes(endpoints, ui_scope_groups, API_SCOPES)

    # Print summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total Endpoints: {len(endpoints)}")
    print(f"Documented: {gap_report.documented_endpoints}")
    print(f"Total Scopes: {scope_report.total_scopes}")
    print(f"Scopes in UI: {scope_report.scopes_in_ui}")
    print(f"Critical Gaps: {len(gap_report.critical_gaps)}")
    print(f"Warnings: {len(gap_report.warnings)}")

    # Print critical gaps
    if gap_report.critical_gaps:
        print()
        print("CRITICAL GAPS:")
        for gap in gap_report.critical_gaps:
            print(f"  [!] {gap.title}")
            print(f"      {gap.details}")

    if gap_report.warnings:
        print()
        print("WARNINGS:")
        for gap in gap_report.warnings:
            print(f"  [!] {gap.title}")

    # Print scopes missing from UI
    if scope_report.missing_from_ui:
        print()
        print("SCOPES MISSING FROM UI:")
        for scope in scope_report.missing_from_ui:
            print(f"  - {scope}")

    # Generate reports
    print()
    print("Generating reports...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Generate catalog markdown
    catalog_file = generate_catalog_md(endpoints, documented_endpoints, scope_report)
    print(f"  Catalog: {catalog_file}")

    # Generate gaps markdown
    gaps_file = generate_gaps_md(gap_report, scope_report)
    print(f"  Gaps: {gaps_file}")

    # Generate CSV
    csv_file = generate_csv(endpoints, documented_endpoints, ui_scope_groups)
    print(f"  CSV: {csv_file}")

    print()
    print("Analysis complete!")


def generate_catalog_md(endpoints, documented_endpoints, scope_report):
    """Generate the catalog markdown report."""
    documented_ids = {e.endpoint_id for e in documented_endpoints}
    by_resource = group_endpoints_by_resource(endpoints)

    lines = [
        "# DoorSpot External API Catalog",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        "",
        f"- **Total Endpoints:** {len(endpoints)}",
        f"- **Resources:** {len(by_resource)}",
        f"- **Documented:** {len(documented_endpoints)}",
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
        resource_name = resource.title().replace('-', ' ').replace('_', ' ')
        lines.append(f"### {resource_name} ({len(resource_endpoints)} endpoints)")
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

    output_file = OUTPUT_DIR / f"catalog-{datetime.now().strftime('%Y-%m-%d')}.md"
    output_file.write_text("\n".join(lines))
    return output_file


def generate_gaps_md(gap_report, scope_report):
    """Generate the gaps markdown report."""
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

    if gap_report.critical_gaps:
        lines.extend(["---", "", "## Critical Gaps", ""])
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

    if gap_report.warnings:
        lines.extend(["---", "", "## Warnings", ""])
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

    output_file = OUTPUT_DIR / f"gaps-{datetime.now().strftime('%Y-%m-%d')}.md"
    output_file.write_text("\n".join(lines))
    return output_file


def generate_csv(endpoints, documented_endpoints, ui_scope_groups):
    """Generate the CSV summary."""
    documented_ids = {e.endpoint_id for e in documented_endpoints}
    ui_scopes = get_ui_available_scopes(ui_scope_groups)

    rows = []
    for ep in sorted(endpoints, key=lambda x: (x.resource_group, x.path, x.method)):
        scope = ep.scopes[0] if ep.scopes else ""
        documented = ep.endpoint_id in documented_ids
        ui_available = scope in ui_scopes if scope else True

        rows.append({
            "Endpoint": ep.endpoint_id,
            "Resource": ep.resource_group,
            "API Scope Required": scope,
            "Documented": "Yes" if documented else "No",
            "UI Access Available": "Yes" if ui_available else "No",
            "Functional Status": "Untested",
            "Last Tested Date": "",
            "Notes": "",
        })

    output_file = OUTPUT_DIR / "api-review-summary.csv"
    with open(output_file, "w", newline="") as f:
        fieldnames = [
            "Endpoint", "Resource", "API Scope Required", "Documented",
            "UI Access Available", "Functional Status", "Last Tested Date", "Notes"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return output_file


if __name__ == "__main__":
    main()
