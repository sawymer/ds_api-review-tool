from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class EndpointStatus(Enum):
    """Status of an endpoint after testing."""
    WORKING = "Working"
    PARTIAL = "Partial"
    BROKEN = "Broken"
    UNTESTED = "Untested"
    SKIPPED = "Skipped"


@dataclass
class TestResult:
    """Result of testing a single endpoint."""
    endpoint: str  # e.g., "GET /api/v1/units"
    method: str
    path: str
    scope_required: str
    documented: bool
    ui_access_available: bool
    status: EndpointStatus = EndpointStatus.UNTESTED
    response_code: Optional[int] = None
    response_time_ms: Optional[int] = None
    schema_valid: Optional[bool] = None
    tests_passed: list[str] = field(default_factory=list)
    tests_failed: list[str] = field(default_factory=list)
    error_message: Optional[str] = None
    notes: str = ""
    tested_at: Optional[datetime] = None

    def to_csv_row(self) -> list[str]:
        """Convert to CSV row values."""
        return [
            self.endpoint,
            self.scope_required,
            "Yes" if self.documented else "No",
            "Yes" if self.ui_access_available else "No",
            self.status.value,
            self.tested_at.strftime("%Y-%m-%d") if self.tested_at else "",
            self.notes,
        ]

    @staticmethod
    def csv_headers() -> list[str]:
        """Get CSV header row."""
        return [
            "Endpoint",
            "API Scope Required",
            "Documented",
            "UI Access Available",
            "Functional Status",
            "Last Tested Date",
            "Notes",
        ]
