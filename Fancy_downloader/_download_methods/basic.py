from Fancy_downloader.utils import Split
from __future__ import annotations

from typing import Optional, TYPE_CHECKING

import requests

from .interface import DownloadMethod
from .utils import get_chunk

if TYPE_CHECKING:
    from ..download import Download


class BasicDownload(DownloadMethod):

    @staticmethod
    def download(d_obj: Download, end_action=None, session: Optional[requests.Session] = None):
        """Downloads a file using a single connection in a single chunk
        """
        d_obj.init_size()
        d_obj.init_file()

        get_chunk(d_obj.url, Split(0, d_obj.size), d_obj, session)
        if end_action != None:
            end_action()
        d_obj.finish()
        return True

    def dump_progress(d_obj: Download, filename: str) -> None:
        return super().dump_progress(filename)
