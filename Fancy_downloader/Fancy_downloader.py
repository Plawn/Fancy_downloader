"""
Lib making downloading file easy
"""


import json
import os
import threading
import time

import requests

from . import utils
from . import download_methods
from . import constants as status

__version__ = 0.2

Action = utils.Action
End_action = utils.Action
Begin_action = utils.Action


CHUNK_SIZE = 65556
MAX_RETRY = 10
TIME_BETWEEN_DL_START = 0.1
SUCCESS_CODES = (200, 206)
TO_REMOVE = (',', ';', '&', "'", '/', ')', '(')

User_Agent = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36"
}


# # # # # # # # # # # # # # # # # # # # # CLASSs# # # # # # # # # # # # # # # # # # # # # #


class Download:
    """
    An object which can be downloaded later on :
    args :
        url :
        name : (displayed)
        type :
        ---o basic
        ---o serial_chunked
        ---o parralel_chunked
        filename : (name of the file (often name + extension))

    """

    def __init__(self, url: str, name: str, *args, **kwargs):
        self.url = url
        self.name = name
        resized = utils.prepare_name(url)
        self.chunk_size = kwargs.get('chunk_size', 8192)
        self._filename = kwargs.get('filename', resized)
        self.download_folder = kwargs.get('download_folder', '.')

        self.nb_split = kwargs.get('splits', 5)
        self.progress = [0]
        self.resumable = kwargs.get('resumable', False)
        self.size = -1
        self.session = kwargs.get('session')
        self.finished = False

        self.speed = 0
        self.started = False
        self.adaptative_chunk_size = kwargs.get('adaptative_chunk_size', False)
        self.pause_time = 1
        self.last = 0
        self.last_time = time.time()
        self.status = ""
        self.thread_counter = kwargs.get('thread_counter')
        self.type = kwargs.get('type', 'basic')
        self.event = threading.Event()
        self.split_size = kwargs.get('split_size', -1)
        self.d_ext = "json"
        self.dump_directory = kwargs.get('dump_directory', '')
        self.origin_url = kwargs.get('origin', '')
        self.user_agent = kwargs.get('user_agent', User_Agent)
        self.on_end = kwargs.get('on_end')

        # download method handling
        download_method_str = kwargs.get('type')
        if isinstance(download_method_str, str):
            self.download_method = download_methods.METHODS.get(
                download_method_str)
        else:
            raise Exception("str exptected")
        if self.download_method == None:
            raise Exception("type not available : {} not found\n types are {}".format(
                download_method_str, list(download_methods.METHODS.keys())))

        self.has_error = False

        self.lock = threading.RLock()
        self.file = None
        self.chunk_size = CHUNK_SIZE
        self.sanitize()

    def __repr__(self):
        return str({"name": self.name, "url": self.url[:20] + '...'})

    def init_file(self):
        self.file = open(self.filename(), 'wb')

    def _size(self):
        if self.size == 0:
            return self.progress[0]
        return self.size

    def init_size(self):
        size = 0
        while size == 0 and not self.is_stopped():
            size, p = utils.url_size(self.url, self.session)
            if size != 0:
                continue
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
        return self.status == status.PAUSED

    def is_finished(self):
        return self.finished

    def is_stopped(self):
        return self.status == status.STOPPED

    def get_progression(self):
        try:
            return (self.progress[0] / self.size) * 100
        except:
            return 0

    def finish(self):
        self.finished, self.progress = True, [self.size]
        self.status = status.FINISHED
        self.file.close()

    def update(self, progress): self.progress[0] = progress

    def pause(self):
        self.status = status.PAUSED

    def resume(self):
        self.status = status.DOWNLOADING

    def stop(self):
        self.status = status.STOPPED
        self.stopped[0] = True
        self.event.set()

    def get_speed(self):
        if time.time() - self.last_time >= 1:
            self.speed = (self.progress[0] - self.last) / \
                (time.time() - self.last_time)
            self.last_time = time.time()
            self.last = self.progress[0]
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

    def write_at(self, at, data):
        with self.lock:
            self.file.seek(at)
            self.file.write(data)
            self.progress[0] += len(data)
        return at + len(data)


class Download_container:
    """
    A download container contains multiples downloads :
        An Action can be executed on start and on end
    """

    def __init__(self, *args, **kwargs):
        self.downloads = []
        downloads = kwargs.get('downloads', [])
        self.name = kwargs.get('name', 'unnamed')
        self.size = -1
        self.url = kwargs.get('url', '')
        self.progress = 0
        self.speed = 0
        self.end_func = kwargs.get('end_func')
        self.f_args = kwargs.get('f_args')
        self.download_folder = kwargs.get('download_folder', '.')
        self.append(*downloads)

        self.finished = False
        self.done = False
        self.event = threading.Event()
        self.end1 = utils.End_action(self.add_finished)
        self.end_action = kwargs.get('end_action')  # should be and End_action
        self.on_start = kwargs.get('begin_action')
        self._filename = kwargs.get('filename', 'file')
        self.paused = [False]
        self.progress = [0]
        self.origin_url = kwargs.get('origin')
        self.threads = []
        self.type = 'Container'
        self.size_set = False
        self.statut = ''
        self.custom_status = ""
        self.custom_status_act = False
        self.dls = 0
        self.finishedd = 0

        self.sanitize()

    def __iter__(self):
        for dl in self.downloads:
            yield dl

    def __repr__(self):
        return str({"name": self.name, 'downloads': self.downloads})

    def _size(self):
        if self.size == 0:
            return self.progress[0]
        else:
            return self.size

    def set_filename(self, name):
        self._filename = name

    def little(self):
        r = {
            "name": self.name,
            "url": self.url,
            "progress": self.get_progression(),
            "size": self.get_size(),
            "speed": self.get_speed(),
            "status": self.get_status(),
        }
        if self.origin_url is not None:
            r.update({"origin": self.origin_url})
        return r

    def set_status(self, string):
        self.custom_status = string
        self.custom_status_act = True

    def get_status(self):
        if self.custom_status_act:
            return self.custom_status
        return self.statut

    def get_progression(self):
        self.progress = 0
        to_dl = 0
        dled = 0
        for dl in self.downloads:
            to_dl += dl._size()
            dled += dl.progress[0]
        if to_dl > 0:
            self.progress = (dled / to_dl) * 100
        else:
            self.progress = 0
        return self.progress

    def finish(self):
        self.finished, self.progress = True, [self.size]
        self.statut = status.FINISHED

    # update
    def stop(self):
        self.statut = status.STOPPED
        for dl in self.downloads:
            dl.stop()

    def pause(self):
        self.statut = status.PAUSED
        for dl in self.downloads:
            dl.pause()

    def resume(self):
        self.statut = status.DOWNLOADING
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

    # dump & dump_progress

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
    def add_finished(self):
        self.finishedd += 1
        self.event.set()

    def _set1(self, action):
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
            self._auto_set(dl)
        self._set1(self.end_action)
        self._set1(self.on_start)

    def _prepare_folder(self):
        try:
            os.mkdir(os.path.join(self.download_folder, self.name))
        except:
            pass

    def download(self):
        self._prepare_folder()
        self._prepare_actions()
        if self.on_start is not None:
            self.on_start()

        self.dls = len(self.downloads)
        self.statut = status.DOWNLOADING
        for dl in self.downloads:
            t = threading.Thread(target=dl.download, args=(self.end1,))
            t.start()
            self.threads.append(t)
            time.sleep(TIME_BETWEEN_DL_START)

        while not self.done:
            self.event.wait(60)
            if self.finishedd == self.dls:
                self.done = True
                if self.end_action is not None and not self.is_stopped():
                    self.end_action()
            self.event.clear()

        for t in self.threads:
            t.join()
        self.finish()

    def is_stopped(self):
        return self.statut == status.STOPPED

    def is_paused(self):
        return self.statut == status.PAUSED

    def _auto_set(self, d_obj: Download):
        d_obj.download_folder = os.path.join(self.download_folder, self.name)

    def append(self, *args):
        for dl in args:
            if isinstance(dl, Download):
                self.downloads.append(dl)
                self._auto_set(dl)
