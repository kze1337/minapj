#########################################################
# Author: Yuuki (@yuuki.dn)
# Chỉ cần import vào thôi, code nó tự chạy <(")
#########################################################

from logging import Filter, StreamHandler, INFO, ERROR, Formatter, WARNING, basicConfig, FileHandler, DEBUG, getLogger
from os import makedirs
from sys import stdout, stderr

from colorama import Fore, Style, init

# Create file .logs/.log if not exist
try:
    open(".logs/log.log", "a").close()
except FileNotFoundError:
    makedirs(".logs", exist_ok=True)
    open(".logs/log.log", "w").close()

asyncio_logger = getLogger("asyncio")

asyncio_logger.disabled = True


class SpectificLevelFilter(Filter):
    ## Logging filter that allow only the spectified level to be processed
    def __init__(self, level: int):
        super().__init__()
        self.level = level

    def filter(self, record) -> bool:
        return record.levelno == self.level

## Format (console only)
INFO_FORMAT = f"{Style.DIM}[%(asctime)s]{Style.RESET_ALL} [%(name)s:%(lineno)d] [✅] {Fore.GREEN}[%(levelname)s] - %(message)s{Style.RESET_ALL}"
WARNING_FORMAT = f"{Style.DIM}[%(asctime)s]{Style.RESET_ALL} [%(name)s:%(lineno)d] [⚠️]  {Fore.YELLOW}[%(levelname)s] - %(message)s{Style.RESET_ALL}"
ERROR_FORMAT = f"{Style.DIM}[%(asctime)s]{Style.RESET_ALL} [%(name)s:%(lineno)d] [❌] {Fore.RED}[%(levelname)s] - %(message)s{Style.RESET_ALL}"
DEBUG_FORMAT = f"{Style.DIM}[%(asctime)s]{Style.RESET_ALL} [%(name)s:%(lineno)d] [🐛] {Fore.BLUE}[%(levelname)s] - %(message)s{Style.RESET_ALL}"

DATEFMT="%d-%m-%Y %H:%M:%S"

## Create handlers
infoHandler = StreamHandler(stream=stdout)
infoHandler.setLevel(INFO)
infoHandler.addFilter(SpectificLevelFilter(INFO))
infoHandler.setFormatter(Formatter(INFO_FORMAT, datefmt=DATEFMT))

warningHandler = StreamHandler(stream=stdout)
warningHandler.setLevel(WARNING)
warningHandler.addFilter(SpectificLevelFilter(WARNING))
warningHandler.setFormatter(Formatter(WARNING_FORMAT, datefmt=DATEFMT))

errorHandler = StreamHandler(stream=stderr)
errorHandler.setLevel(ERROR)
errorHandler.addFilter(SpectificLevelFilter(ERROR))
errorHandler.setFormatter(Formatter(ERROR_FORMAT, datefmt=DATEFMT))

debugHandler = StreamHandler(stream=stderr)
debugHandler.setLevel(DEBUG)
debugHandler.addFilter(SpectificLevelFilter(DEBUG))
debugHandler.setFormatter(Formatter(DEBUG_FORMAT, datefmt=DATEFMT))

fileHandler = FileHandler(".logs/SessionLog.log", mode="w", encoding="utf-8")
fileHandler.setLevel(INFO)
fileHandler.setFormatter(Formatter("%(asctime)s %(name)s:%(lineno)d [%(levelname)s] - %(message)s", datefmt=DATEFMT))

## Configure
basicConfig(
    level=INFO,
    handlers=[infoHandler, warningHandler, errorHandler, fileHandler, debugHandler]
)

def setup_logger():
    init(autoreset=True)