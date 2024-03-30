from os import getenv
from datetime import datetime
from pathlib import Path
import logging

LOG_LEVEL = int(getenv("CHAT_PORTAL_LOG_LEVEL", 100))

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
# create file handler which logs even debug messages
fh = logging.FileHandler(str(log_path))
fh.setLevel(logging.DEBUG)
fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(fh)