# Security Policy

## Reporting a vulnerability

Please report suspected vulnerabilities privately to the maintainers rather than
opening a public issue. Include reproduction steps and affected version.

## Scope notes for this prototype

- Auth is open by default (`PROVENABLY_API_KEYS` empty). Do not deploy publicly
  without setting keys or replacing `require_api_key` with your IdP.
- Uploads are read fully into memory (cap `MAX_UPLOAD_MB`, default 200). Not
  suitable for untrusted multi-tenant load without streaming + limits.
- No rate limiting is implemented yet.
- The demo trust anchor and test CA are for development only; never use them
  for production signing.