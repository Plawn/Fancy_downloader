from enum import Enum

CHUNK_SIZE = 65556
MAX_RETRY = 10
TIME_BETWEEN_DL_START = 0.1
SUCCESS_CODES = (200, 206)
TO_REMOVE = frozenset((',', ';', '&', "'", '/', ')', '('))
DEFAULT_SPLIT_COUNT = 5


DEFAULT_USER_AGENT = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36"
}


class Status(Enum):
    FINISHED = 'FINISHED'
    PAUSED = 'PAUSED'
    DOWNLOADING = 'DOWNLOADING'
    STOPPED = 'STOPPED'
    SLOW = 'SLOW'
