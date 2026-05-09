# Portfolio Backend API

A lightweight **FastAPI** backend powering the contact form for my Angular portfolio. It stores submissions in **MongoDB Atlas** and exposes a health-check endpoint so the frontend can conditionally render the contact form.

---

## ✨ Features

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Welcome / sanity-check |
| `/health` | GET | Liveness probe for the frontend |
| `/api/contact` | POST | Save a contact form submission |
| `/api/contacts` | GET | Retrieve all submissions |
| `/api/contacts` | DELETE | Bulk-delete submissions by ID |
| `/docs` | GET | Auto-generated Swagger UI |
| `/redoc` | GET | ReDoc documentation |

---

## 🛠️ Tech Stack

- **Python 3.11+**
- **FastAPI** — async web framework
- **Uvicorn** — ASGI server
- **Motor** — async MongoDB driver
- **MongoDB Atlas** — cloud database
- **Pydantic v2** — data validation & serialisation
- **python-dotenv** — environment variable management

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/portfolio_backend.git
cd portfolio_backend
```

### 2. Create and activate a virtual environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and set your MongoDB Atlas connection string:

```env
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/portfolio?retryWrites=true&w=majority
```

### 5. Run the development server

```bash
python run.py
```

The API will be available at `http://127.0.0.1:8000`.  
Visit `http://127.0.0.1:8000/docs` for the interactive Swagger UI.

---

## 📁 Project Structure

```
portfolio_backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app, middleware, routers
│   ├── database.py      # MongoDB connection lifecycle
│   ├── models.py        # Pydantic request/response models
│   └── routes/
│       ├── health.py    # /health endpoint
│       └── contact.py   # /api/contact endpoints
├── .env.example         # Environment variable template
├── .gitignore
├── requirements.txt
├── run.py               # Uvicorn entry point
└── README.md
```

---

## 🌐 CORS

By default, the allowed origins include:

```
http://localhost:4200      (Angular dev server)
http://127.0.0.1:4200
```

Update the `origins` list in `app/main.py` before deploying to production.

---

## 📦 Deployment

The app can be deployed to any platform that supports Python ASGI apps (e.g. **Render**, **Railway**, **Fly.io**, **AWS**). Set the `MONGODB_URI` environment variable on the platform and run:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 📄 License

This project is open-source under the [MIT License](LICENSE).
