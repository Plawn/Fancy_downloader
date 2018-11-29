import requests
import threading, time, os
# from download_object import Download
from threading import Event
try:
    import Fancy_progressbar as bar
except:
    print('verbose disabled')

THREADS = 0

prox = [
        {"http":"54.37.9.224:80"},
        {"http":"91.121.87.63:3128"},
        {"http":"54.36.103.237:80"},
        {"http":"88.190.203.36:80"},
        ]
proxi_used = -1





# # # # # # # # # # # # # # # # # # # # # CLASSs# # # # # # # # # # # # # # # # # # # # # # 

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


def extract_nb(string):
    s = ""
    for i in string :
        if i in "0123456789":
            s += i
    return(s)

class Download_container:
    """
    A download container contains multiples downloads :
        was designed to dl YT videos and merge part using ffmpeg
    """
    def __init__(self, *args, **kwargs):
        self.downloads = []
        downloads = kwargs.get('downloads',[])
        self.name = kwargs.get('name', 'unnamed')
        self.size = -1
        self.progress = 0
        self.speed = 0
        self.end_func = kwargs.get('end_func')
        self.f_args = kwargs.get('f_args')
        self.verbose = kwargs.get('verbose', False)
        self.download_folder = kwargs.get('download_folder','.')
        self.family = bar.Progress_bar_family()
        self.append(*downloads)
        if self.verbose :
            self.bh = kwargs.get('bar_handler',bar.Progress_bar_handler())
            self.bh.append(self.family)
        self.finished = 0
        self.done = False
        self.event = Event()
        self.end1 = End_action(self.add_finished)
        self.end = kwargs.get('end_f') # should be and End_action
        self._filename = kwargs.get('filename','file')
        
        
        try :
            # better os.path.join i think
            os.mkdir(self.download_folder + '/' + self.name)
        except:
            pass
    def __iter__(self):
        for dl in self.downloads :
            yield dl
    def __repr__(self):
        return(str({"name":self.name, 'downloads':self.downloads}))
    
    def add_finished(self): 
        self.finished += 1
        self.event.set()
    
    def _set(self):
        if self.end is not None :
            for i in range (len(self.end.args)):
                if 'filename' in self.end.args[i]:
                    j = int(extract_nb(self.end.args[i]))
                    print('i:',i,'j:',j)
                    self.end.args[i] = self.downloads[j].filename()
                elif 'output' in self.end.args[i]:
                    self.end.args[i] = self.filename()
    def filename(self):
        return(self.download_folder + '/' + self.name + '/' + self._filename)
    
    def _auto_set(self, d_obj):
        d_obj.verbose = self.verbose
        d_obj.download_folder = self.download_folder + '/' + self.name
    
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
    def start(self):
        self._set()
        if self.verbose :
            self.bh.start()
        self.dls = len(self.downloads)
        for dl in self.downloads : threading.Thread(target=download, args=(dl, None, None, self.family, self.end1)).start()
        while not self.done :
            self.event.wait(60)
            if self.finished == self.dls :
                self.done = True
                if self.verbose:
                    self.bh.stop()
                if self.end is not None :
                    self.end()
            self.event.clear()
            
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
    





# # # # # # # # # # # # # # # # # # # # # CLASSs# # # # # # # # # # # # # # # # # # # # # # 



class End_action :
    """
    A function to execute, followed by its args
    """
    def __init__(self, func, *args):
        self.function = func
        self.args = [*args]
    def __call__(self): self.function(*self.args)





class Queue_downloader(threading.Thread):
    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self)
        self.queue = []
        self.event = threading.Event()
        self.done = False
        self.current_downloads = []
        self.nb_thread = [0]
        self.max_thread = kwargs.get('threads', 10)
        self.is_empty = False
        self.verbose = kwargs.get('verbose', False)
        self.family = bar.Progress_bar_family(taskname = 'Queue')
        self.barh = kwargs.get('bar_handler',bar.Progress_bar_handler())
        self.barh.append(self.family)
        self.auto_die = True if 'auto_die' in args else False
    
    def append(self, *d_obj, **kwargs):
        if len(d_obj) > 0 :
            self.queue.append(d_obj[0])
        l = kwargs.get('list',[])
        if len(l) > 0 :
            for i in l :
                self.queue.append(i)
        self.event.set()
    def run(self):
        if self.verbose :
            try:
                self.barh.start()
            except :
                pass
                #already started
        while not self.done :
            if len(self.queue) > 0:
                t = threading.Thread(target = download, args = (self.queue[0],self.nb_thread, self.event, self.family))
                t.start()
                
                # self.current_downloads.append(self.queue[0])
                self.queue.pop(0)
                self.family.current('{} | {} | {} | {}'.format(self.nb_thread, len(self.family.bars),THREADS,len(self.queue)))
            if self.nb_thread[0] < self.max_thread :
                self.event.set()
                # print('reste')
            if len(self.queue) == 0 :
                self.is_empty = True
            if self.is_empty and self.auto_die:
                self.stop()
            self.event.wait(60)
            self.event.clear()
            
    def stop(self):
        self.done = True
        self.barh.stop()
        self.event.set()
        

def url_size(url):
    return(int(requests.head(url, headers={'Accept-Encoding': 'identity'}).headers.get('content-length',0)))


def sm_split(sizeInBytes, numsplits):
    if numsplits <= 1:
        return ["0-%s" % sizeInBytes]
    lst = []
    for i in range(numsplits):
        if i == 0:lst.append('%s-%s' % (i, int(round(1 + i * sizeInBytes/(numsplits*1.0) + sizeInBytes/(numsplits*1.0)-1, 0))))
        else:lst.append('%s-%s' % (int(round(1 + i * sizeInBytes/(numsplits*1.0),1)), int(round(1 + i * sizeInBytes/(numsplits*1.0) + sizeInBytes/(numsplits*1.0)-1, 0))))
    return lst


def download(d_obj, nb_thread = None, event = None, family = None, end_action = None):
    if d_obj.type == 'serial_chunked': serial_chunked_download(d_obj, nb_thread, event, family, end_action)
    elif d_obj.type == 'parralel_chunked': parralel_chunked_download(d_obj, nb_thread, event, family, end_action)
    elif d_obj.type == 'basic': basic_download(d_obj, nb_thread, event, family, end_action)



def parralel_chunked_download(d_obj, nb_thread = None, event = None, family = None, end_action = None):
    if d_obj.started :
        print('download already started')
        return(False)
    else:
        d_obj.started = True
    if nb_thread != None :
        nb_thread[0] += 1 
    lock = threading.RLock()
    url = d_obj.url
    file_name = d_obj.filename()
    nb_split = d_obj.nb_split
    g_progress = d_obj.progress
    resumable = d_obj.resumable
    # thread_counter
    size = url_size(url)
    d_obj.size = size
    threads = []
    no = 0
    shared_status = g_progress
    family = None
    if d_obj.split_size != -1:
        nb_split = int(size / d_obj.split_size) + 1
    splits = sm_split(size, nb_split)
    if d_obj.verbose:
        barh = bar.Progress_bar_handler()
        barh.start()
        family = bar.Progress_bar_family(taskname = file_name)
        barh.append(family)
        # k = threading.Thread(target=top_bar_updater,args=(top_bar,d_obj))
        # k.start()
    f = open(file_name, 'wb')
    
    for split in splits :
        t = threading.Thread(target=get_chunk,args=(url, file_name, split, size, no, shared_status, family,f,d_obj,lock))
        t.start()
        threads.append(t)
        no += 1
        time.sleep(0.1)
    for t in threads:
        t.join()
    f.close()
    
    shared_status[0] = 100
    if d_obj.verbose:
        # k.join()
        shared_status[0] = -1
        # top_bar.update(100)
        family.finish()
        barh.stop()
        # print('finished')
    if nb_thread != None :
        nb_thread[0] -= 1
        event.set()
    if end_action is not None : end_action()
    if not d_obj.stopped[0] :
        d_obj.finish()
    
    


def get_chunk(url, file_name, split, total_length, no, shared_status, family, f, d_obj, lock):
    global proxi_used
    chunk_size = 4096
    indent = "  "
    l = split.split('-')
    start, end, dl  = int(l[0]), int(l[1]), 0
    verbose = False
    if family != None:
        bare = bar.Progress_bar('animated',taskname = str(no) )
        family.append(bare)
        verbose = True
    if proxi_used == -1 :
    	response = requests.get(url,headers={'Range': 'bytes={}'.format(split)}, stream = True)
    	proxi_used += 1
    else:
    	response = requests.get(url,headers={'Range': 'bytes={}'.format(split)}, stream = True)
    	proxi_used += 1
    point = start
    for data in response.iter_content(chunk_size = chunk_size):
        if not d_obj.stopped[0] :
            dl += len(data)
            shared_status[0] += len(data)
            with lock :
                f.seek(point)
                f.write(data)
            point += chunk_size
            if verbose :
                bare.update(( dl / (end - start) ) * 100)
            if d_obj.paused[0]:
                d_obj.event.wait(d_obj.pause_time)
        else:
            break
    if verbose:
        bare.delete()


def DL_multiple_files(urls,names):
    threads = []
    for url,name in zip(urls,names):
        t = threading.Thread(target=download_file,args=(url,name,5))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()


def serial_chunked_download(d_obj, nb_thread = None, event = None, family = None, end_action = None):
    if nb_thread != None :
        nb_thread[0] += 1
    def speed(d_obj, ba): ba.current(str(d_obj.get_speed()/1000)+'ko/s')
    size = url_size(d_obj.url)
    d_obj.size = size
    if d_obj.split_size != -1:
        nb_split = int(size / d_obj.split_size) + 1
    else:
        nb_split = d_obj.nb_split
    splits = sm_split(size, nb_split)
    f = open(d_obj.filename(), 'wb')
    no,barh = 0, None
    lock  = threading.RLock()
    verbose = False
    if d_obj.verbose and family == None :
        b = bar.Progress_bar('animated',taskname="dl",func = speed)
        b.f_args = (d_obj, b)
        barh = bar.Progress_bar_handler(b)
        barh.start()
        verbose = True
    if family != None :
        verbose = True
        b = bar.Progress_bar('animated',taskname="dl",func = speed)
        b.f_args = (d_obj, b)
        family.append(b)
        # print('here')
    i, n = 0, len(splits)
    for split in splits :
        if not d_obj.stopped[0] :
            get_chunk(d_obj.url, d_obj.filename(), split, d_obj.size, no, d_obj.progress, barh,f,d_obj,lock)
            if verbose :
                i += 1
                b.update((i/n)*100)
    if nb_thread != None :
        nb_thread[0] -= 1
        event.set()
    if end_action is not None : end_action()
    if not d_obj.stopped[0] :
        d_obj.finish()

def basic_download(d_obj, nb_thread = None, event = None, family = None, end_action = None):
    global THREADS
    if nb_thread != None :
        nb_thread[0] += 1
    THREADS += 1
    def speed(d_obj, ba): ba.current(str(d_obj.get_speed()/1000)+'ko/s')
    response = requests.get(d_obj.url, stream = True)
    d_obj.size = url_size(d_obj.url)
    f = open(d_obj.filename(), 'wb')
    
    chunk_size = 1024
    if d_obj.verbose and family == None:
        b = bar.Progress_bar('animated',taskname="dl",func=speed)
        b.f_args = (d_obj, b)
        barh = bar.Progress_bar_handler(b)
        barh.start()
        verbose = True
    if family != None :
        verbose = True
        b = bar.Progress_bar('animated',taskname="dl",func=speed)
        b.f_args = (d_obj, b)
        family.append(b)
        # print('appended')
    dl = 0
    for data in response.iter_content(chunk_size = chunk_size):
        if not d_obj.stopped[0]:
            f.write(data)
            d_obj.progress[0] += chunk_size
            if verbose:
                dl += len(data)
                b.update(( dl / d_obj._size()) * 100)
            if d_obj.paused[0] :
                d_obj.event.wait(d_obj.pause_time)
        else:
            break
        
    f.close()
    THREADS -= 1
    if verbose :
        b.delete()
    if nb_thread != None :
        # print(current_download.index(d_obj))
        nb_thread[0] -= 1
        event.set()
    if end_action is not None : end_action()

    if not d_obj.stopped[0] :
        d_obj.finish()




