import string
from os import getenv
from time import sleep
from configparser import ConfigParser
from dotenv import load_dotenv
from sqlalchemy_utils import database_exists
from chat_portal import Database
from chat_portal.platforms import Instagram
from chat_portal.portals import GptPortal


def extract_field_names(format_string):
    formatter = string.Formatter()
    return [field_name for _, field_name, _, _ in formatter.parse(format_string) if field_name]

# take program config from config.cfg
# and environment variables from .env
config = ConfigParser()
config.read("config.cfg")
load_dotenv()

# read config
DATABASE_URL = config["DATABASE"]["URL"]
OPENAI_MODEL = config["OPENAI"]["MODEL"]
MID_RUN_SLEEP = int(config["PROGRAM"]["MID_RUN_SLEEP_SECONDS"])
PROMPT_TEMPLATE_PATH = config["PROGRAM"]["PROMPT_TEMPLATE_PATH"]

# read environment variables
INSTAGRAM_USERNAME = getenv("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = getenv("INSTAGRAM_PASSWORD")
if INSTAGRAM_USERNAME is None or INSTAGRAM_PASSWORD is None:
    raise Exception("Instagram username and password must be set in .env")

# format system prompt
SYSTEM_PROMPT = open(PROMPT_TEMPLATE_PATH, 'r').read()
field_names = extract_field_names(SYSTEM_PROMPT)
SYSTEM_PROMPT = SYSTEM_PROMPT.format(**{name: getenv(name) for name in field_names})

# check if this is the first time script is being run
FIRST_SCRIPT_RUN = not database_exists(DATABASE_URL)

# define program components
database = Database(DATABASE_URL)
instagram = Instagram(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
portal = GptPortal(database, instagram, OPENAI_MODEL, SYSTEM_PROMPT)

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