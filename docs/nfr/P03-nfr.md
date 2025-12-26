# P03 — Non-Functional Security Requirements

<a id="nfr-sc-1"></a>
### NFR-SC-1 — Authenticated mutations
- Requirement: Mutating API endpoints **must** require authenticated callers (API key or stronger control).
- Rationale: Protect integrity of inventory data from unauthorized updates.

<a id="nfr-sc-2"></a>
### NFR-SC-2 — Canonicalised item names
- Requirement: User-supplied item names **must** be validated for length and character set before persistence.
- Rationale: Reduce risk of injection and resource exhaustion.

<a id="nfr-r-1"></a>
### NFR-R-1 — Opaque internal errors
- Requirement: The service **must not** leak internal exception details to clients.
- Rationale: Avoid giving attackers implementation hints (maps to P04/F2).

Last updated: 2025-10-23.
