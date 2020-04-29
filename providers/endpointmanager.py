import importlib
import os
import time
# multiprocessing and threading both work, but multiprocessing is banned on
# iOS (https://github.com/kivy/kivy-ios); also Ansible is mostly I/O bound anyhow, not CPU
import threading
import queue
import kivy.clock


def EndpointManager(provider_id, storage):
    imported_module = importlib.import_module(f"providers.{provider_id}")  # dynamic import
    subclass = getattr(imported_module, provider_id.title())  # class name is Titlecase of provider_id
    instance = subclass(storage)
    instance.provider_id = provider_id
    return instance

def EndpointManagerList(storage):
    python_files = list()
    for f in sorted(os.listdir('providers')):  # providers/*.py files except endpointmanager.py
        if (os.path.isfile(os.path.join('providers', f)) and
                f.endswith('.py') and
                f != 'endpointmanager.py'):
            python_files.append(EndpointManager(f.replace('.py', ''), storage))
    return python_files


class EndpointManagerBase():
    """Base class for a provider-specific class. Don't instantiate this class.
    """

    def __init__(self, storage):
        self.thread = None
        self.status = ""
        self.phonebook = None
        self.thread_queue = queue.Queue()

    def days_old(self, path):
        if os.path.isfile(path):
            return (time.time()-os.stat(path).st_mtime)/60/60/24
        else:
            return 10000.0

    def download_endpoints_cached(self, messages):
        """Download the list of endpoints (VPN servers) if the on-disk copy is missing or
        old, then call phonebook_from_provider_list() and send the results back to UI
        thread.
        """
        cache_days_best = 3.0  # after X days we try to update the cached endpoint data file
        cache_days_max = 30.0  # if download fails, use old version unless older than X
        assert cache_days_best < cache_days_max
        cache_age = self.days_old(self.endpoints_path)
        log_str = f"{self.provider_id} file ({self.endpoints_path}) is {cache_age:0.2f} days old, "
        if cache_age >= cache_days_best:
            messages.put("m=" + log_str + f"more than {cache_days_best:0.2f}; updating")
            if os.path.isfile(self.endpoints_path):
                os.replace(self.endpoints_path, self.endpoints_path_old)  # back up cached version
            success = self.download_endpoints(messages)  # actual download in derived class
            if not success and os.path.isfile(self.endpoints_path):
                os.remove(self.endpoints_path)  # delete failed download
            if os.path.isfile(self.endpoints_path_old):
                if os.path.isfile(self.endpoints_path):
                    # both old and new versions exist; keep the new one
                    os.remove(self.endpoints_path_old)
                else:
                    # no new version; keep the old one
                    os.replace(self.endpoints_path_old, self.endpoints_path)
            cache_age = self.days_old(self.endpoints_path)
            dl_msg = "download succeeded" if success else "download failed"
            messages.put(f"m={dl_msg}; {self.provider_id} file is {cache_age:0.2f} days old")
        else:  # cache_age < cache_days_best
            messages.put("m=" + log_str + f"less than {cache_days_best:0.2f}; using cached version")
        if cache_age < cache_days_max:
            messages.put(self.phonebook_from_provider_list())
            messages.put("s=done_succeeded")
            return True
        messages.put("s=done_failed")
        return False

    def prepare_phonebook(self):
        """Calls download_endpoints_cached() in another process. Returns immediately."""
        if self.thread is not None and self.thread.is_alive():
            print(f"{self.provider_id} file download already in progress")
            return
        self.thread = threading.Thread(
            target = self.download_endpoints_cached,
            args = (self.thread_queue,)
        )
        self.status = "running"
        self.thread.start()
        kivy.clock.Clock.schedule_interval(self.get_messages, 0.3)  # call every X seconds
    
    def get_messages(self, *args):
        try:
            while True:
                m = self.thread_queue.get_nowait()
                if isinstance(m, str):
                    if m.startswith("s="):  # status update
                        self.status = m[2:]
                        if self.status.startswith("done"):
                            return False  # cancel scheduled get_messages()
                    else:  # debug message
                        assert(m.startswith("m="))
                        print(m[2:])
                else:  # phonebook update
                    self.phonebook = m
        except queue.Empty:
            pass
        return True
