from .interface import DownloadMethod
from .serial_chunked import SerialChunkedDownload
from .basic import BasicDownload

download_methods = {
    'serial_chunked': SerialChunkedDownload,
    'basic':BasicDownload
}
