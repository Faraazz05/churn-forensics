# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | ✅ Yes    |

## Reporting a Vulnerability

If you discover a security vulnerability, please **do not** open a public GitHub issue.

Email the maintainer directly or open a private GitHub security advisory:
`Settings → Security → Advisories → New draft security advisory`

You will receive a response within 48 hours.

---

## Security Practices in This System

### API Authentication
- Every endpoint requires an `X-API-Key` header.
- Two roles: `admin` (full access) and `read_only` (GET only).
- Keys are set via environment variables — never hardcoded.
- Rotate keys by updating `API_KEY_ADMIN` and `API_KEY_READONLY` in your deployment environment.

### Environment Secrets
- Never commit `.env` to Git — it is in `.gitignore`.
- Use `.env.example` as documentation only (no real values).
- In production: set all secrets as environment variables in your hosting platform (Render, Railway, etc.).
- GitHub Actions secrets: store `API_KEY_ADMIN`, `API_KEY_READONLY`, `RENDER_DEPLOY_HOOK_URL` in `Settings → Secrets`.

### Database
- Production uses PostgreSQL with a dedicated non-root user.
- Development uses SQLite (no credentials required).
- Never expose PostgreSQL port 5432 publicly in production.
- Use strong passwords for `POSTGRES_PASSWORD`.

### Docker
- The backend container runs as a **non-root user** (`appuser`, UID 1000).
- No sensitive files are baked into the Docker image — they are mounted as volumes.

### CORS
- In production, update `allow_origins` in `backend/src/main.py` to restrict to your actual frontend domain:
  ```python
  allow_origins=["https://your-frontend.vercel.app"]
  ```

### Data
- The 500K customer dataset is **synthetic** — no real PII.
- Uploaded files are stored in `uploads/` which is excluded from Git.
- Implement file scanning before production use with real customer data.

### LLM API Token
- `HUGGINGFACEHUB_API_TOKEN` is optional (system works in `rules` mode without it).
- If used, store only in environment variables, never in code.
