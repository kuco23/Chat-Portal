from datetime import datetime
from pathlib import Path
import logging

# create log directory if not exists
log_dir = Path('log')
log_dir.mkdir(exist_ok=True)

# create log file named by current time
log_name = datetime.now().strftime("%Y-%m-%d") + '.log'
log_path = log_dir / log_name

# create chat portal logger
logger = logging.getLogger("Chat Portal")
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler(str(log_path))
fh.setLevel(logging.DEBUG)
fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(fh)