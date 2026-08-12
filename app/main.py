from dotenv import load_dotenv
load_dotenv()  # must run before database.py reads DATABASE_URL from the environment

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import auth_router, investments_router, portfolio_router

# Creates tables on startup if they don't exist yet. For anything beyond a
# personal project, swap this for Alembic migrations.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Private Markets Portfolio Tracker API",
    description="Track fund commitments, capital calls, distributions, and NAV. "
                 "Computes IRR (XIRR), MOIC/TVPI, DPI, and RVPI per investment and portfolio-wide.",
    version="1.0.0",
)

# Allow the React dev server / deployed frontend to call this API.
# Tighten allow_origins to your actual frontend domain in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(investments_router.router)
app.include_router(portfolio_router.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "portfolio-tracker-api"}


@app.get("/health")
def health():
    return {"status": "healthy"}
