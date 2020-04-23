from ansibleapi import AnsibleAPI
import os
import textwrap
import time
import multiprocessing
import queue
import kivy.clock


class EndpointManager():

    def __init__(self, provider_id, storage):
        self.provider_id = provider_id
        self.storage = storage
        self.subprocess = None
        self.subprocess_status = None
        self.subprocess_queue = multiprocessing.Queue()
        if self.provider_id == "mullvad":
            self.endpoints_path = os.path.join(self.storage, 'relays.json')
            self.endpoints_path_old = os.path.join(self.storage, 'relays_old.json')
        elif self.provider_id == "privateinternetaccess":
            self.endpoints_path = os.path.join(self.storage, 'endpoints.xml')
            self.endpoints_path_old = os.path.join(self.storage, 'endpoints_old.xml')
        else:
            raise ValueError("invalid provider ID: {}".format(provider_id))

    def days_old(self, path):
        if os.path.isfile(path):
            return (time.time()-os.stat(path).st_mtime)/60/60/24
        else:
            return 10000.0

    def download_endpoint_list(self, messages):
        """Download the list of VPN servers if needed. Returns True if successful."""
        mullvad_dl = textwrap.dedent('''
        - name: Download Mullvad file relays.json
          hosts: localhost
          tasks:
          - name: Download relays.json
            uri:
              # API from https://github.com/mullvad/mullvadvpn-app/blob/master/update-relays.sh
              url: https://api.mullvad.net/rpc/
              method: POST
              body_format: json
              body: '{"jsonrpc": "2.0", "id": "0", "method": "relay_list_v3"}'
              dest: "{{ relays_path }}"
        ''')
        cache_days_best = 3.0  # after X days we try to update the cached endpoint data
        cache_days_max = 30.0  # if download fails, use old version unless older than X
        messages.put("s=started")
        cache_age = self.days_old(self.endpoints_path)
        log_str = f"{self.provider_id} file ({self.endpoints_path}) is {cache_age:0.2f} days old, "
        if cache_age < cache_days_best:
            messages.put("m=" + log_str + f"less than {cache_days_best:0.2f}; using cached version")
            messages.put("s=done_success")
            return True
        messages.put("m=" + log_str + f"more than {cache_days_best:0.2f}; updating")
        if os.path.isfile(self.endpoints_path):
            os.replace(self.endpoints_path, self.endpoints_path_old)  # back up cached version
        success = False
        messages.put("s=downloading")
        if self.provider_id == "mullvad":
            a = AnsibleAPI()
            a.run(
                playbook = mullvad_dl,
                facts = {
                    'relays_path': self.endpoints_path,
                },
            )
            if a.recap['failed'] > 0:
                messages.put("m==== begin Ansible output ===")
                messages.put("m=" + a.log, end='')
                messages.put("m====== end Ansible output ===")
            success = a.result == 0 and a.recap['failed'] == 0
        elif self.provider_id == "privateinternetaccess":
            time.sleep(15)  # just testing
        if not success and os.path.isfile(self.endpoints_path):
            os.remove(self.endpoints_path)  # delete failed download
        if os.path.isfile(self.endpoints_path_old):
            if os.path.isfile(self.endpoints_path):  # new version exists - keep it
                os.remove(self.endpoints_path_old)
            else:  # no new version - keep old one
                os.replace(self.endpoints_path_old, self.endpoints_path)
        cache_age = self.days_old(self.endpoints_path)
        messages.put(f"m=download {'succeeded' if success else 'failed'}; {self.provider_id} file is {cache_age:0.2f} days old")
        if cache_age < cache_days_max:
            messages.put("s=done_success")
            return True
        messages.put("s=done_failed")
        return False

    def multiprocess_download(self):
        """Calls download_endpoint_list() in another process. Returns immediately."""
        if self.subprocess is not None:
            print(f"{self.provider_id} file download already in progress")
            return
        self.subprocess = multiprocessing.Process(
            target = self.download_endpoint_list,
            args = (self.subprocess_queue,)
        )
        self.subprocess_status = "starting"
        self.subprocess.start()
        kivy.clock.Clock.schedule_interval(self.get_messages, 0.3)  # call every X seconds
    
    def get_messages(self, *args):
        try:
            while True:
                m = self.subprocess_queue.get_nowait()
                if m.startswith("s="):
                    self.subprocess_status = m[2:]
                    if self.subprocess_status.startswith("done"):
                        self.subprocess = None
                        return False  # cancel scheduled get_messages()
                else:
                    assert(m.startswith("m="))
                    print(m[2:])
        except queue.Empty:
            pass
        return True  # call get_messages() again in X seconds