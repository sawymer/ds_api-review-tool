from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ParsedEndpoint:
    """An endpoint parsed from Laravel routes file."""
    method: str  # GET, POST, PATCH, DELETE
    path: str  # /units/{id}
    full_path: str  # /api/v1/units/{id}
    controller: str  # UnitController
    action: str  # index, show, store, update, destroy
    scopes: list[str] = field(default_factory=list)  # ['units:read']
    middleware: list[str] = field(default_factory=list)
    line_number: int = 0
    resource_group: str = ""  # units, reservations, etc.

    @property
    def endpoint_id(self) -> str:
        """Unique identifier for this endpoint (without /api/v1 prefix for comparison)."""
        return f"{self.method} {self.path}"

    @property
    def requires_write_scope(self) -> bool:
        """Check if this endpoint requires a write scope."""
        return any(":write" in scope for scope in self.scopes)


@dataclass
class DocumentedEndpoint:
    """An endpoint documented in OpenAPI spec."""
    method: str
    path: str
    operation_id: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    parameters: list[dict] = field(default_factory=list)
    request_body: Optional[dict] = None
    responses: dict = field(default_factory=dict)
    security: list[dict] = field(default_factory=list)

    @property
    def endpoint_id(self) -> str:
        """Unique identifier for this endpoint."""
        return f"{self.method.upper()} {self.path}"
