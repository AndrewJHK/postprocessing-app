import logging

logger = logging.getLogger("postprocessing-app")
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("app.log", mode='a', encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

if not logger.hasHandlers():
    logger.addHandler(file_handler)

logger.propagate = False
