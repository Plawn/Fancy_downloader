from abc import ABC
import requests


class DownloadMethod(ABC):
    @staticmethod
    def download(d_obj, end_action=None, session: requests.Session = None):
        pass

    @staticmethod
    def dump_progress(d_obj, filename: str) -> None:
        pass

    @staticmethod
    def load_progress(filename:str):
        pass
