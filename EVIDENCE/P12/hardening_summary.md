Container/IaC hardening highlights

- Base image pinned to `python:3.11-slim` (no unpinned `latest`).
- Application runs as non-root user `app` with dedicated group; attachment directory ownership set to this user.
- Healthcheck defined for `http://127.0.0.1:8000/health` to detect unresponsive containers.
- Only runtime files are copied into the image; dependencies are installed in an isolated venv to keep the final image small.
- Attachments path exposed as a volume to keep writable data out of the image filesystem.
