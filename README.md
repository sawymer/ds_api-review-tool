# DS API Review Tool

A standalone Python CLI tool for cataloging and testing the DoorSpot external API.

## Overview

This tool analyzes the DoorSpot external API by:
1. **Parsing Laravel routes** (`routes/api/v1.php`) to extract all endpoints
2. **Parsing OpenAPI specs** (if available) to check documentation coverage
3. **Parsing Angular UI config** to verify scope availability in the UI
4. **Generating reports** identifying gaps and discrepancies

## Installation

```bash
cd ~/dev/ds_api-review-tool
pip install -e .
```

Or with a virtual environment:
```bash
cd ~/dev/ds_api-review-tool
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

### Full Analysis

Run a complete analysis with all reports:

```bash
api-catalog analyze
```

This uses default paths:
- Routes: `~/dev/rf-api/routes/api/v1.php`
- OpenAPI: `~/dev/rf-api/storage/api-docs/api-docs.json`
- UI Config: `~/dev/rf-ui/.../developer-settings.component.ts`
- Output: `~/dev/AI_prod_notes/rf-api/api-catalog/`

### Custom Paths

```bash
api-catalog analyze \
  --routes /path/to/routes/api/v1.php \
  --openapi /path/to/api-docs.json \
  --ui-config /path/to/developer-settings.component.ts \
  --output /path/to/output/
```

### Individual Reports

```bash
# Generate only the catalog
api-catalog catalog

# Generate only gap analysis
api-catalog gaps

# List all endpoints
api-catalog list-endpoints
```

## Generated Reports

### `catalog-YYYY-MM-DD.md`
Complete endpoint inventory organized by resource, showing:
- HTTP method and path
- Required scope
- Documentation status

### `gaps-YYYY-MM-DD.md`
Gap analysis report identifying:
- Scopes missing from UI
- Undocumented endpoints
- Scope mismatches
- Recommendations

### `api-review-summary.csv`
Spreadsheet summary with columns:
- Endpoint (method + path)
- API Scope Required
- Documented (Yes/No)
- UI Access Available (Yes/No)
- Functional Status
- Last Tested Date
- Notes

## Prerequisites

For full analysis, generate the OpenAPI spec first:

```bash
cd ~/dev/rf-api
./vendor/bin/sail artisan l5-swagger:generate
```

## Project Structure

```
ds_api-review-tool/
├── src/
│   ├── cli.py              # CLI entry point
│   ├── parsers/            # File parsers
│   │   ├── laravel_routes.py
│   │   ├── openapi_spec.py
│   │   └── angular_scopes.py
│   ├── analyzers/          # Analysis logic
│   │   ├── gap_analyzer.py
│   │   └── scope_analyzer.py
│   ├── reporters/          # Report generators
│   │   ├── markdown_report.py
│   │   ├── csv_report.py
│   │   └── console_report.py
│   ├── testers/            # Live API testing (Phase 2)
│   └── models/             # Data models
└── tests/                  # Unit tests
```

## Phase 2: Live Testing (Future)

The tool is designed to support live API testing in Phase 2:
- Authenticate with API keys
- Call each endpoint
- Validate responses against schemas
- Generate test results

## Related

- **YouTrack:** RF-2002
- **API Design Doc:** `~/dev/rf-api/docs/external-api-design.md`
- **API Routes:** `~/dev/rf-api/routes/api/v1.php`
