import providers.endpointmanager
from ansibleapi import AnsibleAPI
import os.path
import textwrap
import time

class Privateinternetaccess(providers.endpointmanager.EndpointManagerBase):
    """Provider-specific methods. Note class name must be Titlecase of provider_id.
    """

    def __init__(self, storage):
        super().__init__(storage)
        self.endpoints_path = os.path.join(storage, 'pia_servers.xml')
        self.endpoints_path_old = os.path.join(storage, 'pia_servers_old.xml')
        self.display_name = 'Private Internet Access'
        self.website = 'privateinternetaccess.com'
        self.url = 'https://www.privateinternetaccess.com/'
        self.credentials = [
            { 'user': {
                'hint_text': 'Username',
                'helper_text': 'Usually has the form: p1234567',
                'helper_text_mode': 'on_focus',
                'required' : True,
            }},
            { 'password': {
                'hint_text': 'Password',
                'password': True,
                'password_mask': '*',  # '●' is not displayed correctly
                'required' : True,
            }},
            { 'comment': {
                'hint_text': 'Comment (optional)',
            }},
        ]
    
    def download_endpoints(self, messages):
        playbook = textwrap.dedent('''
        - name: Download Private Internet Access servers list
          hosts: localhost
          tasks:
          - name: Download
            uri:
              # API from pia-nm.sh on https://www.privateinternetaccess.com/pages/client-support/ubuntu-openvpn
              # FIXME: convert to Ansible: curl -Ss "https://www.privateinternetaccess.com/vpninfo/servers?version=24" | head -1
        ''')
        time.sleep(30)  # just testing
        return False  # for testing, this always fails

    def phonebook_from_provider_list(self):
        pass
