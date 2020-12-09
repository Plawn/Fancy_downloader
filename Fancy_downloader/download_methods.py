
from __future__ import annotations
from dataclasses import dataclass
from .data_struct import Chunk, DownloadProgressSave
import threading
from typing import TYPE_CHECKING, Literal, Optional, Union

import requests

from . import utils
from .utils import Action, Split, get_chunk

if TYPE_CHECKING:
    from .download_container import Download


def serial_chunked_download(
    d_obj: Download,
    end_action: Optional[Action] = None,
    session: Optional[requests.Session] = None,
    progress_data: Optional[dict] = None,
    *,
    start: int = 0,
    end: int = 0,
) -> bool:
    """Downloads a file using a single connection getting a chunk at a time
    """
    splits = None
    if start == 0 and end == 0:
        d_obj.init_size()
        d_obj.init_file([Chunk(0, d_obj.size, -1)])
        nb_split: int = 0
        if d_obj.split_size != -1:
            nb_split = int(d_obj.size / d_obj.split_size) + 1
        else:
            nb_split = d_obj.nb_split
        splits = utils.sm_split(d_obj.size, nb_split)
    else:
        nb_split = int(d_obj.size / d_obj.split_size) + 1
        splits = utils.sm_split(end - start, nb_split, start)

    for split in splits:
        get_chunk(d_obj.url, split, d_obj, 0, session)
        if d_obj.has_error or d_obj.is_stopped():
            return False

    if end_action is not None:
        end_action()
    if end == 0 and start == 0:
        d_obj.finish()
    return True


def parralel_chunked_download(
    d_obj: Download,
    end_action: Optional[Action] = None,
    session: Optional[requests.Session] = None,
) -> bool:
    """Downloads a file using multiple connections
    """
    d_obj.init_size()
    splits = utils.sm_split(d_obj.size, d_obj.nb_split)
    d_obj.init_file([Chunk(s.start, s.end, -1) for s in splits])

    threads = []
    for i, split in enumerate(splits):
        t = threading.Thread(
            target=get_chunk,
            args=(d_obj.url, split, d_obj, i, session)
        )
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    if d_obj.has_error:
        return False
    if end_action is not None:
        end_action()
    d_obj.finish()
    return True


def basic_download(
    d_obj: Download,
    end_action: Optional[Action] = None,
    session: Optional[requests.Session] = None,
    *,
    progress_data: Optional[DownloadProgressSave] = None,
) -> bool:
    """Downloads a file using a single connection in a single chunk
    """
    split = None
    if progress_data is None:
        d_obj.init_size()
        d_obj.init_file([
            Chunk(0, d_obj.size, -1)
        ])
        split = Split(0, d_obj.size)
    else:
        d_obj.init_file()
        split = Split(progress_data.chunks[0].last, d_obj.size)
    get_chunk(d_obj.url, split, d_obj, 0, session)
    if end_action is not None:
        end_action()
    d_obj.finish()
    return True


def serial_parralel_chunked_download(
    d_obj: Download,
    end_action: Optional[Action] = None,
    session: Optional[requests.Session] = None,
    progress_data=None
) -> bool:
    """Downloads a file using multiple connections and multiple chunks per connection
    """
    d_obj.init_size()
    d_obj.init_file()

    size = d_obj.size
    splits = utils.sm_split(size, d_obj.nb_split)
    threads = []
    end_action1 = None
    for split in splits:
        t = threading.Thread(
            target=serial_chunked_download,
            args=(d_obj, end_action1, session),
            kwargs={'start': split.start, 'end': split.end},
        )
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


methods = {
    "serial_chunked": serial_chunked_download,
    "parralel_chunked": parralel_chunked_download,
    "basic": basic_download,
    "serial_parralel_chunked": serial_parralel_chunked_download
}

METHODS = Literal["serial_chunked", "parralel_chunked",
                  "basic", "serial_parralel_chunked"]

methodsType = Union[serial_chunked_download, parralel_chunked_download,
                    basic_download, serial_chunked_download]


def get_method(method_name: str) -> methodsType:
    if isinstance(method_name, str):
        method = methods.get(method_name)
        if method is not None:
            return method
        else:
            raise Exception(
                f"""type not available : {method_name} not found""")
    else:
        raise Exception(f'str expeted | got {method_name}')
