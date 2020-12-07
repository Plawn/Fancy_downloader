from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List, Optional, TYPE_CHECKING, Tuple
from functools import lru_cache
import requests

if TYPE_CHECKING:
    from .Fancy_downloader import Download

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
    return (int(res.headers.get('content-length', 0)), res)


def sm_split(sizeInBytes: int, numsplits: int, offset: int = 0) -> List[Split]:
    if numsplits <= 1:
        return Split(0, sizeInBytes)
    lst = []
    i = 0
    lst.append(Split(i + offset, offset + int(round(1 + i *
                                                    sizeInBytes/(numsplits*1.0) + sizeInBytes/(numsplits*1.0)-1, 0))))
    for i in range(1, numsplits):
        lst.append(Split(offset + int(round(1 + i * sizeInBytes/(numsplits*1.0), 1)), offset +
                         int(round(1 + i * sizeInBytes/(numsplits*1.0) + sizeInBytes/(numsplits*1.0)-1, 0))))
    return lst


def extract_int(string: str) -> str:
    return ''.join(i for i in string if i in '0123456789')


def prepare_name(url: str) -> str:
    splited = url.split('/')
    resized = ''
    try:
        resized = splited[-1][:20] + '.' + splited[-1].split('.')[1]
    except:
        resized = splited[-1][:30]
    return resized


def get_and_retry(url: str, split: Split, d_obj: Optional[Download] = None, session: Optional[requests.Session] = None):
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
    session: Optional[requests.Session] = None
) -> bool:
    response = get_and_retry(url, split, d_obj, session)
    at = split.start
    for data in response.iter_content(chunk_size=d_obj.chunk_size):
        if not d_obj.is_stopped():
            at = d_obj.write_at(at, data)
            if d_obj.is_paused():
                d_obj.event.wait(d_obj.pause_time)
        else:
            return False
    return True
