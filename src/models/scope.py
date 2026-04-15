from dataclasses import dataclass, field


@dataclass
class Scope:
    """A single API scope."""
    name: str  # e.g., "units:read"
    resource: str  # e.g., "units"
    permission: str  # "read" or "write"

    @classmethod
    def from_string(cls, scope_str: str) -> "Scope":
        """Parse a scope string like 'units:read'."""
        parts = scope_str.split(":")
        if len(parts) == 2:
            return cls(name=scope_str, resource=parts[0], permission=parts[1])
        return cls(name=scope_str, resource=scope_str, permission="unknown")


@dataclass
class ScopeGroup:
    """A group of scopes for a resource (from UI configuration)."""
    resource: str  # e.g., "Units"
    resource_key: str  # e.g., "units"
    read_scope: str = ""  # e.g., "units:read"
    write_scope: str = ""  # e.g., "units:write"
    read_only: bool = False

    @property
    def scopes(self) -> list[str]:
        """Get all scopes in this group."""
        scopes = []
        if self.read_scope:
            scopes.append(self.read_scope)
        if self.write_scope and not self.read_only:
            scopes.append(self.write_scope)
        return scopes
