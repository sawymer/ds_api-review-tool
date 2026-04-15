"""
CSV report generator for API review summary.
"""

import csv
from datetime import datetime
from pathlib import Path

from ..models.endpoint import ParsedEndpoint, DocumentedEndpoint
from ..models.test_result import TestResult, EndpointStatus


def generate_csv_summary(
    endpoints: list[ParsedEndpoint],
    documented_endpoints: list[DocumentedEndpoint],
    ui_scopes: set[str],
    output_path: Path,
    test_results: list[TestResult] | None = None,
) -> Path:
    """
    Generate a CSV summary of all API endpoints.

    Args:
        endpoints: Parsed endpoints from routes
        documented_endpoints: Endpoints from OpenAPI spec
        ui_scopes: Set of scopes available in UI
        output_path: Directory to write the report
        test_results: Optional test results to include status

    Returns:
        Path to the generated CSV file
    """
    documented_ids = {e.endpoint_id for e in documented_endpoints}

    # Build test results lookup
    test_lookup: dict[str, TestResult] = {}
    if test_results:
        for result in test_results:
            test_lookup[result.endpoint] = result

    rows = []
    for ep in sorted(endpoints, key=lambda x: (x.resource_group, x.path, x.method)):
        scope = ep.scopes[0] if ep.scopes else ""
        documented = ep.endpoint_id in documented_ids

        # Check if scope is in UI
        ui_available = scope in ui_scopes if scope else True

        # Get test status if available
        test_result = test_lookup.get(ep.endpoint_id)
        if test_result:
            status = test_result.status.value
            tested_date = test_result.tested_at.strftime("%Y-%m-%d") if test_result.tested_at else ""
            notes = test_result.notes
        else:
            status = EndpointStatus.UNTESTED.value
            tested_date = ""
            notes = ""

        rows.append({
            "Endpoint": ep.endpoint_id,
            "Resource": ep.resource_group,
            "API Scope Required": scope,
            "Documented": "Yes" if documented else "No",
            "UI Access Available": "Yes" if ui_available else "No",
            "Functional Status": status,
            "Last Tested Date": tested_date,
            "Notes": notes,
        })

    # Write to CSV
    output_file = output_path / "api-review-summary.csv"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", newline="") as f:
        fieldnames = [
            "Endpoint",
            "Resource",
            "API Scope Required",
            "Documented",
            "UI Access Available",
            "Functional Status",
            "Last Tested Date",
            "Notes",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return output_file


def load_existing_results(csv_path: Path) -> list[TestResult]:
    """
    Load existing test results from a CSV file.

    Args:
        csv_path: Path to existing CSV file

    Returns:
        List of TestResult objects
    """
    if not csv_path.exists():
        return []

    results = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse the endpoint to get method and path
            endpoint_parts = row["Endpoint"].split(" ", 1)
            method = endpoint_parts[0] if endpoint_parts else ""
            path = endpoint_parts[1] if len(endpoint_parts) > 1 else ""

            # Parse status
            status_str = row.get("Functional Status", "Untested")
            try:
                status = EndpointStatus(status_str)
            except ValueError:
                status = EndpointStatus.UNTESTED

            # Parse date
            date_str = row.get("Last Tested Date", "")
            tested_at = None
            if date_str:
                try:
                    tested_at = datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    pass

            result = TestResult(
                endpoint=row["Endpoint"],
                method=method,
                path=path,
                scope_required=row.get("API Scope Required", ""),
                documented=row.get("Documented", "No") == "Yes",
                ui_access_available=row.get("UI Access Available", "No") == "Yes",
                status=status,
                tested_at=tested_at,
                notes=row.get("Notes", ""),
            )
            results.append(result)

    return results
