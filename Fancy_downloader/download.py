import io
import threading
import time
from typing import Dict, List, Optional
import os

import requests

from . import download_methods, utils
from .constants import DEFAULT_SPLIT_COUNT, DEFAULT_USER_AGENT, Status, TO_REMOVE
from .utils import Action


class Download:
    """
    An object which can be downloaded later on :

    Parameters
    ---
        url : str
        name : str
        download_type :
        - basic
        - serial_chunked
        - parralel_chunked
        filename : str
    """

    def __init__(
        self,
        url: str,
        filename: str,
        name: str,
        dl_type='basic',
        download_folder: str = '.',
        *,
        chunk_size: int = 8192,
        user_agent: str = DEFAULT_USER_AGENT,
        session: Optional[requests.Session] = None,
        nb_split: int = DEFAULT_SPLIT_COUNT,
        split_size: int = -1,
        on_end: Optional[Action] = None,
    ):

        self.url: str = url
        self.name: str = name
        self.type: download_methods.METHODS = dl_type
        self._filename: str = filename

        self.chunk_size: int = chunk_size

        self.download_folder: str = download_folder

        self.nb_split: int = nb_split
        self.progress = 0
        # TODO:
        # self.resumable = False
        self.size = -1
        self.session = session

        self.speed = 0
        self.started = False
        # not used for now
        # self.adaptative_chunk_size = kwargs.get('adaptative_chunk_size', False)
        self.pause_time: int = 1
        self.last = 0
        self.last_time: int = time.time()
        self.status = ""

        self.event = threading.Event()
        self.split_size = split_size
        self.user_agent = user_agent
        self.on_end: Optional[Action] = on_end

        # download method handling
        if isinstance(dl_type, str):
            self.download_method = download_methods.methods.get(
                dl_type)
        else:
            raise Exception("str exptected")
        if self.download_method is None:
            raise Exception(
                f"""type not available : {dl_type} not found
        types are {list(download_methods.methods.keys())}"""
            )

        self.has_error: bool = False

        self.lock = threading.RLock()
        self.file: Optional[io.BytesIO] = None
        self.sanitize()

    def __repr__(self):
        return f'<Download {self.url}>'

    def init_file(self):
        self.file = open(self.filename, 'wb')

    def _size(self):
        if self.size == 0:
            return self.progress
        return self.size

    def init_size(self):
        size = 0
        while size == 0 and not self.is_stopped():
            size, p = utils.get_size(self.url, self.session)
            if size == 0:
                print('getting size failed | error {} | -> retrying'.format(p))

        self.size = size

    def little(self):
        r = {
            "name": self.name,
            "url": self.url,
            "progress": self.get_progression(),
            "size": self.size,
            "speed": self.get_speed(),
            "status": self.get_status(),
        }
        if self.origin_url != '':
            r["origin"] = self.origin_url
        return r

    def is_paused(self):
        return self.status == Status.PAUSED

    def is_finished(self):
        return self.status == Status.FINISHED

    def is_stopped(self):
        return self.status == Status.STOPPED

    def get_progression(self):
        try:
            return (self.progress / self.size) * 100
        except:
            return 0

    def finish(self):
        self.progress = self.size
        self.status = Status.FINISHED
        self.file.close()

    def update(self, progress):
        self.progress = progress

    def pause(self):
        self.status = Status.PAUSED

    def resume(self):
        self.status = Status.DOWNLOADING

    def stop(self):
        self.status = Status.STOPPED
        self.stopped[0] = True
        self.event.set()

    def get_speed(self):
        if time.time() - self.last_time >= 1:
            self.speed = (self.progress - self.last) / \
                (time.time() - self.last_time)
            self.last_time = time.time()
            self.last = self.progress
        return self.speed

    def dump_progress(self):  # not working
        raise Exception('Broken')

    def dump(self):  # not working
        raise Exception('Broken')

    @property
    def filename(self):
        return os.path.join(self.download_folder, self._filename)

    @filename.setter
    def filename(self, name: str):
        self._filename = name

    def sanitize(self):
        for char in TO_REMOVE:
            self._filename = self._filename.replace(char, '')

    def download(self, action=None):
        self.download_method(self, action, self.session)

    def write_at(self, at: int, data: bytes):
        with self.lock:
            self.file.seek(at)
            self.file.write(data)
            self.progress += len(data)
        return at + len(data)
