from enum import Enum


class Status(Enum):
    FINISHED = 'done'
    DONE = 'done'
    PAUSED = 'paused'
    DOWNLOADING = 'downloading'
    STOPPED = 'stopped'
