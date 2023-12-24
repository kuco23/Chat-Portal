import time, os
from dotenv import load_dotenv
from src import Instagram, Database, Mirroring

load_dotenv()  # take environment variables from .env.

SQLITE_URL = "sqlite:///database.db"
MIRRORING_STEP_SLEEP = 5 # seconds

INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")
if INSTAGRAM_USERNAME is None or INSTAGRAM_PASSWORD is None:
    raise Exception("Instagram username and password must be set in .env")

instagram = Instagram(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
database = Database(SQLITE_URL)
mirroring = Mirroring(database, instagram)

while True:
    mirroring.runStep()
    time.sleep(MIRRORING_STEP_SLEEP)