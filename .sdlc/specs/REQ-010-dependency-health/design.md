# REQ-010: Dependency Health Assessment — Design

## Status

Placeholder — to be completed during implementation planning.

## Architecture

See [ADR-040](../../adrs/ADR-040-scan-metadata-enrichment.md) for the scan metadata contract.
See [ADR-038](../../adrs/ADR-038-public-data-api.md) for the Gateway API surface.

## Key Design Decisions

- Sidecar container vs. Gateway-embedded (decided: sidecar for isolation)
- Gateway API as the interface for both input (dependency queries) and output (health assessments)
- Engine as the scanner for collection content (reuse, not new capability)
- Vulnerability database selection (OSV.dev recommended)
- Caching strategy: collection+version is immutable, scan once; CVE data has TTL

## Key ADRs

- [ADR-040: Scan Metadata Enrichment](../../adrs/ADR-040-scan-metadata-enrichment.md) — prerequisite
- [ADR-038: Public Data API](../../adrs/ADR-038-public-data-api.md) — Gateway API contract
- [ADR-001: gRPC Communication](../../adrs/ADR-001-grpc-communication.md) — engine scan interface
