# Security Guide

## Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `META_ACCESS_TOKEN` | Yes | Meta API bearer token for authenticating WhatsApp Cloud API requests |
| `META_PHONE_NUMBER_ID` | Yes | WhatsApp phone number ID used as the sender |
| `META_BUSINESS_ACCOUNT_ID` | Recommended | Business account ID for webhook and business operations |
| `WABA_ID` | Recommended | WhatsApp Business Account ID (fallback to `META_BUSINESS_ACCOUNT_ID`) |
| `META_APP_ID` | Recommended | Meta App ID for webhook token and field management |
| `META_APP_SECRET` | Recommended | App secret for verifying webhook payload signatures (HMAC-SHA256) |
| `MCP_API_KEY` | Recommended | API key required in `X-API-Key` header for all `/api/*` endpoints |
| `ALLOWED_ORIGINS` | Optional | Comma-separated list of allowed CORS origins. If empty, CORS is disabled |
| `MEDIA_UPLOAD_DIR` | Optional | Directory from which media uploads are allowed (default: `/tmp/whatsapp-media/`) |
| `META_BUSINESS_PORTFOLIO_ID` | Optional | Business portfolio ID for advanced account operations |
| `WHATSAPP_API_VERSION` | Optional | Graph API version (default: `v22.0`) |
| `PORT` | Optional | HTTP server listen port (default: `8080`) |

## Webhook Signature Verification

Meta signs every webhook payload with your app secret using HMAC-SHA256. The signature is sent in the `X-Hub-Signature-256` header in the format `sha256=<hex_digest>`.

### Setup

1. Copy your App Secret from the Meta App Dashboard.
2. Set `META_APP_SECRET` in your `.env` file.
3. The `WebhookHandler` reads this value at startup. If missing, a warning is printed and signature verification is unavailable.

### How it works

`WebhookHandler.verify_webhook_signature(payload, signature)`:
- Computes `HMAC-SHA256(META_APP_SECRET, raw_body)`.
- Extracts the hex digest from the `sha256=...` header value.
- Uses `hmac.compare_digest` for constant-time comparison.
- Returns `False` if the secret is not configured, the header is missing, or the signature does not match.

Call this method on every incoming webhook request before processing the payload.

## API Key Authentication

When `MCP_API_KEY` is set, every request to `/api/*` endpoints must include a matching `X-API-Key` header. Requests with a missing or incorrect key receive a `401 Unauthorized` response.

### Setup

1. Generate a strong random key (e.g., `openssl rand -hex 32`).
2. Set `MCP_API_KEY` in your `.env` file.
3. Pass the key in every HTTP request: `X-API-Key: <your-key>`.

If `MCP_API_KEY` is not set, API key authentication is disabled (development mode). **Always set this in production.**

## Rate Limiting

An in-memory token bucket rate limiter is applied to all `/api/*` endpoints:

- **Rate**: 10 requests per second per client IP.
- **Burst**: Up to 10 requests in a single burst before throttling.
- **Response**: `429 Too Many Requests` when the limit is exceeded.
- **Client IP**: Extracted from the `X-Forwarded-For` header (first entry) or the direct connection IP.

**Limitations**: The rate limiter is in-memory and per-process. It resets on server restart and does not share state across multiple server instances. For multi-instance deployments, use an external rate limiter (e.g., Redis-backed, API gateway).

## Media Upload Directory Restrictions

The `MediaHandler` enforces path traversal protection on all file uploads:

- The `MEDIA_UPLOAD_DIR` environment variable defines the allowed base directory (default: `/tmp/whatsapp-media/`).
- Before any upload, the file path is resolved to its real (canonical) path via `os.path.realpath`.
- The resolved path must start with the allowed directory. If not, the request is rejected with an access denied error.
- This prevents directory traversal attacks (e.g., `../../etc/passwd`).

Ensure the upload directory exists and has appropriate permissions before starting the server.

## Security Headers

The following headers are added to all HTTP responses:

| Header | Value | Purpose |
|---|---|---|
| `X-Content-Type-Options` | `nosniff` | Prevents MIME-type sniffing |
| `X-Frame-Options` | `DENY` | Prevents clickjacking via iframes |
| `Cache-Control` | `no-store` | Prevents caching of responses |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Enforces HTTPS (only set when request arrives over HTTPS) |

## Production Checklist

- [ ] Set `META_ACCESS_TOKEN` and `META_PHONE_NUMBER_ID` with valid credentials
- [ ] Set `META_APP_SECRET` to enable webhook signature verification
- [ ] Set `MCP_API_KEY` to a strong random value (`openssl rand -hex 32`)
- [ ] Set `ALLOWED_ORIGINS` to your specific frontend domain(s) — never use `*`
- [ ] Set `MEDIA_UPLOAD_DIR` to a dedicated directory with restrictive permissions
- [ ] Run behind a reverse proxy (nginx, Caddy) that terminates TLS
- [ ] Enable HSTS by serving over HTTPS (the server sets the header automatically)
- [ ] Do not expose the server directly to the internet — use a firewall or cloud security group
- [ ] For multi-instance deployments, add an external rate limiter (API gateway or Redis)
- [ ] Rotate `META_ACCESS_TOKEN` and `MCP_API_KEY` regularly
- [ ] Monitor logs for authentication failures and rate limit hits
- [ ] Keep the `.env` file out of version control (already in `.gitignore`)
