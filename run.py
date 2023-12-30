import os
from time import sleep
from configparser import ConfigParser
from dotenv import load_dotenv
from sqlalchemy_utils import database_exists
from openai import OpenAI
from src import Database, Instagram, GptPortal

# take program config from config.cfg
# and environment variables from .env
config = ConfigParser()
config.read("config.cfg")
load_dotenv()

# read config
DATABASE_URL = config["DATABASE"]["URL"]
OPENAI_MODEL = config["OPENAI"]["MODEL"]
MID_RUN_SLEEP = int(config["PROGRAM"]["MID_RUN_SLEEP_SECONDS"])

# read environment variables
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")
if INSTAGRAM_USERNAME is None or INSTAGRAM_PASSWORD is None:
    raise Exception("Instagram username and password must be set in .env")

# check if this is the first time script is being run
FIRST_SCRIPT_RUN = not database_exists(DATABASE_URL)

# define program components
database = Database(DATABASE_URL)
instagram = Instagram(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
openai = OpenAI() # takes OPENAI_API_KEY from os.environ
portal = GptPortal(database, instagram, openai, OPENAI_MODEL)

# jumpstart if the script was never run before
# this is to aid of broken database migrations
if FIRST_SCRIPT_RUN:
    print("First script run detected, jumpstarting...")
    portal.jumpstart()
    sleep(MID_RUN_SLEEP)

# run main loop
print("Running main loop...")
while True:
    portal.runStep()
    sleep(MID_RUN_SLEEP)