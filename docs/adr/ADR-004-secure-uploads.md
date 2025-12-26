# ADR-004: Harden Attachment Uploads

- Status: Accepted
- Date: 2025-12-26

## Context
- P04/F4 highlights the risk of path traversal and oversized payloads if uploads are accepted without strict validation.
- P03/NFR-UP-1 requires canonical paths, magic-byte verification, and bounded payloads for user uploads.
- We now need a small attachment endpoint for chore-related images without introducing storage abuse.

## Decision
- Add `POST /uploads` (API-key protected) that reads files in 1 MiB chunks and rejects bodies over 5 MB with `upload_too_large`.
- Validate filenames for traversal attempts, enforce UUID-based server-side names, and derive extensions from trusted magic-byte detection (PNG/JPEG only).
- Resolve the upload root from `UPLOAD_DIR` (default `uploads/`), disallow symlinked roots or parents, and persist metadata in-memory for tracing.
- Return RFC 7807 errors with correlation IDs on validation failures; store successful uploads as `<uuid>.<ext>`.

## Alternatives
- Trust `Content-Type` and client filenames — rejected because it permits spoofed MIME and traversal.
- Stream directly to object storage with presigned URLs — deferred until we add persistence beyond local disk.
- Keep uploads embedded in DB as base64 — rejected due to DB bloat and missing filesystem isolation.

## Consequences
- Only PNG/JPEG are accepted; other formats will require future whitelisting.
- Extra I/O to scan magic bytes and enforce limits adds minimal latency but protects the API surface.
- Operators must provision and rotate the upload directory; stale files should be cleaned periodically.

## Security impact
- Mitigates F4 by blocking traversal attempts, oversized bodies, and MIME spoofing; remaining risk is malware content (antivirus scanning is a future enhancement).

## Rollout plan
- Configure `UPLOAD_DIR` to a dedicated, non-symlinked path with restricted permissions.
- Monitor upload error rates; add housekeeping/retention jobs for accumulated files as volume grows.

## Links
- NFR: [P03 / NFR-UP-1](../nfr/P03-nfr.md#nfr-up-1)
- Threats: [P04 / F4](../threat-model/P04-threat-model.md#f4), [P04 / R4](../threat-model/P04-threat-model.md#r4)
- Verification: [tests/test_uploads.py](../../tests/test_uploads.py)
