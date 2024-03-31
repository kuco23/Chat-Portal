from sys import stdout
from os import getenv
from datetime import datetime
from pathlib import Path
import logging
from dotenv import load_dotenv

load_dotenv('.env', override=True)

LOG_LEVEL = int(getenv("CHAT_PORTAL_LOG_LEVEL", 100))
LOG_STDOUT = getenv("CHAT_PORTAL_LOG_STDOUT", False)

if LOG_LEVEL <= 50:
    # create log directory if not exists
    log_dir = Path('log')
    log_dir.mkdir(exist_ok=True)
    # create log file named by current time
    log_name = datetime.now().strftime("%Y-%m-%d") + '.log'
    log_path = log_dir / log_name
else:
    log_path = Path('/dev/null')

# create chat portal logger
logger = logging.getLogger("Chat Portal")
logger.setLevel(LOG_LEVEL)
if LOG_STDOUT:
    handler = logging.StreamHandler(stdout)
else:
    handler = logging.FileHandler(str(log_path))
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)