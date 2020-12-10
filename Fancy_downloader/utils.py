from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List, Optional, TYPE_CHECKING, Tuple
from functools import lru_cache
import requests

if TYPE_CHECKING:
    from .download_container import Download

RETRY_SLEEP_TIME = 0.3
MAX_RETRY = 10


class Action:
    """
    A function to execute, followed by its args
    """

    def __init__(self, func, *args):
        self.function = func
        self.args = [*args]

    def __call__(self):
        self.function(*self.args)


@dataclass
class Split:
    start: int
    end: int

    def as_range(self):
        return f'{self.start}-{self.end}'


def get_size(url: str, session: Optional[requests.Session] = None) -> Tuple[int, requests.Request]:
    requester = session or requests
    res = requester.head(url, headers={'Accept-Encoding': 'identity'})
    size = int(res.headers.get('content-length', 0))
    return size, res


def split(size: int, chunks_nb: int, offset: int = 0) -> List[Split]:
    size -= 1
    if chunks_nb == 1:
        return [Split(0, size)]
    chunk_size = size // chunks_nb
    l = [Split(
        offset + 0,
        offset + chunk_size
    )]
    l.extend(Split(
        offset + 1 + i * chunk_size,
        offset + (i + 1) * chunk_size)
        for i in range(1, chunks_nb - 1)
    )
    l.append(Split(
        (chunks_nb - 1) * chunk_size,
        size
    ))
    return l


# TODO: clean this
def prepare_name(url: str) -> str:
    splited = url.split('/')
    resized = ''
    try:
        resized = splited[-1][:20] + '.' + splited[-1].split('.')[1]
    except:
        resized = splited[-1][:30]
    return resized


def get_and_retry(
    url: str,
    split: Split,
    d_obj: Download,
    session: Optional[requests.Session] = None
) -> requests.Response:
    headers = {
        'Range': f'bytes={split.as_range()}'
    }
    done = False
    errors = 0
    requester = session or requests
    while not done:
        response = requester.get(url, headers=headers, stream=True)
        if response.status_code < 300:
            done = True
            return response
        else:
            # TODO:
            # better error handling
            errors += 1
            print(f"error retrying | error code {response.status_code}")
            # should be parameters
            time.sleep(RETRY_SLEEP_TIME)
            if errors == MAX_RETRY:
                print('Download canceled')
                d_obj.has_error = True
                d_obj.stop()
                raise Exception("Error max retry")


def get_chunk(
    url: str,
    split: Split,
    d_obj: Download,
    part_id: int,
    session: Optional[requests.Session] = None,
) -> bool:
    # TODO: should be ==
    if split.start >= split.end:
        return True
    response = get_and_retry(url, split, d_obj, session)
    at = split.start
    for data in response.iter_content(chunk_size=d_obj.chunk_size):
        if not d_obj.is_stopped():
            at = d_obj.write_at(at, data, part_id)
            if d_obj.is_paused():
                d_obj.event.wait(d_obj.pause_time)
        else:
            return False
    return True
