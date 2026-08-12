# Ledger — Private Markets Portfolio Tracker

A full-stack app for tracking private equity / real estate / VC fund commitments — capital calls, distributions, NAV — and computing real industry performance metrics: **IRR (XIRR), MOIC/TVPI, DPI, RVPI**.

**Stack:** React (Vite) · FastAPI · MySQL · SQLAlchemy · JWT auth

## Features

- Email/password auth with JWT tokens
- Add fund commitments (name, asset class, vintage year, commitment amount)
- Log capital calls and distributions with dates and notes
- Update current NAV over time
- Auto-computed metrics per fund and portfolio-wide: **IRR, MOIC, TVPI, DPI, RVPI**
- Cashflow timeline chart (cumulative paid-in vs. distributions)
- CSV bulk import for cashflow history
- Cashflow ledger with delete support

## Project structure

```
portfolio-tracker/
  backend/          FastAPI app
    app/
      main.py        entrypoint
      models.py       SQLAlchemy models
      schemas.py       Pydantic request/response schemas
      calculations.py  IRR/MOIC/DPI math (the interesting part — read this)
      auth.py          JWT auth helpers
      routers/         auth, investments, portfolio endpoints
    requirements.txt
    .env.example
  frontend/          React app (Vite)
    src/
      pages/          Login, Register, Dashboard, InvestmentDetail
      components/     Layout, AddInvestmentModal, ProtectedRoute
      context/        AuthContext (JWT storage)
      api/            axios client
```

## 1. Local setup

### Prerequisites
- Python 3.10+
- Node 18+
- MySQL 8+ running locally (or a free hosted MySQL — see Deployment below)

### Create the database

```sql
CREATE DATABASE portfolio_tracker CHARACTER SET utf8mb4;
```

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env: set DATABASE_URL to your MySQL connection string and a random SECRET_KEY
# generate a secret with: openssl rand -hex 32

uvicorn app.main:app --reload --port 8000
```

Tables are created automatically on first run. API docs live at `http://localhost:8000/docs` (FastAPI's built-in Swagger UI — genuinely useful to demo in an interview).

### Frontend

```bash
cd frontend
npm install
cp .env.example .env    # sets VITE_API_URL=http://localhost:8000
npm run dev
```

Visit `http://localhost:5173`, register an account, and start adding funds.

### Try it with sample data

Add a fund, then log a couple of cashflows:
- Capital call: $500,000 on 2022-01-15
- Capital call: $500,000 on 2022-07-15
- Distribution: $300,000 on 2023-06-01
- Update NAV to $900,000

You should see DPI ≈ 0.30, TVPI ≈ 1.20, and a positive IRR.

### CSV import format

```csv
type,amount,date,note
capital_call,500000,2022-01-15,Initial call
capital_call,500000,2022-07-15,Second call
distribution,300000,2023-06-01,Q2 distribution
```

## 2. Deployment (free-tier friendly)

**Database — Railway or PlanetScale (MySQL, free tier available)**
1. Create a MySQL database on Railway (railway.app) or another MySQL host.
2. Copy the connection string and convert it to SQLAlchemy's format:
   `mysql+pymysql://user:password@host:port/dbname`

**Backend — Render**
1. Push this repo to GitHub.
2. On render.com: New → Web Service → connect the repo, root directory `backend`.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables: `DATABASE_URL`, `SECRET_KEY`.
6. Deploy — note the resulting URL (e.g. `https://ledger-api.onrender.com`).

**Frontend — Vercel**
1. On vercel.com: New Project → import the repo, root directory `frontend`.
2. Framework preset: Vite.
3. Add environment variable: `VITE_API_URL=https://ledger-api.onrender.com` (your Render URL).
4. Deploy.

**Final step:** in `backend/app/main.py`, tighten `allow_origins=["*"]` to your actual Vercel domain before calling it done — leaving it wide open is fine for a demo, but worth mentioning you know to fix it (good interview talking point).

## Why these metrics (for your own explanation in interviews)

- **Paid-in capital** — cash actually sent to the fund (sum of capital calls)
- **DPI** (Distributions to Paid-In) — cash actually returned, per dollar invested
- **RVPI** (Residual Value to Paid-In) — unrealized value still in the fund, per dollar invested
- **TVPI / MOIC** — DPI + RVPI, total value (realized + unrealized) per dollar invested
- **IRR** — the annualized return rate, computed via XIRR since real capital calls/distributions land on irregular dates, not neat yearly intervals

`app/calculations.py` implements XIRR from scratch (Newton's method with a bisection fallback) rather than pulling in a black-box library — worth walking through in an interview since it shows you understand the underlying math, not just an API call.
