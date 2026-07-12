"""Reset and seed the development database. Run: python seed_dev.py"""
from app import create_app
from app.seed import reset_db, seed

app = create_app()
reset_db(app.db_engine)
seed(app.db_session)
app.db_session.remove()
print("seeded", app.config["DATABASE_URL"])
