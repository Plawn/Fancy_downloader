import time
from threading import Event

# 3 types :
# * serial_chunked
# * parralel_chunked
# * basic
class Download:
    """
    An object which can be downloaded later on :
    args :
        url :
        name : (displayed)
        type :
            * basic
            * serial_chunked
            * parralel_chunked
        filename : (name of the file (often name + extension))

    """
    
    
    def __init__(self,*args,**kwargs):
        self.url = kwargs.get('url','')
        try :
            resized = self.url.split("/")[-1][0:20] + '.' + self.url.split("/")[-1].split('.')[1]
        except:
            resized = self.url.split("/")[-1][0:30]
        self._filename = kwargs.get('filename',resized)
        self.download_folder = kwargs.get('download_folder','.')
        self.name = kwargs.get('name',resized)
        self.nb_split = kwargs.get('splits',5)
        self.progress = [0]
        self.resumable = kwargs.get('resumable',False)
        self.size = -1
        self.verbose = kwargs.get("verbose", False)
        self.paused = [False]
        self.stopped = [False]
        self.finished = False
        self.speed = 0
        self.started = False
        self.fast_download_enabled = kwargs.get('fast_download_enabled', False) # deprecated
        self.basic = kwargs.get('basic', False)
        self.pause_time = 1
        self.last = 0
        self.last_time = time.time()
        self.status = ""
        self.thread_counter = kwargs.get('thread_counter')
        self.type = kwargs.get('type', 'basic')
        self.event = Event()
        self.split_size = kwargs.get('split_size', -1)
        self.chunks = []
        self.d_ext = "json"
        self.dump_directory = kwargs.get('dump_directory','')
        self.origin_url = kwargs.get('origin','') 
    def _size(self):
        if self.size == 0:return(self.progress[0])
        else:return(self.size)
    def little(self):
        r = {
                "name"    :self.name,
                "url"     :self.url,
                "progress":self.get_progression(),
                "size"    :self.size,
                "speed"   :self.get_speed(),
                "status"  :self.get_status(),
            }
        if self.origin_url != '':r.update({"origin":self.origin_url})
        return(r)
    def __repr__(self):
        return(str({"name":self.name,"url":self.url[0:20]+'...'}))
    def get_status(self):
        if self.stopped[0]:return('stopped')
        if self.paused[0]: return('paused')
        if self.finished:  return('done')
        return("downloading")
    def get_progression(self):
        try :return((self.progress[0] / self.size)  * 100)
        except:return(0)
    def finish(self):
        self.finished, self.progress = True, [self.size]
    def update(self, progress): self.progress[0] = progress
    def stop(self):
        self.stopped = [True]
        self.event.set()
    def pause(self):self.paused = [True]
    def resume(self):self.paused = [False]
    def get_speed(self):
        if time.time() - self.last_time >= 1 :
            self.speed = (self.progress[0] - self.last) / (time.time() - self.last_time)
            self.last_time = time.time()
            self.last = self.progress[0]
        return(self.speed)
    def filename(self):return(self.download_folder + "/" + self._filename)
    def dump_progress(self):
        if self.type == "parralel_chunked":
            return(self.chunks)
        return(self.progress[0])
    def dump(self):
        with open('{}.{}'.format(self.filename(),self.d_ext), 'w') as f :
            f.write(json.dumps({
            "name":self.name,
            "url":self.url,
            "size":self.size,
            "progress":self.dump_progress(),
            "type":self.type,
        }, indent=4))
    def sanitize(self):
        to_remove = [',',';','&',"'"]
        for char in to_remove : 
            self._filename = self._filename.replace(char,'')




class Download_container:
    def __init__(self, *args, **kwargs):
        self.downloads = kwargs.get('downloads',[])
        self.name = kwargs.get('name', 'unnamed')
        self.size = -1
        self.progress = 0
        self.speed = 0
        self.end_func = kwargs.get('end_func')
        self.f_args = kwargs.get('f_args')
        self.verbose = kwargs.get('verbose', False)
        self.download_folder = kwargs.get('download_folder','.')
        # self.bh = kwargs.get()
    def __iter__(self):
        for dl in self.downloads :
            yield dl
    def __repr__(self):
        return(str({"name":self.name, 'downloads':self.downloads}))
    
    
    def _auto_set(self, d_obj):
        d_obj.verbose = self.verbose
        d_obj.download_folder = self.download_folder
    
    def append(self, *args, **kwargs):
        for dl in args :
            if isinstance(dl, Download):
                self.downloads.append(dl)
                self._auto_set(dl)
        for dl in kwargs.get('list',[]):
            self.downloads.append(dl)
            self._auto_set(dl)
    def get_progression(self):
        pass
    
    def get_speed(self):
        for dl in self.downloads: self.speed += dl.speed

    def get_size(self):
        for dl in self.downloads : self.size += dl.size
    def pause(self):
        for dl in self.downloads: dl.pause()
    def resume(self):
        for dl in self.downloads : dl.resume()
    def stop(self):
        for dl in self.downloads: dl.stop()
    def start(self, func):
        for dl in self.downloads : func(dl)
    def _size(self):
        if self.size == 0:return(self.progress[0])
        else:return(self.size)
    def little(self):
        r = {"name":self.name,
                "url":self.url,
                "progress":self.get_progression(),
                "size":self.size,
                "speed":self.get_speed(),
                "status":self.get_status(),
                }
        if self.origin_url != '':r.update({"origin":self.origin_url})
        return(r)
    