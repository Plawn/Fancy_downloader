import Fancy_downloader as dl
import Fancy_progressbar as fp

url = 'https://download01.logi.com/web/ftp/pub/techsupport/gaming/lghub_installer.zip'


b = fp.ProgressBar('download', 'kill_when_finished', 'animated')

handle = fp.ProgressBarHandler([b])
handle.start()
d = dl.Download(url, 'test.zip', 'serial_chunked')
b.use_progress(d.get_progression)
d.download()
b.finish()
