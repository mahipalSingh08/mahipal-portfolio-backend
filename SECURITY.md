# Security

This API protects admin contact-management endpoints with short-lived bearer tokens.

## Protected Endpoints

| Endpoint | Method | Protection |
|---|---|---|
| `/api/contacts` | GET | `Authorization: Bearer <token>` |
| `/api/contacts` | DELETE | `Authorization: Bearer <token>` |

Public endpoints:

- `POST /api/contact`
- `POST /api/auth/login`
- `GET /health`
- `GET /`

## Admin Login

Configure these environment variables:

```env
AUTH_USER_ID=admin
AUTH_PASSWORD_HASH=your_precomputed_password_hash
AUTH_SESSION_DURATION_MINUTES=60
```

Request a session token:

```bash
curl -X POST "https://your-api.com/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"admin","hash_password":"your_precomputed_password_hash"}'
```

Use the returned token:

```bash
curl "https://your-api.com/api/contacts?page=1&limit=10" \
  -H "Authorization: Bearer <token>"
```

Delete contacts:

```bash
curl -X DELETE "https://your-api.com/api/contacts" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"ids":["507f1f77bcf86cd799439011"]}'
```

## Production Checklist

- Set `ENVIRONMENT=production`.
- Set `ENABLE_DOCS=false` unless public docs are intended.
- Restrict `CORS_ORIGINS` to deployed frontend origins only.
- Store secrets only in the deployment provider secret manager.
- Use HTTPS for the frontend and API.
- Keep MongoDB network access restricted.
- Rotate `AUTH_PASSWORD_HASH` if it is exposed.
- Keep `AUTH_SESSION_DURATION_MINUTES` short enough for the admin workflow.

## Notes

- Tokens are random URL-safe values stored in MongoDB.
- Session cleanup uses a MongoDB TTL index on `auth_sessions.expires_at`.
- API responses avoid returning raw server exception details.
