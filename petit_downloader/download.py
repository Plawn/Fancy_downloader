from __future__ import annotations

import io
import ujson as json
import os
import threading
import time
from typing import Any, Dict, List, Optional
import dataclasses_json

import requests

from . import download_methods, utils
from .constants import (DEFAULT_SPLIT_COUNT, DEFAULT_USER_AGENT, TO_REMOVE,
                        Status)
from .data_struct import Chunk, DownloadProgressSave
from .utils import Action, MAX_RETRY

# struct for downlaoding file:
# 8 bytes as utf-8 encoded giving the size of the progress struct_size
# progress_struct encoded as json as base64 encoded bytes
# progress struct is updated on file_write
# rest of the file is the actual data
#
#
#


HEADER_LENGTH = 6


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
        dl_type: download_methods.METHODS = 'basic',
        download_folder: str = '.',
        *,
        chunk_size: int = 8192,
        user_agent: str = DEFAULT_USER_AGENT,
        session: Optional[requests.Session] = None,
        nb_split: int = DEFAULT_SPLIT_COUNT,
        split_size: int = -1,
        on_end: Optional[Action] = None,
        progress_data: Optional[DownloadProgressSave] = None,
    ):

        self.url: str = url
        self.name: str = name
        self.type: download_methods.METHODS = dl_type

        self.__filename: str = filename
        self.download_folder: str = download_folder

        self.chunk_size: int = chunk_size

        self.nb_split: int = nb_split

        self.size: int = progress_data.size if progress_data is not None else -1
        self.progress: int = 0 if progress_data is None else sum(
            s.last - s.start for s in progress_data.chunks)
        self.session = session

        self.speed = 0
        self.started = False
        # TODO: not used for now
        # self.adaptative_chunk_size = kwargs.get('adaptative_chunk_size', False)
        self.pause_time: int = 1
        self.last = 0
        self.last_time: int = time.time()
        self.status: Status = ""

        self.event = threading.Event()
        self.split_size = split_size
        self.user_agent = user_agent
        self.on_end: Optional[Action] = on_end

        self.download_method = download_methods.get_method(dl_type)
        self.has_error: bool = False

        self.lock = threading.RLock()
        self.file: Optional[io.BytesIO] = None

        # used to store progress data in order to dump the file
        self.progress_data: DownloadProgressSave = progress_data
        self.header_size = HEADER_LENGTH
        self.progress_file: Optional[io.TextIOWrapper] = None

    def __repr__(self):
        return f'<Download {self.url}>'

    def init_file(self, chunks: Optional[List[Chunk]] = None):
        self.progress_file = open(f'{self.filename}.json', 'w+')
        if chunks is not None:
            self.file = open(self.filename, 'wb')
            self.progress_data = DownloadProgressSave(
                self.url, self.__filename, self.size, self.name,
                self.type, chunks,
            )
        else:
            self.file = open(self.filename, 'rb+')

    def _size(self):
        if self.size == 0:
            return self.progress
        return self.size

    def init_size(self):
        failed = 0
        size = 0
        while size == 0 and failed < MAX_RETRY and not self.is_stopped():
            size, p = utils.get_size(self.url, self.session)
            if size == 0:
                # TODO: handle error here
                print('getting size failed | error {} | -> retrying'.format(p))
                failed += 1
        self.size = size

    def is_paused(self):
        return self.status == Status.PAUSED

    def is_finished(self):
        return self.status == Status.FINISHED

    def is_stopped(self):
        return self.status == Status.STOPPED

    def get_progression(self) -> float:
        if self.size != 0:
            return (self.progress / self.size) * 100
        return 0

    def finish(self):
        self.status = Status.FINISHED
        self.file.close()
        self.progress_file.close()

    def update(self, progress: float) -> None:
        self.progress = progress

    def slow(self) -> None:
        self.status = Status.SLOW

    def pause(self) -> None:
        self.status = Status.PAUSED
        self.file.close()
        self.progress_file.close()
        self.event.set()

    def resume(self) -> None:
        self.status = Status.DOWNLOADING
        self.event.clear()
        self.download()

    def cancel(self) -> None:
        self.status = Status.STOPPED
        self.file.close()
        self.progress_file.close()
        self.event.set()

    def get_speed(self) -> float:
        if time.time() - self.last_time >= 1:
            self.speed = (self.progress - self.last) / \
                (time.time() - self.last_time)
            self.last_time = time.time()
            self.last = self.progress
        return self.speed

    @property
    def filename(self) -> str:
        return os.path.join(self.download_folder, self.__filename)

    @filename.setter
    def filename(self, name: str) -> None:
        self.__filename = name

    def download(self, action: Optional[Action] = None):
        self.download_method(
            d_obj=self,
            end_action=action,
            session=self.session,
            progress_data=self.progress_data
        )

    def __save_progress(self, at: int, bytes_length: int, chunk_id: int):
        # basic save only for now
        # 6 is the number of bytes used to save the length of the metadata

        self.progress_data.chunks[chunk_id].last = at + bytes_length - 1
        # TODO: optimize writes
        self.progress_file.seek(0)
        self.progress_file.write(self.progress_data.to_json())

    def write_at(self, at: int, data: bytes, chunk_id: int):
        with self.lock:
            self.file.seek(at)
            self.file.write(data)
            self.__save_progress(at, len(data), chunk_id)
            self.progress += len(data)
        return at + len(data)


def from_save(d: dict) -> Download:
    """Loads a previous download from a save
    """
    data: DownloadProgressSave = DownloadProgressSave.from_dict(d)
    # TODO: handle download folder
    dl = Download(data.url, data.filename, data.name,
                  data.type, progress_data=data)

    return dl
