# Repository instructions

- Keep the application self-hosted and Raspberry Pi friendly.
- Do not commit credentials, .env files, media, databases, or user uploads.
- Validate uploaded file types, paths, and size limits. Never trust client-provided filenames.
- Keep admin endpoints authenticated; player endpoints should expose only the content needed for playback.
- Do not expose the service directly to the public internet. Document VPN/TLS requirements for remote administration.
- Preserve a simple upgrade path; avoid patching upstream signage software until the integration need is proven.
- For code changes, run Python compilation and automated tests where the environment allows. State clearly when hardware tests cannot be run.
- Update docs/STATE.md and docs/TASKS.md as implementation status changes.
