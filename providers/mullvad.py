from providers.endpointmanager import EndpointManagerBase
from ansibleapi import AnsibleAPI
import os.path
import textwrap
import json

class Mullvad(EndpointManagerBase):
    """Provider-specific methods. Note class name must be Titlecase of provider_id.
    """

    def __init__(self, storage):
        super().__init__(storage)
        self.endpoints_path = os.path.join(storage, 'mullvad_relays.json')
        self.endpoints_path_old = os.path.join(storage, 'mullvad_relays_old.json')
        self.display_name = 'Mullvad VPN'  # name shown in app
        self.website = 'mullvad.net'  # display, without https or www or unnecessary slashes
        self.url = 'https://mullvad.net/en/'  # full web address of provider's website
        self.credentials = [  # list of fields required to use the VPN (e.g. username, password); each field has a list of MDTExtField attributes (see https://kivymd.readthedocs.io/en/latest/components/text-field/index.html#kivymd.uix.textfield.MDTextField)
            { 'account': {
                'hint_text': 'Account number',
                'required' : True,
            }},
            { 'comment': {
                'hint_text': 'Comment (optional)',
            }},
        ]

    
    def download_endpoints(self, messages):
        playbook = textwrap.dedent('''
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
        a = AnsibleAPI()
        a.run(
            playbook = playbook,
            facts = {
                'relays_path': self.endpoints_path,
            },
        )
        if a.recap['failed'] > 0:
            messages.put("m==== begin Ansible output ===")
            messages.put("m=" + a.log, end='')
            messages.put("m====== end Ansible output ===")
        return a.result == 0 and a.recap['failed'] == 0

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
        phonebook = {'version': 1, 'providers': []}
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
                        'port_rages_wg_udp': [],  # 'wg' is WireGuard
                        #'port_rages_ov_udp':  # 'ov' is OpenVPN
                        #'port_rages_ov_tcp':  # 'ov' is OpenVPN
                    })
                    port_rages_wg_udp = servers[-1]['port_rages_wg_udp']
                    for range in server['tunnels']['wireguard'][0]['port_ranges']:
                        port_rages_wg_udp.append(range)  # [range[0], range[1]]
        return phonebook
