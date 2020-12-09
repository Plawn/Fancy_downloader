from abc import ABC, abstractstaticmethod
from typing import Optional
import requests
from ..download import Download


class DownloadMethod(ABC):
    @abstractstaticmethod
    def download(d_obj: Download, end_action=None, session: Optional[requests.Session] = None):
        pass

    @abstractstaticmethod
    def dump_progress(d_obj: Download, filename: str) -> None:
        pass

    @abstractstaticmethod
    def load_progress(filename: str):
        pass
