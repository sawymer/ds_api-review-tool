"""
Console output for API analysis results.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..models.endpoint import ParsedEndpoint
from ..analyzers.gap_analyzer import GapReport
from ..analyzers.scope_analyzer import ScopeReport


console = Console()


def print_summary(
    endpoints: list[ParsedEndpoint],
    gap_report: GapReport,
    scope_report: ScopeReport,
) -> None:
    """
    Print a summary of the analysis to the console.

    Args:
        endpoints: Parsed endpoints
        gap_report: Gap analysis results
        scope_report: Scope analysis results
    """
    # Summary panel
    summary = f"""
[bold]Total Endpoints:[/bold] {len(endpoints)}
[bold]Documented:[/bold] {gap_report.documented_endpoints}
[bold]Total Scopes:[/bold] {scope_report.total_scopes}
[bold]Scopes in UI:[/bold] {scope_report.scopes_in_ui}
[bold]Critical Gaps:[/bold] {len(gap_report.critical_gaps)}
[bold]Warnings:[/bold] {len(gap_report.warnings)}
"""
    console.print(Panel(summary.strip(), title="API Analysis Summary", border_style="blue"))

    # Critical gaps
    if gap_report.critical_gaps:
        console.print()
        console.print("[bold red]Critical Gaps:[/bold red]")
        for gap in gap_report.critical_gaps:
            console.print(f"  [red]![/red] {gap.title}")
            console.print(f"     {gap.details}")

    # Warnings
    if gap_report.warnings:
        console.print()
        console.print("[bold yellow]Warnings:[/bold yellow]")
        for gap in gap_report.warnings:
            console.print(f"  [yellow]![/yellow] {gap.title}")

    # Scopes table
    if scope_report.missing_from_ui:
        console.print()
        console.print("[bold]Scopes Missing from UI:[/bold]")
        for scope in scope_report.missing_from_ui:
            console.print(f"  - {scope}")


def print_endpoints_table(endpoints: list[ParsedEndpoint], documented_ids: set[str]) -> None:
    """Print a table of all endpoints."""
    table = Table(title="API Endpoints")

    table.add_column("Method", style="cyan")
    table.add_column("Path", style="green")
    table.add_column("Scope", style="yellow")
    table.add_column("Documented", style="magenta")

    for ep in sorted(endpoints, key=lambda x: (x.resource_group, x.path)):
        scope = ep.scopes[0] if ep.scopes else "-"
        documented = "[green]Yes[/green]" if ep.endpoint_id in documented_ids else "[red]No[/red]"
        table.add_row(ep.method, ep.full_path, scope, documented)

    console.print(table)


def print_resource_summary(endpoints: list[ParsedEndpoint]) -> None:
    """Print a summary by resource."""
    by_resource: dict[str, int] = {}
    for ep in endpoints:
        resource = ep.resource_group or "root"
        by_resource[resource] = by_resource.get(resource, 0) + 1

    table = Table(title="Endpoints by Resource")
    table.add_column("Resource", style="cyan")
    table.add_column("Count", style="green", justify="right")

    for resource in sorted(by_resource.keys()):
        table.add_row(resource, str(by_resource[resource]))

    console.print(table)
