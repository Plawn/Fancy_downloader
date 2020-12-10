"""
Lib making downloading file easy
"""


import os
import threading
import time
from typing import Dict, List, Optional, Tuple

from . import utils
from .constants import TIME_BETWEEN_DL_START, TO_REMOVE, Status
from .download import Download
from .utils import Action

# # # # # # # # # # # # # # # # # # # # # CLASSs# # # # # # # # # # # # # # # # # # # # # #


class DownloadContainer:
    """
    A download container contains multiples downloads :
        An Action can be executed on start and on end
    """

    def __init__(
        self,
        name: str,
        downloads: List[Download],
        download_folder: str = '.',
        **kwargs
    ):
        self.downloads: List[Download] = []
        self.name = name
        self.download_folder = download_folder

        self.end_func = kwargs.get('end_func')
        self.f_args = kwargs.get('f_args')
        self.size = -1
        self.progress = 0
        self.speed = 0
        self.event = threading.Event()
        self.type = 'Container'
        self.size_set = False
        self.append(*downloads)

        self.finished = False
        self.done = False

        self.end1 = utils.End_action(self.__add_finished)
        self.end_action = kwargs.get('end_action')
        self.on_start = kwargs.get('begin_action')
        self._filename = kwargs.get('filename', 'file')
        self.threads = []

        self.statut: str = ''
        self.custom_status = ""
        self.custom_status_act = False
        self.finishedd = 0

        self.sanitize()

    def __iter__(self):
        for dl in self.downloads:
            yield dl

    def __repr__(self):
        return str({"name": self.name, 'downloads': self.downloads})

    def _size(self):
        if self.size == 0:
            return self.progress
        else:
            return self.size

    def set_filename(self, name: str) -> None:
        self._filename = name

    def set_status(self, string):
        self.custom_status = string
        self.custom_status_act = True

    def get_status(self):
        if self.custom_status_act:
            return self.custom_status
        return self.statut

    def get_progression(self) -> float:
        self.progress = 0
        to_dl: int = 0
        dled: int = 0
        for dl in self.downloads:
            to_dl += dl._size()
            dled += dl.progress
        if to_dl > 0:
            self.progress = (dled / to_dl) * 100
        else:
            self.progress = 0
        return self.progress

    def finish(self):
        self.finished = True
        self.statut = Status.FINISHED

    def stop(self):
        self.statut = Status.STOPPED
        for dl in self.downloads:
            dl.stop()

    def pause(self):
        self.statut = Status.PAUSED
        for dl in self.downloads:
            dl.pause()

    def resume(self):
        self.statut = Status.DOWNLOADING
        for dl in self.downloads:
            dl.resume()

    def get_speed(self):
        self.speed = 0
        for dl in self.downloads:
            self.speed += dl.get_speed()
        return self.speed

    @property
    def filename(self):
        return os.path.join(self.download_folder, self.name, self._filename)

    @filename.setter
    def filename(self, name: str):
        self._filename = name

    def get_size(self):
        if not self.size_set:
            self.size = 0
            for dl in self.downloads:
                if dl.size != -1:
                    self.size += dl._size()
                    self.size_set = True
                else:
                    self.size_set = False
        return self.size

    def sanitize(self):
        for char in TO_REMOVE:
            self._filename = self._filename.replace(char, '')
            self.name = self.name.replace(char, '')

    # container stuff
    def __add_finished(self):
        self.finishedd += 1
        self.event.set()

    def __prepare_actions(self, *actions: Action):
        # TODO: really necessary ?
        for action in actions:
            if action is not None:
                for i in range(len(action.args)):
                    if 'filename' in action.args[i]:
                        action.args[i] = self.downloads[int(
                            utils.extract_nb(action.args[i]))].filename
                    elif 'output' in action.args[i]:
                        action.args[i] = self.filename
                    elif 'self' in action.args[i]:
                        action.args[i] = self

    def _prepare_actions(self):
        for dl in self.downloads:
            self._prepare_download(dl)
        self.__prepare_actions(self.end_action, self.on_start)

    def _prepare_folder(self):
        try:
            os.mkdir(os.path.join(self.download_folder, self.name))
        except:
            # TODO: better error handling
            pass

    def download(self):
        self._prepare_folder()
        self._prepare_actions()
        if self.on_start is not None:
            self.on_start()

        dls = len(self.downloads)
        self.statut = Status.DOWNLOADING
        for dl in self.downloads:
            t = threading.Thread(target=dl.download, args=(self.end1,))
            t.start()
            self.threads.append(t)
            time.sleep(TIME_BETWEEN_DL_START)
        WAIT_TIME = 60
        while not self.done:
            self.event.wait(WAIT_TIME)
            if self.finishedd == dls:
                self.done = True
                if self.end_action is not None and not self.is_stopped():
                    self.end_action()
            self.event.clear()

        for t in self.threads:
            t.join()
        self.finish()

    def is_stopped(self):
        return self.statut == Status.STOPPED

    def is_paused(self):
        return self.statut == Status.PAUSED

    def _prepare_download(self, d_obj: Download):
        d_obj.download_folder = os.path.join(self.download_folder, self.name)

    def append(self, download: Download):
        if isinstance(download, Download):
            self.downloads.append(download)
            self._prepare_download(download)
        else:
            raise Exception('Invalid type, expexted Download instance')
