# Ledger: Private Markets Portfolio Tracker

A web app for tracking private-markets fund commitments (private equity, venture capital, real estate, private credit, infrastructure). Log capital calls and distributions per fund and see portfolio-level performance.

This repository is the **React frontend only**. It talks to a separate REST API (see [API contract](#api-contract)).

## Features

- Email/password registration and login (JWT bearer token)
- Portfolio dashboard: total committed, paid-in capital, distributions, current NAV, portfolio TVPI and IRR
- Fund positions table with per-fund TVPI and IRR
- Add a fund commitment (name, asset class, vintage year, commitment, optional NAV)
- Fund detail page: paid-in, distributed, DPI, TVPI/MOIC, IRR, and a cumulative cashflow chart
- Add or delete cashflows, bulk-import them from CSV, and update NAV

## Tech stack

React 19, Vite, React Router, Axios, Recharts.

## Run locally

```bash
npm install
npm run dev
```

The app calls the API at `http://localhost:8000` by default. To point it elsewhere, create a `.env` file:

```
VITE_API_URL=https://your-backend.example.com
```

Other scripts: `npm run build`, `npm run preview`, `npm run lint`.

## Architecture notes

- `src/api/client.js`: one Axios instance. A request interceptor attaches `Authorization: Bearer <token>`. A response interceptor clears the token and redirects to `/login` on any 401.
- `src/context/AuthContext.jsx`: login, register and logout. The token is kept in `localStorage`.
- `src/components/ProtectedRoute.jsx`: redirects unauthenticated users to `/login`.
- All performance metrics (TVPI, DPI, IRR) are computed by the backend and only formatted here (`src/utils/format.js`).

## API contract

These are the endpoints the frontend calls. A backend must provide them.

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/register` | Body `{email, password}` |
| POST | `/auth/login` | Form-encoded `username` (the email) and `password`; returns `{access_token}` |
| GET | `/portfolio/summary` | `total_committed`, `total_paid_in`, `total_distributions`, `total_nav`, `portfolio_tvpi`, `portfolio_irr` |
| GET | `/investments` | List of investments |
| POST | `/investments` | Body `{fund_name, asset_class, vintage_year, commitment_amount, current_nav}` |
| GET | `/investments/{id}` | One investment |
| PATCH | `/investments/{id}` | Body `{current_nav, nav_as_of}` (`nav_as_of` is `YYYY-MM-DD`) |
| DELETE | `/investments/{id}` | Also removes its cashflows |
| GET | `/investments/{id}/metrics` | `paid_in`, `distributions`, `dpi`, `tvpi`, `irr` |
| GET | `/investments/{id}/cashflow-timeline` | Array of `{date, cumulative_paid_in, cumulative_distributions}` |
| POST | `/investments/{id}/cashflows` | Body `{type, amount, date, note}`; `type` is `capital_call` or `distribution` |
| DELETE | `/investments/{id}/cashflows/{cashflow_id}` | Remove one cashflow |
| POST | `/investments/{id}/cashflows/import-csv` | Multipart `file` with columns `type,amount,date,note`; returns the created cashflows |

Errors are read from `response.data.detail`. Missing optional metrics (such as IRR before any cashflows) are expected as `null`.
