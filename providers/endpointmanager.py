from ansibleapi import AnsibleAPI
import collections
import json
import os
import random
import textwrap
import time
# multiprocessing and threading both work, but multiprocessing is banned on
# iOS (https://github.com/kivy/kivy-ios); also Ansible is mostly I/O bound anyhow, not CPU
import threading
import queue
import kivy.clock


class EndpointManager():

    def __init__(self, provider_id, storage):
        self.provider_id = provider_id
        self.storage = storage
        self.thread = None
        self.status = ""
        self.phonebook = None
        self.thread_queue = queue.Queue()
        if self.provider_id == "mullvad":
            self.endpoints_path = os.path.join(self.storage, 'mullvad_relays.json')
            self.endpoints_path_old = os.path.join(self.storage, 'mullvad_relays_old.json')
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
        - name: Download Mullvad servers list
          hosts: localhost
          tasks:
          - name: Download
            uri:
              # API from https://github.com/mullvad/mullvadvpn-app/blob/master/update-relays.sh
              url: https://api.mullvad.net/rpc/
              method: POST
              body_format: json
              body: '{"jsonrpc": "2.0", "id": "0", "method": "relay_list_v3"}'
              dest: "{{ relays_path }}"
        ''')
        pirivateinternetaccess_dl = textwrap.dedent('''
        - name: Download Private Internet Access servers list
          hosts: localhost
          tasks:
          - name: Download
            uri:
              # API from pia-nm.sh on https://www.privateinternetaccess.com/pages/client-support/ubuntu-openvpn
              # FIXME: convert to Ansible: curl -Ss "https://www.privateinternetaccess.com/vpninfo/servers?version=24" | head -1
        ''')
        cache_days_best = 3.0  # after X days we try to update the cached endpoint data file
        cache_days_max = 30.0  # if download fails, use old version unless older than X
        cache_age = self.days_old(self.endpoints_path)
        log_str = f"{self.provider_id} file ({self.endpoints_path}) is {cache_age:0.2f} days old, "
        if cache_age < cache_days_best:
            messages.put("m=" + log_str + f"less than {cache_days_best:0.2f}; using cached version")
            messages.put(self.phonebook_from_provider_list())
            messages.put("s=done_succeeded")
            return True
        messages.put("m=" + log_str + f"more than {cache_days_best:0.2f}; updating")
        if os.path.isfile(self.endpoints_path):
            os.replace(self.endpoints_path, self.endpoints_path_old)  # back up cached version
        success = False
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
            #import math
            #total = 0
            #for i in range(200000000):
            #     total += math.sqrt(i)  # just testing; about 30 seconds on my laptop
            time.sleep(30)  # just testing
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
            messages.put(self.phonebook_from_provider_list())
            messages.put("s=done_succeeded")
            return True
        messages.put("s=done_failed")
        return False

    def phonebook_from_provider_list(self):
        """Read provider's endpoint data and convert to our provider-neutral 'phonebook'
        format, simplifying and stripping unused data. For Mullvad, phonebook (exported as
        JSON) was 15% the size of relays.json.
        """
        # notes on relays.json
        #   see also https://github.com/mullvad/mullvadvpn-app
        #   include_in_country:
        #     true for 155 of 173 WireGuard relays and 42 or 45 cities
        #     possibly "include this server as part of a country" [1]
        #   weight:
        #     possibly "load and preferability when in the process of picking random servers" [1]
        #     see `pick_random_relay` in mullvadvpn-app; I think relay with a weight of 200
        #       is twice as likely to get picked as a relay with a weight of 100
        #     "relay-selector.md" seems to confirm the above
        #   [1] https://github.com/mozilla-services/guardian-vpn-windows/blob/master/ui/src/JSONStructures/Server/Server.cs
        phonebook = {"version": 1, "providers": []}
        phonebook['providers'].append({
            'id': 'mullvad',
            'name': 'Mullvad VPN',
            'server_name_suffix': '.mullvad.net',
            'countries': [],
        })
        with open(self.endpoints_path) as f:
            endpoint_data = json.load(f)
        countries = phonebook['providers'][-1]['countries']
        for country in endpoint_data['result']['countries']:
            depth = 0  # mechanism to skip countries and cities with no applicable servers
            for city in country.get('cities', list()):
                depth = min(1, depth)
                for server in city.get('relays', list()):
                    if server.get('active', False) != True:
                        continue
                    if server.get('tunnels', dict()).get('wireguard', None) is None:
                        continue  # no WireGuard support here
                    assert len(server['tunnels']['wireguard']) == 1
                    if depth == 0:
                        countries.append({
                            'name': country['name'],
                            'code': country['code'].upper(),  # 2 capital letters (ISO 3166)
                            'cities': [],
                        })
                        cities = countries[-1]['cities']
                        depth = 1
                    if depth == 1:
                        cities.append({
                            'name': city['name'],
                            'servers': [],
                        })
                        servers = cities[-1]['servers']
                        depth = 2
                    servers.append({
                        'name': server['hostname'],  # does not contain 'server_name_suffix'
                        'weight': server['weight'],
                        'public_key': server['tunnels']['wireguard'][0]['public_key'],
                        'port_rages_wg_udp': [],  # WireGuard
                        #'port_rages_ov_udp':  # OpenVPN UDP ports
                        #'port_rages_ov_tcp':  # OpenVPN TCP ports
                    })
                    port_rages_wg_udp = servers[-1]['port_rages_wg_udp']
                    for range in server['tunnels']['wireguard'][0]['port_ranges']:
                        port_rages_wg_udp.append(range)  # [range[0], range[1]]
        return phonebook

    def prepare_phonebook(self):
        """Calls download_endpoint_list() in another process. Returns immediately."""
        if self.thread is not None and self.thread.is_alive():
            print(f"{self.provider_id} file download already in progress")
            return
        self.thread = threading.Thread(
            target = self.download_endpoint_list,
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
