import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# MySQL connection string format:
# mysql+pymysql://<user>:<password>@<host>:<port>/<database>
#
# Local dev example (after creating the DB - see README):
#   mysql+pymysql://root:yourpassword@localhost:3306/portfolio_tracker
#
# Hosted MySQL (PlanetScale, Railway, AWS RDS, etc.) - copy the connection
# string they give you and swap the driver prefix to mysql+pymysql://
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:password@localhost:3306/portfolio_tracker",
)

# pool_pre_ping avoids "MySQL server has gone away" errors on idle connections
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=280)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
