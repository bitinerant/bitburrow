#!/usr/bin/env python3

import argparse
import base64
import crypt
from hashlib import sha256
import io
import ipaddress
from ipaddress import IPv4Address, IPv6Address
import os
from pathlib import Path
import re
import secrets  # needs sudo apt install python3-secretstorage but default on Ubuntu 18.04 Desktop
from socket import gaierror
import sys
import telnetlib
import textwrap
import time
from typing import Union
import uuid

from cryptography.hazmat.backends import default_backend as crypto_default_backend
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from dbus import exceptions
import getmac
import netifaces  # needs sudo apt install python3-netifaces but default on Ubuntu 18.04 Desktop
import NetworkManager  # needs sudo apt install python3-networkmanager
import paramiko
from scp import SCPClient
import yaml


def _(s: str) -> str:
    """For future localization, mark all strings to be translated with _("string")"""
    return s


class CGError(Exception):
    pass


class RemoteExecutionError(Exception):
    pass


# TODO: Use logging levels for this rather than a global int.
verbose: int = None


def print_msg(level, msg, end="\n"):
    if verbose > level:
        if level == 0:
            print("{}".format(msg), file=sys.stderr, end=end)
        else:
            print("{}".format(msg), end=end)


def wifi_active_ssids():
    """Return a dict of MAC:SSID of currently-connected WiFi connections; note list may contain
    MACs which were seen for the AP but not currently (or even ever) associated with"""
    macs_found = dict()
    for conn in NetworkManager.NetworkManager.ActiveConnections:
        settings = conn.Connection.GetSettings()["connection"]
        if settings["type"] != "802-11-wireless":
            continue
        wifi = conn.Connection.GetSettings()["802-11-wireless"]
        ssid = wifi["ssid"]
        for mac in wifi["seen-bssids"]:
            macs_found[mac.lower()] = ssid
    return macs_found


def wifi_available_ssids():
    """Initiate a new WiFi scan, wait for it to complete, and return a (possibly empty)
    dict of MAC:SSID of available WiFi networks; usually takes a few seconds; it is normal
    to have multiple MACs with the same SSID"""
    # Based on: https://github.com/seveas/python-networkmanager/blob/master/examples/ssids.py
    macs_found = dict()
    os.system("nmcli dev wifi rescan 2>/dev/null")
    time.sleep(0.4)
    for dev in NetworkManager.NetworkManager.GetDevices():
        if dev.DeviceType != NetworkManager.NM_DEVICE_TYPE_WIFI:
            continue
        sig_levels = None
        # Wait until WiFi scan has completed, normally 0.8 - 3.8 seconds (including the 0.4 above).
        for delay in range(4, 68):  # tenths of seconds; upper limit slightly arbitrary
            try:
                # AccessPoint docs:
                # https://developer.gnome.org
                #   /NetworkManager/stable/gdbus-org.freedesktop.NetworkManager.AccessPoint.html
                aps = dev.GetAccessPoints()
                new_sig_levels = [a.Strength for a in aps]  # list of WiFi signal levels for APs
            except (exceptions.DBusException, NetworkManager.ObjectVanished):
                # ~5% of the scans, we get: No such interface 'org.freedesktop.DBus.Properties'
                time.sleep(0.1)
                continue
            # A change in signal levels means WiFi scan has completed.
            if sig_levels is not None and new_sig_levels != sig_levels:
                print_msg(
                    2, _("WiFi scan delay {}, signal levels {}").format(delay, new_sig_levels)
                )
                for ap in aps:
                    macs_found[ap.HwAddress.lower()] = ap.Ssid
                break
            sig_levels = new_sig_levels
            time.sleep(0.1)
    return macs_found


def wifi_connect(target_ssid, password):
    # Based on: https://github.com/seveas/python-networkmanager/blob/master/examples/n-m
    # and: https://github.com/seveas/python-networkmanager/blob/master/examples/add_connection.py
    nm_nm = NetworkManager.NetworkManager
    for c in nm_nm.ActiveConnections:
        s = c.Connection.GetSettings()
        if "802-11-wireless" in s and s["802-11-wireless"]["ssid"] == target_ssid:
            print_msg(1, _("Already connected to WiFi network {}").format(target_ssid))
            return
    conn_to_activate = None
    for twice in range(0, 2):
        for c in NetworkManager.Settings.ListConnections():
            if c.GetSettings()["connection"]["type"] != "802-11-wireless":
                continue
            # Not yet needed: id = c.GetSettings()['connection']['id']
            ssid = c.GetSettings()["802-11-wireless"]["ssid"]  # usually id == ssid
            if ssid == target_ssid:
                conn_to_activate = c
                break
        if conn_to_activate is not None:  # found - exit 'twice' loop
            break
        print_msg(2, _("Adding new NetworkManager connection {}").format(target_ssid))
        new_connection = {  # add a new connection
            "802-11-wireless": {
                "mode": "infrastructure",
                "security": "802-11-wireless-security",
                "ssid": target_ssid,
            },
            "802-11-wireless-security": {
                "auth-alg": "open",
                "key-mgmt": "wpa-psk",
                "psk": password,
            },
            "connection": {
                "id": target_ssid,
                "type": "802-11-wireless",
                "uuid": str(uuid.uuid4()),
            },
        }
        NetworkManager.Settings.AddConnection(new_connection)
        # Now repeat 'twice' loop to find the just-added item in ListConnections()
    for dev in nm_nm.GetDevices():
        if dev.DeviceType == NetworkManager.NM_DEVICE_TYPE_WIFI:
            print_msg(1, _("Connecting to WiFi network {}").format(target_ssid))
            nm_nm.ActivateConnection(conn_to_activate, dev, _("/"))
            time.sleep(3)
            return
    raise CGError(
        _("Cannot connect to Wifi network {} - no suitable devices are available").format(
            target_ssid
        )
    )


def generate_new_password(length=12):
    """Return a new, secure, random password of the given length"""
    # Do not use visually similar characters: lIO01
    pass_chars = r"""abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"""
    return "".join(secrets.choice(pass_chars) for i in range(length))


def hashed_md5_password(password, salt=None):  # https://stackoverflow.com/a/27282771/10590519
    """Return the Linux-format hashed password. The salt, if specified, must begin with
    '$' followed by an id as listed in the 'crypt' man page. If no salt is given, an MD5 salt
    is generaged for compatibility with older systems."""
    if salt is None:
        salt = crypt.mksalt(crypt.METHOD_MD5)  # begins '$1$', e.g. '$1$D6/56C4p'
    # The cli equivalent to crypt.crypt(): openssl passwd -1 -salt $PLAIN_SALT $PASSWORD
    return crypt.crypt(password, salt)


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


def add_line_breaks(long_string, line_len=70):
    return "\n".join(long_string[i : i + line_len] for i in range(0, len(long_string), line_len))


def possible_router_ips():
    """Return a list of IP addresses which may be a router - currently first IP of each subnet."""
    possible_routers = list()  # items are type ipaddress.ip_address
    for intf in netifaces.interfaces():  # e.g. eth0, lo
        for ip_ver in [netifaces.AF_INET, netifaces.AF_INET6]:  # IPv4 then IPv6
            if ip_ver in netifaces.ifaddresses(intf):  # if this interface has at least one address
                for a in netifaces.ifaddresses(intf)[ip_ver]:
                    if "addr" in a and "netmask" in a:
                        addr = a["addr"].split("%")[0]  # strip away '%' and interface name
                        prefix_len = bin(
                            int.from_bytes(
                                ipaddress.ip_address(a["netmask"]).packed, byteorder="big"
                            )
                        ).count("1")
                        subnet = ipaddress.ip_network(addr + "/" + str(prefix_len), strict=False)
                        if (
                            prefix_len < subnet.max_prefixlen  # not a /32 (IPv4) address
                            and not ipaddress.ip_address(addr).is_link_local
                        ):
                            first_ip = subnet[1]  # assume router is first IP in subnet
                            if not first_ip == ipaddress.ip_address(addr):  # if not our IP
                                possible_routers.append(first_ip)
    return possible_routers


def ssh_keyscan(ip, port=22):
    try:
        transport = paramiko.Transport((ip, port))
        transport.connect()
        key = transport.get_remote_server_key()
        transport.close()
        return key.get_name() + " " + key.get_base64()
    except (paramiko.ssh_exception.SSHException, gaierror):
        return None


def new_nickname(mac=None):
    manuf = ""
    known_macs = """
        # Small subset of OUI database from:
        # https://code.wireshark.org/review/gitweb?p=wireshark.git;a=blob_plain;f=manuf
        # Note literal tab characters don't work.
        E4:95:6E:40:00:00/28  GL.iNet
        B8:27:EB              Raspberry Pi
        94:B8:6D              Intel
        9C:B6:D0              RivetNet
    """
    if mac is not None and mac != "00:00:00:00:00:00":
        digits_of_mac = mac.translate({ord(c): None for c in [":", "-", ".", " "]}).lower()
        line_re = re.compile(r"^\s*([0-9a-fA-F:\.-]+)(/[0-9]+)?\s+([^#]+)$")
        comment_re = re.compile(r"^\s*(#.*)?$")
        for line in known_macs.split("\n"):
            match = line_re.match(line)
            if match:
                mask = 24 if match[2] is None else int(re.sub(r"\D", "", match[2]))
                assert (mask / 4).is_integer(), _("mask not multiple of 4: {}").format(line)
                mask_div_4 = int(mask / 4)  # ¼ of address mask is the number of hex digits needed
                line_digits = (
                    match[1].translate({ord(c): None for c in [":", "-", ".", " "]}).lower()
                )
                if digits_of_mac[0:mask_div_4] == line_digits[0:mask_div_4]:
                    manuf = " " + match[3].rstrip()
            elif not comment_re.match(line):
                raise CGError(_("Invalid OUI line: {}").format(line))
        return "new" + manuf + " device"


class SSHClientNoAuth(paramiko.SSHClient):
    # The work-around below is because paramiko does not support the "auth_none"
    # option (SSH requiring no authentication at all). For more details, see
    # https://stackoverflow.com/a/32986895/10590519
    # Instead of this work-around, one could modify "paramiko/client.py" and
    # change the last line of "_auth()"
    # from: raise SSHException("No authentication methods available")
    # to:   self._transport.auth_none(username)

    def _auth(self, username, *args):
        self._transport.auth_none(username)


class Router(yaml.YAMLObject):
    yaml_loader = yaml.SafeLoader
    yaml_tag = "!Router"  # https://stackoverflow.com/a/2890073/10590519

    def __init__(self, ip: Union[IPv4Address, IPv6Address], mac: str) -> None:
        assert mac is not None and mac != "00:00:00:00:00:00"
        self.ip = str(ip)
        self.mac = mac
        self.nickname = new_nickname(mac)
        self.create = time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime())
        self.version_map = dict()
        self.router_password = None
        self.client = None

    def generate_passwords(self):
        self.first_password = generate_new_password(length=12)
        self.router_password = generate_new_password(length=12)
        self.wifi_password = generate_new_password(length=10)

    def generate_ssh_keys(self):
        # Instead of ssh-keyscan, a safer option would be to convert
        # /etc/dropbear/dropbear_rsa_host_key to OpenSSH format. See:
        # https://github.com/mkj/dropbear/blob/master/dropbearconvert.c
        self.ssh_hostkey = add_line_breaks(ssh_keyscan(self.ip), line_len=64)
        # 64 (above) matches the privkey width
        (pub, priv) = generate_ssh_key_pair()
        self.ssh_pubkey = add_line_breaks(pub, line_len=64)
        self.ssh_privkey = priv

    def set_password_on_router(self, phase2):
        # It is also possible to set the router password via http, but this is
        # programmatically more complex, plus on older GL-iNet firmware, this
        # changes the WiFi password as well.
        # It would be more secure to use first_password below, and then set it again
        # with router_password via ssh.
        prompt = "[\r\n]root@"
        phase1 = {
            "[Ll]]ogin:": "root\n",
            "[Pp]assword:": "\n",
            prompt: None,  # None == we have arrived
        }
        # After a hard reset, some routers and firmware version listen for a telnet connection,
        # while others listen for an ssh connection with no authentication for 'root'. Try ssh
        # with no authentication first.
        tmp_client = SSHClientNoAuth()
        tmp_client.set_missing_host_key_policy(paramiko.RejectPolicy)  # ensure correct host key
        hostkey = self.ssh_hostkey.split(" ")
        tmp_client.get_host_keys().add(
            self.ip, hostkey[0], paramiko.RSAKey(data=base64.b64decode(hostkey[1]))
        )
        try:
            tmp_client.connect(
                hostname=self.ip,
                username="root",
                pkey=None,
                password=None,
                allow_agent=False,
                look_for_keys=False,
            )
        except paramiko.ssh_exception.NoValidConnectionsError:
            print_msg(1, _("Initial connection via ssh failed - trying telnet."))
        except paramiko.ssh_exception.AuthenticationException:
            pass  # router was reset and telnet will work -OR- it is already set up
        else:  # ssh connected
            for to_send in phase2.splitlines():
                print_msg(1, "Router cmd:    " + to_send)
                __, stdout, stderr = tmp_client.exec_command(to_send)
                exitc = stdout.channel.recv_exit_status()
                print_msg(1, "Router stdout: ".join([""] + list(stdout)), end="")
                print_msg(1, "Router stderr: ".join([""] + list(stderr)), end="")
                if exitc != 0:
                    tmp_client.close()
                    raise RemoteExecutionError(to_send)
            tmp_client.close()
            return
        phase1_prompts = [re.compile(p.encode()) for p in phase1]
        esc_seq_re = re.compile(r"\x1b\[[0-9;]+m")
        print_msg(1, "<telnet_log>")
        try:
            with telnetlib.Telnet(self.ip, timeout=5) as t:
                cycles = 0
                while cycles < 7:  # phase 1 - logging into router
                    (index, __, data) = t.expect(phase1_prompts, timeout=5)
                    print_msg(1, "".join(esc_seq_re.split(data.decode())), end="")
                    if index >= 0:
                        to_send = phase1[phase1_prompts[index].pattern.decode()]
                        if to_send is None:
                            break
                        t.write(to_send.encode())
                    else:
                        raise CGError(_("Timeout connecting to {}").format(self.nickname))
                    cycles += 1
                if cycles >= 7:
                    raise CGError(_("Unable to log in to {}").format(self.nickname))
                for to_send in phase2.splitlines():  # phase 2 - commands to send router
                    try:
                        t.write((to_send + "\n").encode())
                        (__, __, data) = t.expect([re.compile(prompt.encode())], timeout=3)
                    except EOFError:
                        pass
                    print_msg(1, "".join(esc_seq_re.split(data.decode())), end="")
                print_msg(1, "")  # make sure we end with a newline
        except (ConnectionRefusedError, EOFError):
            # The 'official' instructions to reset: Press and hold the "Reset" button for
            # 10 seconds, then release your finger. You will see LEDs flash in a
            # pattern. Wait for the router to reboot and then start over.
            raise CGError(
                _("Unable to connect to {} at {}. ").format(self.nickname, self.ip)
                + _("Please factory-reset your router and try again.")
            )
        finally:
            print_msg(1, "</telnet_log>")

    def connect_ssh(self):
        if self.client is not None:
            return
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.RejectPolicy)  # ensure correct host key
        # Host key is normally a line in ~/.ssh/known_hosts
        try:
            hostkey = self.ssh_hostkey.split(" ")
        except AttributeError:
            raise CGError(_("Router has not yet been configured for ssh."))
        self.client.get_host_keys().add(
            self.ip, hostkey[0], paramiko.RSAKey(data=base64.b64decode(hostkey[1]))
        )
        # Private key is normally in ~/.ssh/id_rsa
        privkey_file = io.StringIO()
        privkey_file.write(self.ssh_privkey)
        privkey_file.seek(0)
        privkey = paramiko.RSAKey.from_private_key(privkey_file)
        connect_method = "none"
        try:  # first try to connect using private ssh key
            self.client.connect(
                hostname=self.ip,
                username="root",
                pkey=privkey,
                # Don't use password this time because we want to know if ssh key fails.
                # Could improve speed by using low-level class, but key should normally
                # work so not worth it. See: https://stackoverflow.com/questions/54296230
                password=None,
                allow_agent=False,
                look_for_keys=False,
            )
            connect_method = "ssh key"
        except paramiko.ssh_exception.AuthenticationException:
            try:  # if private ssh key fails, try the password
                self.client.connect(
                    hostname=self.ip,
                    username="root",
                    pkey=None,
                    password=self.router_password,
                    allow_agent=False,
                    look_for_keys=False,
                )
                print_msg(1, _("Warning: connecting via ssh key failed"))
                connect_method = "password"
            except paramiko.ssh_exception.AuthenticationException:
                self.client = None
                raise CGError(_("Unable to connect to {} at {}.").format(self.nickname, self.ip))
        self.last_connect = time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime()) + " {}".format(
            connect_method
        )
        print_msg(1, _("Connected to {} via {}").format(self.nickname, connect_method))

    def exec(self, command, okay_to_fail=False):
        print_msg(1, "Router cmd:    " + command)
        __, stdout, stderr = self.client.exec_command(command)
        exitc = stdout.channel.recv_exit_status()
        out = ""
        for line in stdout:
            out += line
            print_msg(1, "Router stdout: " + line.rstrip())
        err0 = ""
        err_count = 0
        for line in stderr:
            if err_count == 0:
                err0 = line.rstrip()
            err_count += 1
            print_msg(1, "Router stderr: " + line.rstrip())
        if exitc != 0:
            if okay_to_fail:
                return err0
            else:
                raise RemoteExecutionError(err0)
        return out

    def put(self, data, remote_path):
        # SFTP would be nice, but OpenWrt only supports SCP
        scp = SCPClient(self.client.get_transport())  # https://github.com/jbardin/scp.py
        data_file = io.BytesIO()  # in-memory file-like object
        data_file.write(data)
        data_file.seek(0)
        scp.putfo(data_file, remote_path)
        scp.close()
        data_file.close()

    def close(self):
        if self.client:
            print_msg(1, _("Closing client connection"))
            self.client.close()
            self.client = None


class Config(yaml.YAMLObject):
    yaml_loader = yaml.SafeLoader
    yaml_tag = "!Config"

    def __init__(self):
        self.routers = None

    def set_defaults(self):
        self.routers = list()
        self.default_vpn_username = input(_("Enter the PIA username to use on routers: "))
        self.default_vpn_password = input(_("Enter the PIA password to use on routers: "))
        self.default_vpn_server_host = input(_("Enter the PIA region to use on routers: "))


class ConfigSaver:
    @staticmethod
    def long_str_representer(dumper, data):  # https://stackoverflow.com/a/33300001/10590519
        if len(data.splitlines()) > 1:  # check for multiline string
            return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
        return dumper.represent_scalar("tag:yaml.org,2002:str", data)

    @staticmethod
    def conf_dir():
        return os.path.expanduser("~/.cleargopher")

    @staticmethod
    def _conf_path():
        return os.path.join(ConfigSaver.conf_dir(), "cleapher.conf")

    @staticmethod
    def load() -> Config:
        config = Config()
        conf_path = ConfigSaver._conf_path()
        try:
            with open(conf_path, "r") as conf_file:
                try:
                    config = yaml.safe_load(conf_file.read())
                except yaml.YAMLError as yaml_err:
                    raise CGError(_("Error parsing {}: {}").format(conf_path, yaml_err))
        except FileNotFoundError:  # missing config file
            pass
        if config.routers is None:  # missing or empty config file - start fresh
            config.set_defaults()
        for r in config.routers:
            r.client = None
        return config

    @staticmethod
    def save(config: Config) -> None:
        conf_path = ConfigSaver._conf_path()
        try:
            os.mkdir(ConfigSaver.conf_dir())
        except FileExistsError:
            pass
        yaml.add_representer(str, ConfigSaver.long_str_representer)
        # For Router.version_map, we use in-order dictionaries in YAML output - from:
        # https://stackoverflow.com/a/52621703/10590519
        yaml.add_representer(
            dict,
            lambda self, data: yaml.representer.SafeRepresenter.represent_dict(self, data.items()),
        )
        try:
            header = (
                _("This is the Clear Gopher YAML configuration file. Be very careful ")
                + _("when editing because indent, colons, and many other characters have ")
                + _("special meaning.")
            )
            # The 'width' option below does not work as expected
            body = yaml.dump(config, default_flow_style=None, width=48)
            with open(conf_path + ".0", "w") as conf_file:
                # Restrict file permissions to protect passwords, keys from other users
                os.chmod(conf_path + ".0", 0o600)
                conf_file.write("# " + "\n# ".join(textwrap.wrap(header, width=66)) + "\n")
                # Don't save routers.client
                conf_file.write(re.sub(r"\n *client:[^\n]+\n", "\n", body))
        except OSError as err:
            raise CGError(_("Error saving configuration {}: {}").format(conf_path + ".0", err))
        try:
            os.rename(conf_path, conf_path + ".bak")  # keep 1 old version
        except FileNotFoundError:
            pass
        try:
            os.rename(conf_path + ".0", conf_path)
        except FileNotFoundError as err:
            raise CGError(_("Error saving configuration {}: {}").format(conf_path, err))


def wifi_hunt(conf, factory_wifi=""):
    """Scan and connect to router's WiFi network. Return SSID, password."""
    line_re = re.compile(r" {2,}: +")  # wifi_re and password separated by '  : ', one per line
    factory_ssids = dict()
    for line in factory_wifi.splitlines():
        if line.startswith("#"):
            continue
        two_items = line_re.split(line)
        if len(two_items) != 2:
            raise CGError(_("Invalid factory_wifi data line: {}").format(line))
        factory_ssids[two_items[0]] = two_items[1]
    nets = wifi_available_ssids()  # scan for nearby WiFi networks
    known_ssids = dict()  # SSID : password
    for s in list(set(nets.values())):  # for each unique SSID
        for r in conf.routers:  # test SSIDs from conf file _first_
            if s == r.ssid:
                print_msg(1, _("Using stored password for WiFi network {}").format(s))
                known_ssids[s] = r.wifi_password
        for e in factory_ssids:  # test regex list _second_
            if s not in known_ssids and re.match(e, s):
                known_ssids[s] = factory_ssids[e]
    if len(known_ssids) == 0:
        print_msg(1, _("Visible networks: {}").format(", ".join(list(set(nets.values())))))
        raise CGError(_("Unable to find WiFi network for a supported router"))
    elif len(known_ssids) > 1:
        err = "\n".join(_("Possible router: {}").format(r) for r in known_ssids) + "\n"
        raise CGError(err + _("Multiple possible networks found"))
    ssid = list(known_ssids.keys())[0]
    ssid_password = known_ssids[ssid]
    wifi_connect(ssid, ssid_password)
    return ssid, ssid_password


def get_mac_address(address: Union[IPv4Address, IPv6Address]) -> Optional[str]:
    if isinstance(address, IPv4Address):
        mac = getmac.get_mac_address(ip=str(address))
    elif isinstance(address, IPv6Address):
        mac = getmac.get_mac_address(ip6=str(address))
    else:
        raise TypeError("address must be an ipaddress")
    return mac


def set_up_ssh(router: Router, conf: Config):
    router.generate_passwords()
    router.generate_ssh_keys()
    router.vpn_username = conf.default_vpn_username
    router.vpn_password = conf.default_vpn_password
    router.vpn_server_host = conf.default_vpn_server_host
    # If router also serves as AP, once we have connected to the router via ssh, this
    # could be used instead of above line:
    # router.ssid = router.exec('uci get wireless.@wifi-iface[0].ssid').rstrip()
    conf.routers.append(router)


def network_hunt(conf, ssid):
    """Scan local networks for router. Return existing or new Router() instance."""
    ip_list_full = [ipaddress.ip_address(r.ip) for r in conf.routers]  # IPs from config file
    ip_list_full += possible_router_ips()  # first IP of each detected network
    # Note ip_list_full will normally include 192.168.8.1
    ip_list_no_dups = [i for n, i in enumerate(ip_list_full) if i not in ip_list_full[:n]]
    mac_to_ip = dict()
    router_options = list()  # computed list of what could be a router
    for ip in ip_list_no_dups:  # for each IP that might be a router
        mac = get_mac_address(ip)
        if mac is None:  # unroutable IP
            continue
        if mac == "00:00:00:00:00:00":  # unreachable (no host at IP)
            continue
        if mac in mac_to_ip:  # duplicate MAC
            print_msg(
                1,
                _("Using MAC {mac} on {ip1}, ignoring duplicate on {ip2}").format(
                    mac=mac, ip1=str(mac_to_ip[mac]), ip2=str(ip)
                ),
            )
            continue
        mac_to_ip[mac] = ip
        found = False
        hostkey = add_line_breaks(ssh_keyscan(str(ip)), line_len=64)  # takes a few seconds
        # Note we don't match based on MAC because routers can be reset, plus some
        # routers generate the MAC address for certain interfaces at _boot_ time.
        for r in conf.routers:  # look for matching hostkey in conf data
            if r.ssh_hostkey == hostkey:
                r.ip = str(ip)  # update IP if it has changed since config file was saved
                r.mac = mac  # update MAC if it has changed
                router_options.append(r)
                found = True
                break
        if not found:
            r = Router(ip, mac)  # previously-unknown router
            router_options.append(r)
    if len(router_options) > 1:
        err = "\n".join(_("Possible router: {} (ip {})").format(r.nickname, r.ip)) + "\n"
        raise CGError(err + _("Multiple possible routers found"))
    if len(router_options) == 0:
        raise CGError(_("No possible routers found"))
    router = router_options[0]  # the chosen router
    router.ssid = ssid
    if not router.router_password:
        set_up_ssh(router, conf)
    print_msg(1, _("Using router {} (ip {})").format(router.nickname, router.ip))
    return router


class Coteries:
    """
    A coterie is a group of gophers, or in this context, a group of commands or a file
    which changes the state of the router. A coterie module is a YAML file which contains
    some metadata plus an ordered set of coteries which can be used to set up a router
    for a particular purpose.

    Example of the beginning of a .coterie file with line numbers added:

     1  !CoterieModule
     2  module_type: router_hardware
     3  vpn_type: openvpn
     4  display_name: GL.iNet
     5  coteries:
     6  - !Coterie
     7  id: routerauth
     8  delta: 0 1
     9  sort: 15
    10  type: routerauth
    11  data: |
    12      cat /etc/openwrt_release
    13      uname -a

    Line explanations:
    - 1: required header
    - 7: the name of the coterie
    - 8: 2 integers separated by a space, representing the from and to version for this coterie
    - 9: |
        This integer defines the sequence in which coteries are applied. Coteries with the
        same 'sort' will be done in the order listed in the .coterie file. The primary
        purpose for this value is to be able to properly merge coteries of VPN providers and
        router vendors.
        10-19 configure router password and ssh key
        20-29 check existing state and compatibility
        30-39 configure system and other passwords
        40-49 copy files and set permissions (45 is recommended for all VPN provider files and
          commands)
        50-59 install needed software
        60-69 configure VPN, network, firewall
        70-79 configure startup
        80-89 after first reboot
        90-99 testing
    - 10: |
        commands: list of shell commands to be run one-at-a-time on router
        exploration: like 'commands' but okay for commands to fail
        routerauth: like 'commands' but connect to router without authentication
        file: file that is to be copied to router; must define 'path' and (in another coterie)
          commands to set permissions
        factory_wifi: list of WiFi SSIDs (regular expression), followed by '  : ' (additional
          spaces are ignored), followed by the default WiFi password for the given SSID; one
          SSID/password per line
    """

    class CoterieModule(yaml.YAMLObject):
        yaml_loader = yaml.SafeLoader
        yaml_tag = "!CoterieModule"

    class Coterie(yaml.YAMLObject):
        yaml_loader = yaml.SafeLoader
        yaml_tag = "!Coterie"

        def exec(self, router):
            if self.type == "factory_wifi":
                return
            version_now = router.version_map.get(self.id, 0)
            version_available = int(self.delta.split(" ")[1])  # 'from' version not yet implemented
            if version_now >= version_available:
                return
            print_msg(1, _("Updating to {} {}").format(self.id, version_available))
            data_no_params = self.data
            if "{root_shadow_line}" in data_no_params:
                p = "root:" + hashed_md5_password(router.router_password) + ":0:0:99999:7:::"
                data_no_params = data_no_params.replace("{root_shadow_line}", p)
            if "{authorized_keys_line}" in data_no_params:
                # Remove all whitespace except a space by itself
                p = re.sub(r"(\s{2,})|([\t\r\n]+)|(\s+$)", "", router.ssh_pubkey)
                data_no_params = data_no_params.replace("{authorized_keys_line}", p)
            if "{http_password_sha256}" in data_no_params:
                p = sha256(router.router_password.encode()).hexdigest()
                data_no_params = data_no_params.replace("{http_password_sha256}", p)
            # Alternatively, we could ignore the KeyError exception -
            # see https://stackoverflow.com/a/17215533/10590519
            try:
                data_no_params = data_no_params.format(**vars(router))
            except (KeyError, IndexError) as err:
                raise CGError(_("Unknown named parameter in coterie {}: {}").format(self.id, err))
            try:
                if self.type == "routerauth":
                    router.set_password_on_router(data_no_params)
                elif self.type == "exploration":
                    router.connect_ssh()
                    for line in data_no_params.splitlines():
                        router.exec(line, okay_to_fail=True)
                elif self.type == "commands":
                    router.connect_ssh()
                    for line in data_no_params.splitlines():
                        router.exec(line, okay_to_fail=False)
                elif self.type == "file":
                    router.connect_ssh()
                    router.put(data_no_params.encode(), self.path)
            except RemoteExecutionError as err:
                raise CGError(_("Failed to execute coterie {}: {}").format(self.id, err))
            router.version_map[self.id] = version_available  # we have now successfully upgraded

    @staticmethod
    def load():
        """Load and validate coterie modules."""
        self = Coteries()
        valid_module_types = {"vpn_provider", "router_hardware"}
        valid_vpn_types = {"openvpn"}
        valid_types = {"commands", "exploration", "routerauth", "file", "factory_wifi"}
        valid_id_re = re.compile(r"[a-zA-Z0-9\._-]+$")
        valid_display_name_re = re.compile(r"[^\t\r\n]+$")
        self.modules = list()
        our_dir = os.path.dirname(Path(sys.argv[0]).resolve())
        coteries_dir = os.path.join(our_dir, "coteries")
        for f in os.listdir(coteries_dir):
            f_path = os.path.join(coteries_dir, f)
            with open(f_path, "r") as coterie_file:
                try:
                    module = yaml.safe_load(coterie_file)
                except (yaml.YAMLError, yaml.constructor.ConstructorError) as yaml_err:
                    raise CGError(_("Error parsing {}: {}").format(f, yaml_err))
            try:
                if module.module_type not in valid_module_types:
                    raise CGError(_("Invalid module_type in {}: {}").format(f, module.module_type))
                if module.vpn_type not in valid_vpn_types:
                    raise CGError(_("Invalid vpn_type in {}: {}").format(f, module.vpn_type))
                if not valid_display_name_re.match(module.display_name):
                    raise CGError(
                        _("Invalid display_name in {}: {}").format(f, module.display_name)
                    )
            except AttributeError as err:
                raise CGError(_("Missing item in {}: {}").format(f, err))
            sort_max = 0
            ids = set()
            for c in module.coteries:
                try:
                    if not valid_id_re.match(c.id):
                        raise CGError(_("Invalid id in {}: {}").format(f, c.id))
                    if c.id in ids:
                        raise CGError(_("Duplicate id in {}: {}").format(f, c.id))
                    ids.add(c.id)
                except AttributeError:
                    raise CGError(_("Missing id for a coterie in {}").format(f))
                try:
                    if int(c.delta.split(" ")[0]) >= int(c.delta.split(" ")[1]):
                        raise CGError(_("Invalid delta in {}#{}: {}").format(f, c.id, c.delta))
                    if c.sort < sort_max:
                        raise CGError(_("Coterie {}#{} is not in sort order").format(f, c.id))
                    sort_max = c.sort
                    if c.type not in valid_types:
                        raise CGError(_("Invalid type in {}#{}: {}").format(f, c.id, c.type))
                    if c.type == "file" and c.path[0] != "/":
                        raise CGError(_("Invalid path in {}#{}: {}").format(f, c.id, c.path))
                    if c.data[-1][-1] != "\n":
                        raise CGError(_("Data does not end in a newline in {}#{}").format(f, c.id))
                except AttributeError as err:
                    raise CGError(_("Missing item in {}#{}: {}").format(f, c.id, err))
            print_msg(2, _("Loaded module {} ({} coteries)").format(f_path, len(module.coteries)))
            module.elected = True  # selecting a subset of modules is not yet implemented
            self.modules.append(module)
        return self

    def elected_coteries(self):
        """Return a list of coteries from all elected modules"""
        coteries_from_elected_modules = list()
        for m in self.modules:
            if m.elected:
                coteries_from_elected_modules += m.coteries
        ids = set()
        for c in coteries_from_elected_modules:  # be certain we have no duplicate IDs here
            if c.id in ids:
                raise CGError(_("Duplicate coterie id {}").format(c.id))
            ids.add(c.id)
        return sorted(coteries_from_elected_modules, key=lambda c: c.sort)


def do_router_set_up():
    coteries = Coteries.load()
    elected = coteries.elected_coteries()
    conf = ConfigSaver.load()
    try:
        factory_wifi = next((c.data for c in elected if c.type == "factory_wifi"), None)
        ssid, ssid_password = wifi_hunt(conf, factory_wifi)
        router = network_hunt(conf, ssid)
    except:  # noqa: E722
        ConfigSaver.save(conf)
        raise
    try:
        for c in elected:
            c.exec(router)
        print_msg(1, _("Set-up successful"))
    finally:
        router.close()  # docs emphasize importance of closing Paramiko client
        ConfigSaver.save(conf)


def do_shell(verbosity: int, router_address: IPv4Address = None) -> None:
    """Execute shell commands on the router. This is mostly for testing and as example code."""
    conf = ConfigSaver.load()
    if router_address is not None:
        mac = get_mac_address(router_address)
        if mac is None:
            # TODO: Should the MAC be required just to connect to the router? Add dummy
            #   MAC for now to support NAT'd VMs or other scenarios where the router is not on
            #   the same subnet.
            mac = "00:01:02:03:04:05"
        router = Router(router_address, mac)
        set_up_ssh(router, conf)
    else:
        ssid, ssid_password = wifi_hunt(conf)
        router = network_hunt(conf, ssid)
    try:
        router.connect_ssh()
        if verbosity > 1:
            global verbose
            verbose = 1  # reduce verbosity for shell processing
        cmd = ""
        while cmd != "exit":
            try:
                cmd = input("router> ")
            except (EOFError, KeyboardInterrupt):
                cmd = "exit"
            if cmd == "":
                continue
            try:
                print(router.exec(cmd).rstrip())
            except RemoteExecutionError as err:
                print(err)
    finally:
        router.close()  # docs emphasize importance of closing Paramiko client
        ConfigSaver.save(conf)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=_("Configures a router as a VPN client"),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Optional arguments
    group_verbose = parser.add_mutually_exclusive_group()
    group_verbose.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=1,
        help=_("increase output verbosity; can be used multiple times"),
    )
    group_verbose.add_argument(
        "-q",
        "--quiet",
        action="store_const",
        const=0,
        dest="verbose",  # mapping: '-q'->0 / default->1 / '-v'->2 / '-vv'->3
        help=_("silence error messages"),
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help=_("unattended mode (answer 'yes' to all questions)"),
    )
    parser.add_argument(
        "--router-address",
        required=False,
        type=IPv4Address,
        help=_(
            "IP address of the router, if known and already connected via WiFi or LAN, to skip "
            "automatic scanning."
        ),
    )

    # Mandatory arguments
    parser.add_argument(
        "command",
        choices=("set-up", "update", "shell", "internal-tests"),
        metavar="command",
        help=_("task to perform: set-up, update, or shell"),
    )

    # To get a real shell (in step 3 use 'router_password' from ~/.cleargopher/cleapher.conf):
    # ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa  # if prompted, don't overwrite existing key
    # ssh-keyscan 192.168.8.1 2>/dev/null |perl -pe 's|^[^ ]*|*|' >>~/.ssh/known_hosts
    # cat ~/.ssh/id_rsa.pub |ssh root@192.168.8.1 'cat - >>/etc/dropbear/authorized_keys'
    # ssh root@192.168.8.1  # no password needed from now on
    return parser.parse_args()


def main() -> None:
    global verbose

    args = parse_args()
    verbose = args.verbose

    if args.command == "set-up":
        do_router_set_up()
    elif args.command == "shell":
        do_shell(args.verbose, args.router_address)
    elif args.command == "internal-tests":
        coteries = Coteries.load()
        first = coteries.modules[1].coteries[0].data  # noqa: F841
        assert new_nickname("b8:27:eb:12:34:56") == "new Raspberry Pi device"
        print_msg(1, _("Internal tests successful"))


if __name__ == "__main__":
    try:
        main()
    except CGError as err:
        print_msg(0, err)
        exit(1)
