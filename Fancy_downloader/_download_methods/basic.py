from .interface import DownloadMethod
from .utils import get_chunk
import requests

class BasicDownload(DownloadMethod):

    @staticmethod
    def download(d_obj, end_action=None, session: requests.Session = None):
        """Downloads a file using a single connection in a single chunk
        """
        d_obj.init_size()
        d_obj.init_file()

        get_chunk(d_obj.url, f"{0}-{d_obj.size}", d_obj, session)
        if end_action != None:
            end_action()
        d_obj.finish()
        return True
