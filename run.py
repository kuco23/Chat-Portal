import time, os
from configparser import ConfigParser
from dotenv import load_dotenv
from src import Instagram, Database, Portal

# take program config from config.cfg
# and environment variables from .env
config = ConfigParser()
config.read("config.cfg")
load_dotenv()

# read config
DATABASE_URL = config["DATABASE"]["URL"]
MID_RUN_SLEEP = int(config["PROGRAM"]["MID_RUN_SLEEP_SECONDS"])

# read environment variables
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")
if INSTAGRAM_USERNAME is None or INSTAGRAM_PASSWORD is None:
    raise Exception("Instagram username and password must be set in .env")

# define program components
instagram = Instagram(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
database = Database(DATABASE_URL)
portal = Portal(database, instagram)

# run main loop
while True:
    portal.runStep()
    time.sleep(MID_RUN_SLEEP)