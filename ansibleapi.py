import os
import sys
import re
import itertools
import traceback
import tempfile
import contextlib
from io import StringIO
from tempfile import SpooledTemporaryFile
# must set environment vars *before*: from ansible.cli import CLI
os.environ['ANSIBLE_NOCOLOR'] = 'True'  # tty colors make log hard to parse
os.environ['ANSIBLE_LOCALHOST_WARNING'] = 'False'  # avoid warning, but doesn't seem to work
from ansible import context
from ansible.cli import CLI
from ansible.module_utils.common.collections import ImmutableDict
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager


class AnsibleAPI():

    def run(self, playbook, hosts=None, facts=None):
        """Run an Ansible playbook. Var 'playbook' can be a YAML string
        or, if it contains no newlines, a path to a playbook file.
        Var 'hosts' can be None (localhost only) or a list of hosts,
        such as ['server.example.com', '192.168.8.101']. Var 'facts' can be
        a dictionary of Ansible facts. After run(), var 'result' is 0 for
        success or no hosts matched, 2 for failures, or -1 for exception.
        Var 'log' is the full Ansible output or exception listing. Var
        'recap' is a dict of Ansible's "play recap" line.
        Example usage:
            a = AnsibleAPI()
            a.run("myplaybook.yml", {'upload_file': 'longexamplefilename.zip'})
            print("=== begin Ansible output ===")
            print(a.log, end='')
            print("===== end Ansible output ===")
            print("result = {}".format(a.result))
            for k in a.recap:  # 'ok', 'changed', 'failed', etc.
                print("recap[{}] = {}".format(k, a.recap[k]))
        """
        # Based on https://docs.ansible.com/ansible/latest/dev_guide/developing_api.html
        # and https://stackoverflow.com/a/57501942
        self.result = -1
        self.log = None
        self.recap = {'failed': 1}
        if hosts is None:
            hosts = list()
        if facts is None:
            facts = dict()
        loader = DataLoader()
        context.CLIARGS = ImmutableDict(
            tags = dict(),
            listtags = False,
            listtasks = False,
            listhosts = False,
            syntax = False,
            connection = 'ssh',
            module_path = None,
            forks = 100,
            remote_user = 'xxx',
            private_key_file = None,
            ssh_common_args = None,
            ssh_extra_args = None,
            sftp_extra_args = None,
            scp_extra_args = None,
            become = False,
            become_method = 'sudo',
            become_user = 'root',
            verbosity = True,
            check = False,
            start_at_task = None,
        )
        inventory_warnings = StringIO()  # capture "No inventory was parsed" warning
        with contextlib.redirect_stderr(inventory_warnings):
            inventory = InventoryManager(
                loader = loader,
                sources = [h+',' for h in hosts],
            )
        variable_manager  =  VariableManager(
            loader = loader,
            inventory = inventory,
            version_info = CLI.version_info(gitinfo=False),
        )
        playbook_path = None
        if playbook.count('\n') > 0:  # playbook is YAML content
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(str.encode(playbook))
                playbook_path = f.name
        else:  # playbook is a path to a YAML file
            playbook_path = playbook
        variable_manager.set_host_facts('localhost', facts=facts)
        for h in hosts:
            variable_manager.set_host_facts(h, facts=facts)
        pbex = PlaybookExecutor(
            playbooks = [playbook_path],
            inventory = inventory,
            variable_manager = variable_manager,
            loader = loader,
            passwords = dict(),
        )
        ansible_output = StringIO()
        with contextlib.redirect_stdout(ansible_output):
            try:
                self.result = pbex.run()  # execute playbook
            except Exception:
                print(traceback.format_exc(), end='')
        if playbook.count('\n') > 0:  # playbook is a string
            os.unlink(playbook_path)
        self.log = inventory_warnings.getvalue() + ansible_output.getvalue()
        recap_line_re = re.search(
            r'^PLAY RECAP \*+[ \r\n]+\S+\s+:\s*([^\r\n]+)',
            self.log,
            re.MULTILINE,
        )
        if recap_line_re is not None:
            try:
                # line example: localhost  : ok=1  changed=0  unreachable=0  failed=1  ...
                line = recap_line_re.group(1).rstrip()
                line_split = re.split(r'\s+|=', line)
                self.recap = dict(itertools.zip_longest(  # https://stackoverflow.com/a/6900977
                    itertools.islice(line_split, 0, None, 2),
                    [int(i) for i in itertools.islice(line_split, 1, None, 2)],
                    fillvalue='',
                ))
            except Exception as e:  # assume it's malformed log text
                self.result = -1
                print(f"exception while parsing Ansible log: {e}")
        else:
            self.result = -1
            print(f"cannot find Ansible play recap data")
        return self.result

