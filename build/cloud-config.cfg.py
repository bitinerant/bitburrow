#!/usr/bin/env python3
#
"""
To test:
./70_child_host_keys.cfg.py ci-test /tmp/ci-test-ecdsa-key >/tmp/ci-test.yaml
./80_child_users.cfg.py >>/tmp/ci-test.yaml
./81_child_sys.cfg.py >>/tmp/ci-test.yaml
lxc launch ubuntu:18.04/amd64 cloud-init-test "--config=user.user-data=$(cat /tmp/ci-test.yaml)"
sleep 10  # let it set up users, keys
IP=$(lxc info cloud-init-test |grep -Po '\seth\d:\sinet\s+\K[0-9\.]+')
echo $IP $(cat /tmp/ci-test-ecdsa-key) >/tmp/ci-test-known_hosts
ssh -i ~/.ssh/id_rsa_kivy-buildozer -o UserKnownHostsFile=/tmp/ci-test-known_hosts adminc@$IP
lxc stop cloud-init-test && lxc delete cloud-init-test
"""

import os
import re
import subprocess
import sys
from sys import stderr
import tempfile
import yaml

def generate_ssh_key_pair():  # based on: https://stackoverflow.com/a/39126754/10590519
    """Return a tuple containing new public and private keys."""
    key = rsa.generate_private_key(
        backend=crypto_default_backend(), public_exponent=65537, key_size=2048
    )
    private_key = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.PKCS8,
        crypto_serialization.NoEncryption(),
    ).decode()
    public_key = (
        key.public_key()
        .public_bytes(
            crypto_serialization.Encoding.OpenSSH, crypto_serialization.PublicFormat.OpenSSH
        )
        .decode()
    )
    # 'RSA' needs to be in header; looks like: https://github.com/paramiko/paramiko/issues/1226
    return (
        public_key,
        private_key.replace("-BEGIN PRIVATE KEY-", "-BEGIN RSA PRIVATE KEY-").replace(
            "-END PRIVATE KEY-", "-END RSA PRIVATE KEY-"
        ),
    )

class Config(yaml.YAMLObject):
    yaml_tag = "!Config"

class YamlSaver:
    @staticmethod
    def long_str_representer(dumper, data):  # https://stackoverflow.com/a/33300001/10590519
        if len(data.splitlines()) > 1:  # check for multiline string
            return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
        return dumper.represent_scalar("tag:yaml.org,2002:str", data)

    @staticmethod
    def save(config) -> None:
        yaml.add_representer(str, YamlSaver.long_str_representer)
        yaml.add_representer(
            dict,
            lambda self, data: yaml.representer.SafeRepresenter.represent_dict(self, data.items()),
        )
        header = "#cloud-config"
        # The 'width' option below does not work as expected
        return yaml.dump(config, default_flow_style=None, width=48)

def add_line_breaks(long_string, line_len=70):
    return "\n".join(long_string[i : i + line_len] for i in range(0, len(long_string), line_len))

def child_users_cfg():
    # cloudinit docs: https://cloudinit.readthedocs.io/en/stable/topics/modules.html#users-and-groups
    id_rsa_pub_path = os.path.join(os.environ['HOME'], ".ssh/id_rsa_kivy-buildozer")
    if not os.path.isfile(id_rsa_pub_path):  # generate ssh key if needed
        os.system("ssh-keygen -q -f '" + id_rsa_pub_path + "' -t rsa -N ''")
    with open(id_rsa_pub_path + ".pub", "r") as k:
        key = k.read()
    data = Config()
    data.users = [
        #"default",  # do not create the default 'ubuntu' user
        {
            "name": "adminc",  # 'admin' is reserved - https://askubuntu.com/a/900986
            "uid": "4288",  # reserve uid range 1000-1999 for mirroring desktop users
            "groups": "adm, audio, cdrom, dialout, dip, floppy, lxd, netdev, plugdev, sudo, video",
            "ssh_authorized_keys": [key.rstrip(" \n"),],
            "sudo": "ALL=(ALL) NOPASSWD:ALL",
            "shell": "/bin/bash",
        },
    ]
    y = YamlSaver.save(data)
    y = re.sub(r"^!Config\n", "", y)
    return "#cloud-config\n"+y

def child_host_keys(key_comment, ecdsa_pub_key_path):
    # docs: https://cloudinit.readthedocs.io/en/latest/topics/modules.html#ssh
    # and: https://cloudinit.readthedocs.io/en/latest/topics/examples.html#configure-instances-ssh-keys
    temp_key_dir = tempfile.mkdtemp(prefix='ccc_')
    temp_key_file = os.path.join(temp_key_dir, "ssh_host_key")
    data = Config()
    data.ssh_keys = Config()
    #ssh-keygen -f etc/ssh/ssh_host_key       -C 'root@child' -N '' -t rsa1
    #ssh-keygen -f etc/ssh/ssh_host_rsa_key   -C 'root@child' -N '' -t rsa
    #ssh-keygen -f etc/ssh/ssh_host_dsa_key   -C 'root@child' -N '' -t dsa
    #ssh-keygen -f etc/ssh/ssh_host_ecdsa_key -C 'root@child' -N '' -t ecdsa -b 521
    for key_type in ["rsa", "dsa", "ecdsa"]:
        r = subprocess.run([
            "/usr/bin/ssh-keygen",
            "-f", temp_key_file,
            "-C", key_comment,
            "-N", "",
            "-t", key_type,
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        with open(temp_key_file, "r") as k:
            key = k.read()
        with open(temp_key_file+".pub", "r") as k:
            key_pub = k.read()
        setattr(data.ssh_keys, key_type+"_private", key)
        setattr(data.ssh_keys, key_type+"_public", add_line_breaks(key_pub))
        if(key_type == "ecdsa"):
            with open(ecdsa_pub_key_path, "w") as k:
                k.write(key_pub.replace(key_comment, "").rstrip(" \n"))
        os.remove(temp_key_file)
        os.remove(temp_key_file+".pub")
    os.rmdir(temp_key_dir)
    y = YamlSaver.save(data)
    y = re.sub(r"^!Config\n", "", y)
    y = re.sub(r" !Config\n", "\n", y)
    return "#cloud-config\n"+y

def child_sys_cfg():
    data = Config()
    data.package_update = True  # default True
    #data.package_upgrade = True  # this might take a very long time on first boot
    data.packages = [
        "ssh",
    ]
    y = YamlSaver.save(data)
    y = re.sub(r"^!Config\n", "", y)
    return "#cloud-config\n"+y

if __name__ == "__main__":
    _, argv0 = os.path.split(sys.argv[0])  # name of program
    if argv0 == "81_child_sys.cfg.py":
        print(child_sys_cfg(), end="")
    elif argv0 == "80_child_users.cfg.py":
        print(child_users_cfg(), end="")
    elif argv0 == "70_child_host_keys.cfg.py":
        argv1 = sys.argv[1]  # comment to put in keys
        argv2 = sys.argv[2]  # path to write ecdsa public key to
        print(child_host_keys(argv1, argv2), end="")
    else:
        print("error: unknown program", file=stderr)

