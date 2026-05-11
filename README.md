# Portfolio Backend API

A lightweight FastAPI backend for an Angular portfolio contact form. It stores submissions in MongoDB Atlas and provides authenticated admin endpoints for reading and deleting contacts.

## Features

| Endpoint | Method | Description | Auth Required |
|---|---|---|---|
| `/` | GET | API welcome response | No |
| `/health` | GET | Liveness probe | No |
| `/api/auth/login` | POST | Admin login that returns a bearer token | No |
| `/api/contact` | POST | Save a contact form submission | No |
| `/api/contacts` | GET | Retrieve paginated submissions | Yes |
| `/api/contacts` | DELETE | Bulk-delete submissions by ID | Yes |
| `/docs` | GET | Swagger UI, when enabled | No |
| `/redoc` | GET | ReDoc, when enabled | No |

## Tech Stack

- Python 3.11+
- FastAPI
- Uvicorn
- Motor
- MongoDB Atlas
- Pydantic v2
- python-dotenv

## Getting Started

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
```

```powershell
.venv\Scripts\activate
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Set at least these values:

```env
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/portfolio?retryWrites=true&w=majority
MONGODB_DATABASE=portfolio
CORS_ORIGINS=http://localhost:4200,http://127.0.0.1:4200
AUTH_USER_ID=admin
AUTH_PASSWORD_HASH=your_precomputed_password_hash
AUTH_SESSION_DURATION_MINUTES=60
```

### 4. Run locally

```bash
python run.py
```

The API runs at `http://127.0.0.1:8000`. Swagger UI is available at `/docs` when `ENABLE_DOCS=true`.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `ENVIRONMENT` | `development` | Set to `production` in deployed environments |
| `APP_NAME` | `Portfolio Backend API` | FastAPI application name |
| `APP_VERSION` | `1.0.0` | FastAPI application version |
| `LOG_LEVEL` | `INFO` | Uvicorn log level for `run.py` |
| `ENABLE_DOCS` | `true` in development, `false` in production | Enables `/docs`, `/redoc`, and OpenAPI JSON |
| `MONGODB_URI` | none | MongoDB connection string |
| `MONGODB_DATABASE` | `portfolio` | MongoDB database name |
| `CORS_ORIGINS` | Angular localhost origins | Comma-separated allowed frontend origins |
| `AUTH_USER_ID` | none | Admin login user ID |
| `AUTH_PASSWORD_HASH` | none | Precomputed admin password hash expected from the frontend |
| `AUTH_SESSION_DURATION_MINUTES` | `60` | Bearer token lifetime |

## Authentication

Admin endpoints use a bearer token returned by `POST /api/auth/login`.

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"admin","hash_password":"your_precomputed_password_hash"}'
```

Use the returned token for protected routes:

```bash
curl "http://localhost:8000/api/contacts?page=1&limit=10" \
  -H "Authorization: Bearer <token>"
```

## Deployment

For Render, set the secret environment variables in the dashboard:

- `MONGODB_URI`
- `CORS_ORIGINS`
- `AUTH_USER_ID`
- `AUTH_PASSWORD_HASH`

The included `render.yaml` sets production defaults and starts the app with:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2
```

## Production Notes

- Store timestamps in UTC and convert to local time in the client when needed.
- Keep `ENABLE_DOCS=false` in production unless public API docs are intentional.
- Keep `CORS_ORIGINS` restricted to the deployed frontend domains.
- Rotate `AUTH_PASSWORD_HASH` and active sessions after credential exposure.
- MongoDB session documents expire automatically using a TTL index on `expires_at`.

## Project Structure

```text
portfolio_backend/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   └── routes/
│       ├── __init__.py
│       ├── auth.py
│       ├── contact.py
│       └── health.py
├── .env.example
├── .gitignore
├── requirements.txt
├── runtime.txt
├── render.yaml
├── run.py
└── SECURITY.md
```

## License

This project is open-source under the [MIT License](LICENSE).
