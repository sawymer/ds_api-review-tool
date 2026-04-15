# DS API Review Tool

## Project Overview

A standalone Python CLI tool for cataloging and testing the DoorSpot external API.

**Related Ticket:** RF-2002 (DS public API - Review and Complete)

## Quick Start

```bash
# Install the tool
pip install -e .

# Run full analysis (requires rf-api and rf-ui to be present)
api-catalog analyze

# List endpoints only
api-catalog list-endpoints
```

## Project Structure

```
src/
├── cli.py              # Typer CLI entry point
├── parsers/            # File parsers
│   ├── laravel_routes.py   # Parse routes/api/v1.php
│   ├── openapi_spec.py     # Parse OpenAPI JSON/YAML
│   └── angular_scopes.py   # Parse developer-settings.component.ts
├── analyzers/          # Analysis logic
│   ├── gap_analyzer.py     # Compare routes vs docs vs UI
│   └── scope_analyzer.py   # Analyze scope usage
├── reporters/          # Report generators
│   ├── markdown_report.py
│   ├── csv_report.py
│   └── console_report.py
├── testers/            # Live API testing (Phase 2)
└── models/             # Pydantic/dataclass models
    ├── endpoint.py
    ├── scope.py
    └── test_result.py
```

## Key Patterns

### Data Models
- Use Python `dataclasses` for all data models
- Use `pathlib.Path` for all file paths
- Use Pydantic for validation where needed

### CLI
- Built with Typer for rich CLI experience
- Rich library for terminal output
- Default paths configured for ~/dev/rf-api and ~/dev/rf-ui

### Parsers
- Regex-based parsing for Laravel routes (avoids PHP runtime)
- JSON/YAML parsing for OpenAPI specs
- Pattern matching for Angular TypeScript

## Default Paths

The tool expects these files to exist for full analysis:

| Source | Default Path |
|--------|--------------|
| Routes | `~/dev/rf-api/routes/api/v1.php` |
| OpenAPI | `~/dev/rf-api/storage/api-docs/api-docs.json` |
| UI Config | `~/dev/rf-ui/.../developer-settings.component.ts` |
| Output | `~/dev/AI_prod_notes/rf-api/api-catalog/` |

## API Scopes

The tool has hardcoded API scopes from `ApiKey.php`:

- units, reservations, contacts, invoices, payments
- service_requests, tenants, webhooks
- ledger_accounts, ledger_entries, tasks
- communications, sales_leads, unit_contracts, restrictions

## Phase Status

- **Phase 1 (Static Analysis):** Complete
- **Phase 2 (Live Testing):** Not started

## Commands

| Command | Description |
|---------|-------------|
| `api-catalog analyze` | Full analysis with all reports |
| `api-catalog catalog` | Generate catalog report only |
| `api-catalog gaps` | Generate gap analysis only |
| `api-catalog list-endpoints` | List all endpoints |
| `api-catalog version` | Show version |

## Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run the CLI
api-catalog --help
```

## Output Files

Reports are generated to the output directory:

- `catalog-YYYY-MM-DD.md` - Full endpoint inventory
- `gaps-YYYY-MM-DD.md` - Gap analysis with recommendations
- `api-review-summary.csv` - Spreadsheet summary

## Prerequisites

Before running full analysis, generate the OpenAPI spec:

```bash
cd ~/dev/rf-api
./vendor/bin/sail artisan l5-swagger:generate
```

## Notes for Claude

- This is a Python 3.11+ project using Typer CLI
- Use `rich` library for any console output
- Parsers should be robust to file format variations
- Reports should be human-readable and actionable
- The tool is intentionally separate from rf-api for independence
