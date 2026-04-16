"""
Analyzer to compare local OpenAPI spec with published spec.

Identifies discrepancies between what's documented locally and what's live.
"""

from dataclasses import dataclass, field

from ..models.endpoint import DocumentedEndpoint


@dataclass
class DocsDiffReport:
    """Report comparing local docs to published docs."""
    local_only: list[str] = field(default_factory=list)  # In local but not published
    published_only: list[str] = field(default_factory=list)  # In published but not local
    local_count: int = 0
    published_count: int = 0
    match_count: int = 0

    @property
    def has_differences(self) -> bool:
        return len(self.local_only) > 0 or len(self.published_only) > 0


def analyze_docs_diff(
    local_endpoints: list[DocumentedEndpoint],
    published_endpoints: list[DocumentedEndpoint],
) -> DocsDiffReport:
    """
    Compare local docs with published docs.

    Args:
        local_endpoints: Endpoints from local OpenAPI spec (public only)
        published_endpoints: Endpoints from published spec

    Returns:
        DocsDiffReport with differences
    """
    # Filter to public endpoints only for local
    local_public = [e for e in local_endpoints if not e.is_internal]

    local_ids = {e.endpoint_id for e in local_public}
    published_ids = {e.endpoint_id for e in published_endpoints}

    report = DocsDiffReport(
        local_only=sorted(local_ids - published_ids),
        published_only=sorted(published_ids - local_ids),
        local_count=len(local_public),
        published_count=len(published_endpoints),
        match_count=len(local_ids & published_ids),
    )

    return report
