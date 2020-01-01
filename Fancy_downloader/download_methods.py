import threading
import time

import requests

from . import Fancy_downloader as dl
from . import utils
from . import tokens
from .utils import get_chunk


def serial_chunked_download(d_obj, end_action=None, session: requests.Session = None, start=0, end=0):
    """Downloads a file using a single connection getting a chunk at a time
    """
    splits = None
    if start == 0 and end == 0:
        d_obj.init_size()
        d_obj.init_file()
        nb_split = 0
        if d_obj.split_size != -1:
            nb_split = int(d_obj.size / d_obj.split_size) + 1
        else:
            nb_split = d_obj.nb_split
        splits = utils.sm_split(d_obj.size, nb_split)
    else:
        nb_split = int(d_obj.size / d_obj.split_size) + 1
        splits = utils.sm_split(end - start, nb_split, start)

    for split in splits:
        get_chunk(d_obj.url, split, d_obj, session)
        if d_obj.has_error or d_obj.is_stopped():
            return False

    if end_action != None:
        end_action()
    if end == 0 and start == 0:
        d_obj.finish()
    return True


def parralel_chunked_download(d_obj, end_action=None):
    """Downloads a file using multiple connections
    """
    d_obj.init_size()
    d_obj.init_file()
    
    splits = utils.sm_split(d_obj.size, d_obj.nb_split)
    threads = []
    for split in splits:
        t = threading.Thread(target=get_chunk, args=(d_obj.url, split, d_obj))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    if d_obj.has_error:
        return False
    if end_action != None:
        end_action()
    d_obj.finish()
    return True


def basic_download(d_obj, end_action=None, session: requests.Session = None):
    """Downloads a file using a single connection in a single chunk
    """
    d_obj.init_size()
    d_obj.init_file()

    get_chunk(d_obj.url, f"{0}-{d_obj.size}", d_obj, session)
    if end_action != None:
        end_action()
    d_obj.finish()
    return True


def serial_parralel_chunked_download(d_obj, end_action=None, session: requests.Session = None):
    """Downloads a file using multiple connections and multiple chunks per connection
    """
    d_obj.init_size()
    d_obj.init_file()

    size = d_obj.size
    splits = utils.sm_split(size, d_obj.nb_split)
    threads = []
    end_action1 = None
    for split in splits:
        l = split.split('-')

        start, end = int(l[0]), int(l[1])
        t = threading.Thread(target=serial_chunked_download,
                             args=(d_obj, end_action1, session, start, end))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    if d_obj.has_error:
        return False
    if end_action != None:
        end_action()
    d_obj.finish()
    return False


METHODS = {
    "serial_chunked": serial_chunked_download,
    "parralel_chunked": parralel_chunked_download,
    "basic": basic_download,
    "serial_parralel_chunked": serial_parralel_chunked_download
}
