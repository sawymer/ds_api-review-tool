"""
CLI entry point for the DS API Review Tool.

Usage:
    api-catalog analyze --routes <path> --output <dir>
    api-catalog catalog --routes <path> --output <dir>
    api-catalog gaps --routes <path> --output <dir>
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from .parsers import parse_laravel_routes, parse_openapi_spec, parse_angular_scopes
from .analyzers import analyze_gaps, analyze_scopes
from .reporters import (
    generate_catalog_report,
    generate_gap_report,
    generate_csv_summary,
    print_summary,
)

app = typer.Typer(
    name="api-catalog",
    help="DoorSpot API catalog and testing tool",
    add_completion=False,
)
console = Console()


# Default paths for rf-api and rf-ui
DEFAULT_ROUTES = Path.home() / "dev" / "rf-api" / "routes" / "api" / "v1.php"
DEFAULT_OPENAPI = Path.home() / "dev" / "rf-api" / "storage" / "api-docs" / "api-docs.json"
DEFAULT_UI_CONFIG = (
    Path.home() / "dev" / "rf-ui" / "src" / "app" / "client-layout" / "settings"
    / "developer-settings" / "developer-settings.component.ts"
)
DEFAULT_OUTPUT = Path.home() / "dev" / "AI_prod_notes" / "rf-api" / "api-catalog"

# Known API scopes from ApiKey.php model
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


@app.command()
def analyze(
    routes: Path = typer.Option(
        DEFAULT_ROUTES,
        "--routes",
        "-r",
        help="Path to Laravel routes file (routes/api/v1.php)",
    ),
    openapi: Optional[Path] = typer.Option(
        None,
        "--openapi",
        "-o",
        help="Path to OpenAPI spec (JSON or YAML)",
    ),
    ui_config: Optional[Path] = typer.Option(
        None,
        "--ui-config",
        "-u",
        help="Path to Angular developer-settings.component.ts",
    ),
    output: Path = typer.Option(
        DEFAULT_OUTPUT,
        "--output",
        "-O",
        help="Output directory for reports",
    ),
) -> None:
    """
    Run full analysis: parse routes, compare with docs, generate all reports.
    """
    console.print("[bold blue]DS API Review Tool[/bold blue]")
    console.print()

    # Use defaults if not provided
    openapi = openapi or DEFAULT_OPENAPI
    ui_config = ui_config or DEFAULT_UI_CONFIG

    # Parse sources
    console.print(f"[dim]Parsing routes from:[/dim] {routes}")
    if not routes.exists():
        console.print(f"[red]Error:[/red] Routes file not found: {routes}")
        raise typer.Exit(1)

    endpoints = parse_laravel_routes(routes)
    console.print(f"  Found [green]{len(endpoints)}[/green] endpoints")

    # Parse OpenAPI spec (optional)
    documented_endpoints = []
    if openapi.exists():
        console.print(f"[dim]Parsing OpenAPI spec from:[/dim] {openapi}")
        documented_endpoints = parse_openapi_spec(openapi)
        console.print(f"  Found [green]{len(documented_endpoints)}[/green] documented endpoints")
    else:
        console.print(f"[yellow]Warning:[/yellow] OpenAPI spec not found: {openapi}")
        console.print("  Run: sail artisan l5-swagger:generate")

    # Parse UI config (optional)
    ui_scope_groups = []
    if ui_config.exists():
        console.print(f"[dim]Parsing UI config from:[/dim] {ui_config}")
        ui_scope_groups = parse_angular_scopes(ui_config)
        console.print(f"  Found [green]{len(ui_scope_groups)}[/green] scope groups")
    else:
        console.print(f"[yellow]Warning:[/yellow] UI config not found: {ui_config}")

    # Analyze
    console.print()
    console.print("[bold]Analyzing...[/bold]")

    gap_report = analyze_gaps(endpoints, documented_endpoints, ui_scope_groups, API_SCOPES)
    scope_report = analyze_scopes(endpoints, ui_scope_groups, API_SCOPES)

    # Print summary to console
    print_summary(endpoints, gap_report, scope_report)

    # Generate reports
    console.print()
    console.print("[bold]Generating reports...[/bold]")

    output.mkdir(parents=True, exist_ok=True)

    catalog_file = generate_catalog_report(endpoints, documented_endpoints, scope_report, output)
    console.print(f"  [green]Catalog:[/green] {catalog_file}")

    gap_file = generate_gap_report(gap_report, scope_report, output)
    console.print(f"  [green]Gaps:[/green] {gap_file}")

    ui_scopes = set()
    for group in ui_scope_groups:
        ui_scopes.update(group.scopes)

    csv_file = generate_csv_summary(endpoints, documented_endpoints, ui_scopes, output)
    console.print(f"  [green]CSV:[/green] {csv_file}")

    console.print()
    console.print("[bold green]Analysis complete![/bold green]")


@app.command()
def catalog(
    routes: Path = typer.Option(
        DEFAULT_ROUTES,
        "--routes",
        "-r",
        help="Path to Laravel routes file",
    ),
    output: Path = typer.Option(
        DEFAULT_OUTPUT,
        "--output",
        "-O",
        help="Output directory for report",
    ),
) -> None:
    """
    Generate only the API catalog report (no gap analysis).
    """
    console.print("[bold blue]Generating API Catalog[/bold blue]")

    if not routes.exists():
        console.print(f"[red]Error:[/red] Routes file not found: {routes}")
        raise typer.Exit(1)

    endpoints = parse_laravel_routes(routes)
    console.print(f"Found [green]{len(endpoints)}[/green] endpoints")

    # Try to load OpenAPI spec
    documented_endpoints = []
    if DEFAULT_OPENAPI.exists():
        documented_endpoints = parse_openapi_spec(DEFAULT_OPENAPI)

    ui_scope_groups = []
    if DEFAULT_UI_CONFIG.exists():
        ui_scope_groups = parse_angular_scopes(DEFAULT_UI_CONFIG)

    scope_report = analyze_scopes(endpoints, ui_scope_groups, API_SCOPES)

    output.mkdir(parents=True, exist_ok=True)
    catalog_file = generate_catalog_report(endpoints, documented_endpoints, scope_report, output)

    console.print(f"[green]Generated:[/green] {catalog_file}")


@app.command()
def gaps(
    routes: Path = typer.Option(
        DEFAULT_ROUTES,
        "--routes",
        "-r",
        help="Path to Laravel routes file",
    ),
    output: Path = typer.Option(
        DEFAULT_OUTPUT,
        "--output",
        "-O",
        help="Output directory for report",
    ),
) -> None:
    """
    Generate only the gap analysis report.
    """
    console.print("[bold blue]Generating Gap Analysis[/bold blue]")

    if not routes.exists():
        console.print(f"[red]Error:[/red] Routes file not found: {routes}")
        raise typer.Exit(1)

    endpoints = parse_laravel_routes(routes)
    console.print(f"Found [green]{len(endpoints)}[/green] endpoints")

    # Load other sources
    documented_endpoints = []
    if DEFAULT_OPENAPI.exists():
        documented_endpoints = parse_openapi_spec(DEFAULT_OPENAPI)

    ui_scope_groups = []
    if DEFAULT_UI_CONFIG.exists():
        ui_scope_groups = parse_angular_scopes(DEFAULT_UI_CONFIG)

    gap_report = analyze_gaps(endpoints, documented_endpoints, ui_scope_groups, API_SCOPES)
    scope_report = analyze_scopes(endpoints, ui_scope_groups, API_SCOPES)

    output.mkdir(parents=True, exist_ok=True)
    gap_file = generate_gap_report(gap_report, scope_report, output)

    console.print(f"[green]Generated:[/green] {gap_file}")


@app.command()
def list_endpoints(
    routes: Path = typer.Option(
        DEFAULT_ROUTES,
        "--routes",
        "-r",
        help="Path to Laravel routes file",
    ),
) -> None:
    """
    List all endpoints from the routes file.
    """
    if not routes.exists():
        console.print(f"[red]Error:[/red] Routes file not found: {routes}")
        raise typer.Exit(1)

    endpoints = parse_laravel_routes(routes)

    for ep in sorted(endpoints, key=lambda x: (x.resource_group, x.path, x.method)):
        scope = ep.scopes[0] if ep.scopes else "-"
        console.print(f"{ep.method:7} {ep.full_path:50} [{scope}]")


@app.command()
def version() -> None:
    """Show version information."""
    console.print("DS API Review Tool v1.0.0")


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
