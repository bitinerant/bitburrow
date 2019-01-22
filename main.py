#!/usr/bin/python3
# note double quotes are used for text that should be localized (l10n); single quotes elsewhere

import argparse
import os
import io
from sys import stderr
import re
import secrets
import base64
import netifaces # needs pip3 install netifaces (but installed by default on Ubuntu 18.04 Desktop)
import ipaddress
import getmac # needs pip3 install getmac
from scp import SCPClient # needs pip3 install scp
import telnetlib
import paramiko
from socket import gaierror
import crypt
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend
from hashlib import sha256
import yaml # FIXME: consider ruamel.yaml - https://stackoverflow.com/a/36760452/10590519
import time
import textwrap


class CGError(Exception):
    pass

class RemoteExecutionError(Exception):
    pass


def print_msg(level, msg, end='\n'):
    if args.verbose > level:
        if level == 0:
            print('{}'.format(msg), file=stderr, end=end)
        else:
            print('{}'.format(msg), end=end)


### process command-line arguments ###
# optional arguments
parser = argparse.ArgumentParser(description="Configures a router as a VPN client")
group_verbose = parser.add_mutually_exclusive_group()
group_verbose.add_argument('-v', '--verbose', action='count', default=1,
        help="increase output verbosity; can be used multiple times")
group_verbose.add_argument('-q','--quiet', action='store_const', const=0,
        dest='verbose', # mapping: '-q'->0 / default->1 / '-v'->2 / '-vv'->3
        help="silence error messages")
parser.add_argument('-y','--yes', action='store_true', 
        help="unattended mode (answer 'yes' to all questions)")
parser.add_argument('-d','--debug', action='store_true', 
        help="debug mode")
# mandatory arguments
parser.add_argument('command', choices=('configure', 'update'), metavar='command',
        help="task to perform: configure or update")
args = parser.parse_args()


if args.debug:
    import code
    #insert this to debug new code:
    # if args.debug:
    #     code.interact(local=locals())


class VpnProvider():
    pass


class PrivateInternetAccess(VpnProvider):

    def file(filename, data={}):
        if filename == 'ca.rsa.2048.crt':
            # from https://www.privateinternetaccess.com/openvpn/openvpn.zip
            fcontents = '''\
                -----BEGIN CERTIFICATE-----
                MIIFqzCCBJOgAwIBAgIJAKZ7D5Yv87qDMA0GCSqGSIb3DQEBDQUAMIHoMQswCQYD
                VQQGEwJVUzELMAkGA1UECBMCQ0ExEzARBgNVBAcTCkxvc0FuZ2VsZXMxIDAeBgNV
                BAoTF1ByaXZhdGUgSW50ZXJuZXQgQWNjZXNzMSAwHgYDVQQLExdQcml2YXRlIElu
                dGVybmV0IEFjY2VzczEgMB4GA1UEAxMXUHJpdmF0ZSBJbnRlcm5ldCBBY2Nlc3Mx
                IDAeBgNVBCkTF1ByaXZhdGUgSW50ZXJuZXQgQWNjZXNzMS8wLQYJKoZIhvcNAQkB
                FiBzZWN1cmVAcHJpdmF0ZWludGVybmV0YWNjZXNzLmNvbTAeFw0xNDA0MTcxNzM1
                MThaFw0zNDA0MTIxNzM1MThaMIHoMQswCQYDVQQGEwJVUzELMAkGA1UECBMCQ0Ex
                EzARBgNVBAcTCkxvc0FuZ2VsZXMxIDAeBgNVBAoTF1ByaXZhdGUgSW50ZXJuZXQg
                QWNjZXNzMSAwHgYDVQQLExdQcml2YXRlIEludGVybmV0IEFjY2VzczEgMB4GA1UE
                AxMXUHJpdmF0ZSBJbnRlcm5ldCBBY2Nlc3MxIDAeBgNVBCkTF1ByaXZhdGUgSW50
                ZXJuZXQgQWNjZXNzMS8wLQYJKoZIhvcNAQkBFiBzZWN1cmVAcHJpdmF0ZWludGVy
                bmV0YWNjZXNzLmNvbTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAPXD
                L1L9tX6DGf36liA7UBTy5I869z0UVo3lImfOs/GSiFKPtInlesP65577nd7UNzzX
                lH/P/CnFPdBWlLp5ze3HRBCc/Avgr5CdMRkEsySL5GHBZsx6w2cayQ2EcRhVTwWp
                cdldeNO+pPr9rIgPrtXqT4SWViTQRBeGM8CDxAyTopTsobjSiYZCF9Ta1gunl0G/
                8Vfp+SXfYCC+ZzWvP+L1pFhPRqzQQ8k+wMZIovObK1s+nlwPaLyayzw9a8sUnvWB
                /5rGPdIYnQWPgoNlLN9HpSmsAcw2z8DXI9pIxbr74cb3/HSfuYGOLkRqrOk6h4RC
                OfuWoTrZup1uEOn+fw8CAwEAAaOCAVQwggFQMB0GA1UdDgQWBBQv63nQ/pJAt5tL
                y8VJcbHe22ZOsjCCAR8GA1UdIwSCARYwggESgBQv63nQ/pJAt5tLy8VJcbHe22ZO
                sqGB7qSB6zCB6DELMAkGA1UEBhMCVVMxCzAJBgNVBAgTAkNBMRMwEQYDVQQHEwpM
                b3NBbmdlbGVzMSAwHgYDVQQKExdQcml2YXRlIEludGVybmV0IEFjY2VzczEgMB4G
                A1UECxMXUHJpdmF0ZSBJbnRlcm5ldCBBY2Nlc3MxIDAeBgNVBAMTF1ByaXZhdGUg
                SW50ZXJuZXQgQWNjZXNzMSAwHgYDVQQpExdQcml2YXRlIEludGVybmV0IEFjY2Vz
                czEvMC0GCSqGSIb3DQEJARYgc2VjdXJlQHByaXZhdGVpbnRlcm5ldGFjY2Vzcy5j
                b22CCQCmew+WL/O6gzAMBgNVHRMEBTADAQH/MA0GCSqGSIb3DQEBDQUAA4IBAQAn
                a5PgrtxfwTumD4+3/SYvwoD66cB8IcK//h1mCzAduU8KgUXocLx7QgJWo9lnZ8xU
                ryXvWab2usg4fqk7FPi00bED4f4qVQFVfGfPZIH9QQ7/48bPM9RyfzImZWUCenK3
                7pdw4Bvgoys2rHLHbGen7f28knT2j/cbMxd78tQc20TIObGjo8+ISTRclSTRBtyC
                GohseKYpTS9himFERpUgNtefvYHbn70mIOzfOJFTVqfrptf9jXa9N8Mpy3ayfodz
                1wiqdteqFXkTYoSDctgKMiZ6GdocK9nMroQipIQtpnwd4yBDWIyC6Bvlkrq5TQUt
                YDQ8z9v+DMO6iwyIDRiU
                -----END CERTIFICATE-----
            '''
        if filename == 'ca.rsa.4096.crt':
            # from https://www.privateinternetaccess.com/openvpn/ca.rsa.4096.crt
            fcontents = '''\
                -----BEGIN CERTIFICATE-----
                MIIHqzCCBZOgAwIBAgIJAJ0u+vODZJntMA0GCSqGSIb3DQEBDQUAMIHoMQswCQYD
                VQQGEwJVUzELMAkGA1UECBMCQ0ExEzARBgNVBAcTCkxvc0FuZ2VsZXMxIDAeBgNV
                BAoTF1ByaXZhdGUgSW50ZXJuZXQgQWNjZXNzMSAwHgYDVQQLExdQcml2YXRlIElu
                dGVybmV0IEFjY2VzczEgMB4GA1UEAxMXUHJpdmF0ZSBJbnRlcm5ldCBBY2Nlc3Mx
                IDAeBgNVBCkTF1ByaXZhdGUgSW50ZXJuZXQgQWNjZXNzMS8wLQYJKoZIhvcNAQkB
                FiBzZWN1cmVAcHJpdmF0ZWludGVybmV0YWNjZXNzLmNvbTAeFw0xNDA0MTcxNzQw
                MzNaFw0zNDA0MTIxNzQwMzNaMIHoMQswCQYDVQQGEwJVUzELMAkGA1UECBMCQ0Ex
                EzARBgNVBAcTCkxvc0FuZ2VsZXMxIDAeBgNVBAoTF1ByaXZhdGUgSW50ZXJuZXQg
                QWNjZXNzMSAwHgYDVQQLExdQcml2YXRlIEludGVybmV0IEFjY2VzczEgMB4GA1UE
                AxMXUHJpdmF0ZSBJbnRlcm5ldCBBY2Nlc3MxIDAeBgNVBCkTF1ByaXZhdGUgSW50
                ZXJuZXQgQWNjZXNzMS8wLQYJKoZIhvcNAQkBFiBzZWN1cmVAcHJpdmF0ZWludGVy
                bmV0YWNjZXNzLmNvbTCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoCggIBALVk
                hjumaqBbL8aSgj6xbX1QPTfTd1qHsAZd2B97m8Vw31c/2yQgZNf5qZY0+jOIHULN
                De4R9TIvyBEbvnAg/OkPw8n/+ScgYOeH876VUXzjLDBnDb8DLr/+w9oVsuDeFJ9K
                V2UFM1OYX0SnkHnrYAN2QLF98ESK4NCSU01h5zkcgmQ+qKSfA9Ny0/UpsKPBFqsQ
                25NvjDWFhCpeqCHKUJ4Be27CDbSl7lAkBuHMPHJs8f8xPgAbHRXZOxVCpayZ2SND
                fCwsnGWpWFoMGvdMbygngCn6jA/W1VSFOlRlfLuuGe7QFfDwA0jaLCxuWt/BgZyl
                p7tAzYKR8lnWmtUCPm4+BtjyVDYtDCiGBD9Z4P13RFWvJHw5aapx/5W/CuvVyI7p
                Kwvc2IT+KPxCUhH1XI8ca5RN3C9NoPJJf6qpg4g0rJH3aaWkoMRrYvQ+5PXXYUzj
                tRHImghRGd/ydERYoAZXuGSbPkm9Y/p2X8unLcW+F0xpJD98+ZI+tzSsI99Zs5wi
                jSUGYr9/j18KHFTMQ8n+1jauc5bCCegN27dPeKXNSZ5riXFL2XX6BkY68y58UaNz
                meGMiUL9BOV1iV+PMb7B7PYs7oFLjAhh0EdyvfHkrh/ZV9BEhtFa7yXp8XR0J6vz
                1YV9R6DYJmLjOEbhU8N0gc3tZm4Qz39lIIG6w3FDAgMBAAGjggFUMIIBUDAdBgNV
                HQ4EFgQUrsRtyWJftjpdRM0+925Y6Cl08SUwggEfBgNVHSMEggEWMIIBEoAUrsRt
                yWJftjpdRM0+925Y6Cl08SWhge6kgeswgegxCzAJBgNVBAYTAlVTMQswCQYDVQQI
                EwJDQTETMBEGA1UEBxMKTG9zQW5nZWxlczEgMB4GA1UEChMXUHJpdmF0ZSBJbnRl
                cm5ldCBBY2Nlc3MxIDAeBgNVBAsTF1ByaXZhdGUgSW50ZXJuZXQgQWNjZXNzMSAw
                HgYDVQQDExdQcml2YXRlIEludGVybmV0IEFjY2VzczEgMB4GA1UEKRMXUHJpdmF0
                ZSBJbnRlcm5ldCBBY2Nlc3MxLzAtBgkqhkiG9w0BCQEWIHNlY3VyZUBwcml2YXRl
                aW50ZXJuZXRhY2Nlc3MuY29tggkAnS7684Nkme0wDAYDVR0TBAUwAwEB/zANBgkq
                hkiG9w0BAQ0FAAOCAgEAJsfhsPk3r8kLXLxY+v+vHzbr4ufNtqnL9/1Uuf8NrsCt
                pXAoyZ0YqfbkWx3NHTZ7OE9ZRhdMP/RqHQE1p4N4Sa1nZKhTKasV6KhHDqSCt/dv
                Em89xWm2MVA7nyzQxVlHa9AkcBaemcXEiyT19XdpiXOP4Vhs+J1R5m8zQOxZlV1G
                tF9vsXmJqWZpOVPmZ8f35BCsYPvv4yMewnrtAC8PFEK/bOPeYcKN50bol22QYaZu
                LfpkHfNiFTnfMh8sl/ablPyNY7DUNiP5DRcMdIwmfGQxR5WEQoHL3yPJ42LkB5zs
                6jIm26DGNXfwura/mi105+ENH1CaROtRYwkiHb08U6qLXXJz80mWJkT90nr8Asj3
                5xN2cUppg74nG3YVav/38P48T56hG1NHbYF5uOCske19F6wi9maUoto/3vEr0rnX
                JUp2KODmKdvBI7co245lHBABWikk8VfejQSlCtDBXn644ZMtAdoxKNfR2WTFVEwJ
                iyd1Fzx0yujuiXDROLhISLQDRjVVAvawrAtLZWYK31bY7KlezPlQnl/D9Asxe85l
                8jO5+0LdJ6VyOs/Hd4w52alDW/MFySDZSfQHMTIc30hLBJ8OnCEIvluVQQ2UQvoW
                +no177N9L2Y+M9TcTA62ZyMXShHQGeh20rb4kK8f+iFX8NxtdHVSkxMEFSfDDyQ=
                -----END CERTIFICATE-----
            '''
        if filename == 'crl.rsa.2048.pem':
            # from https://www.privateinternetaccess.com/openvpn/openvpn.zip
            fcontents = '''\
                -----BEGIN X509 CRL-----
                MIICWDCCAUAwDQYJKoZIhvcNAQENBQAwgegxCzAJBgNVBAYTAlVTMQswCQYDVQQI
                EwJDQTETMBEGA1UEBxMKTG9zQW5nZWxlczEgMB4GA1UEChMXUHJpdmF0ZSBJbnRl
                cm5ldCBBY2Nlc3MxIDAeBgNVBAsTF1ByaXZhdGUgSW50ZXJuZXQgQWNjZXNzMSAw
                HgYDVQQDExdQcml2YXRlIEludGVybmV0IEFjY2VzczEgMB4GA1UEKRMXUHJpdmF0
                ZSBJbnRlcm5ldCBBY2Nlc3MxLzAtBgkqhkiG9w0BCQEWIHNlY3VyZUBwcml2YXRl
                aW50ZXJuZXRhY2Nlc3MuY29tFw0xNjA3MDgxOTAwNDZaFw0zNjA3MDMxOTAwNDZa
                MCYwEQIBARcMMTYwNzA4MTkwMDQ2MBECAQYXDDE2MDcwODE5MDA0NjANBgkqhkiG
                9w0BAQ0FAAOCAQEAQZo9X97ci8EcPYu/uK2HB152OZbeZCINmYyluLDOdcSvg6B5
                jI+ffKN3laDvczsG6CxmY3jNyc79XVpEYUnq4rT3FfveW1+Ralf+Vf38HdpwB8EW
                B4hZlQ205+21CALLvZvR8HcPxC9KEnev1mU46wkTiov0EKc+EdRxkj5yMgv0V2Re
                ze7AP+NQ9ykvDScH4eYCsmufNpIjBLhpLE2cuZZXBLcPhuRzVoU3l7A9lvzG9mjA
                5YijHJGHNjlWFqyrn1CfYS6koa4TGEPngBoAziWRbDGdhEgJABHrpoaFYaL61zqy
                MR6jC0K2ps9qyZAN74LEBedEfK7tBOzWMwr58A==
                -----END X509 CRL-----
            '''
        if filename == 'ca.crt':
            # from wget https://www.privateinternetaccess.com/openvpn/ca.crt
            fcontents = '''\
                -----BEGIN CERTIFICATE-----
                MIID2jCCA0OgAwIBAgIJAOtqMkR2JSXrMA0GCSqGSIb3DQEBBQUAMIGlMQswCQYD
                VQQGEwJVUzELMAkGA1UECBMCT0gxETAPBgNVBAcTCENvbHVtYnVzMSAwHgYDVQQK
                ExdQcml2YXRlIEludGVybmV0IEFjY2VzczEjMCEGA1UEAxMaUHJpdmF0ZSBJbnRl
                cm5ldCBBY2Nlc3MgQ0ExLzAtBgkqhkiG9w0BCQEWIHNlY3VyZUBwcml2YXRlaW50
                ZXJuZXRhY2Nlc3MuY29tMB4XDTEwMDgyMTE4MjU1NFoXDTIwMDgxODE4MjU1NFow
                gaUxCzAJBgNVBAYTAlVTMQswCQYDVQQIEwJPSDERMA8GA1UEBxMIQ29sdW1idXMx
                IDAeBgNVBAoTF1ByaXZhdGUgSW50ZXJuZXQgQWNjZXNzMSMwIQYDVQQDExpQcml2
                YXRlIEludGVybmV0IEFjY2VzcyBDQTEvMC0GCSqGSIb3DQEJARYgc2VjdXJlQHBy
                aXZhdGVpbnRlcm5ldGFjY2Vzcy5jb20wgZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJ
                AoGBAOlVlkHcxfN5HAswpryG7AN9CvcvVzcXvSEo91qAl/IE8H0knKZkIAhe/z3m
                hz0t91dBHh5yfqwrXlGiyilplVB9tfZohvcikGF3G6FFC9j40GKP0/d22JfR2vJt
                4/5JKRBlQc9wllswHZGmPVidQbU0YgoZl00bAySvkX/u1005AgMBAAGjggEOMIIB
                CjAdBgNVHQ4EFgQUl8qwY2t+GN0pa/wfq+YODsxgVQkwgdoGA1UdIwSB0jCBz4AU
                l8qwY2t+GN0pa/wfq+YODsxgVQmhgaukgagwgaUxCzAJBgNVBAYTAlVTMQswCQYD
                VQQIEwJPSDERMA8GA1UEBxMIQ29sdW1idXMxIDAeBgNVBAoTF1ByaXZhdGUgSW50
                ZXJuZXQgQWNjZXNzMSMwIQYDVQQDExpQcml2YXRlIEludGVybmV0IEFjY2VzcyBD
                QTEvMC0GCSqGSIb3DQEJARYgc2VjdXJlQHByaXZhdGVpbnRlcm5ldGFjY2Vzcy5j
                b22CCQDrajJEdiUl6zAMBgNVHRMEBTADAQH/MA0GCSqGSIb3DQEBBQUAA4GBAByH
                atXgZzjFO6qctQWwV31P4qLelZzYndoZ7olY8ANPxl7jlP3YmbE1RzSnWtID9Gge
                fsKHi1jAS9tNP2E+DCZiWcM/5Y7/XKS/6KvrPQT90nM5klK9LfNvS+kFabMmMBe2
                llQlzAzFiIfabACTQn84QLeLOActKhK8hFJy2Gy6
                -----END CERTIFICATE-----
            '''
        if filename == 'credentials.txt':
            fcontents = '''\
                {user}
                {pw}
            '''.format(user=data['vpn_username'], pw=data['vpn_password'])
        if filename == 'client.conf':
            fcontents = '''\
                client
                dev tun
                proto udp
                # mssfix is needed to solve MTU issues (VPN stall) on some networks
                # FIXME: for better throughput on correct links, don't use ...
                #     'mssfix' unless needed; see ...
                #      https://www.privateinternetaccess.com/archive/forum/discussion/4603
                mssfix 1400
                remote {server} 1198
                resolv-retry infinite
                nobind
                persist-key
                persist-tun
                cipher aes-128-cbc
                auth sha1
                tls-client
                remote-cert-tls server
                cd /etc/openvpn
                auth-user-pass credentials.txt
                # 'auth-nocache' appears to greatly reduce AUTH_FAILED errors ...
                #     (64% -> 6% in a quick test)
                auth-nocache
                # 'pull-filter ignore "auth-token"' seems eliminate errors on OpenVPN 2.4; ...
                #     see https://www.privateinternetaccess.com/forum/discussion/24089
                pull-filter ignore "auth-token"
                crl-verify crl.rsa.2048.pem
                ca ca.rsa.2048.crt
                reneg-sec 0
                comp-lzo yes
                verb 3
                mute-replay-warnings
                log /tmp/openvpn.log
                daemon
            '''.format(server=data['vpn_server_host'])
        if filename == 'restart-if-needed.sh':
            # the OpenVPN default '--ping-restart 120' seems to not always recover connectivity
            fcontents = '''\
                #!/bin/sh
                vpn_endp=$( \\
                    ip route  \\
                    |grep '^10\.[0-9\.]* via 10\.[0-9\.]* dev tun'  \\
                    |grep -o '^[0-9\.]*' \\
                )
                restart=0
                if ! pidof openvpn ; then restart=1; fi
                if ! ip route |grep '^128\.0\.0\.0/1 via .* dev tun' ; then restart=1; fi
                if ! ping -q -c1 -W4 $vpn_endp |grep '1 packets received' ; then restart=1; fi
                if ! (
                    ping -q -c1 -W4 8.8.8.8 |grep '1 packets received' ||
                    ping -q -c1 -W4 141.1.1.1 |grep '1 packets received'
                ) ; then restart=1; fi
                if [ $restart == 1 ] ; then
                    killall openvpn && sleep 2
                    killall -9 openvpn && sleep 2
                    /usr/sbin/openvpn \\
                        --syslog 'openvpn(vpnas)' \\
                        --status /var/run/openvpn.vpnas.status \\
                        --cd /etc/openvpn \\
                        --config /etc/openvpn/client.conf
                fi
            '''
        return textwrap.dedent(fcontents).encode()

    def files():
        return {
            #filename               :  target directory on router
            'ca.rsa.2048.crt'       : '/etc/openvpn',
            'ca.rsa.4096.crt'       : '/etc/openvpn',
            'crl.rsa.2048.pem'      : '/etc/openvpn',
            'ca.crt'                : '/etc/openvpn',
            'credentials.txt'       : '/etc/openvpn',
            'client.conf'           : '/etc/openvpn',
            'restart-if-needed.sh'  : '/etc/openvpn',
        }


def generate_new_password(length = 12):
    """Return a new, secure, random password of the given length"""
    # pass_chars does not include visually similar characters
    pass_chars = r'''abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789''' 
    return ''.join(secrets.choice(pass_chars) for i in range(length))


def hashed_md5_password(password, salt=None): # https://stackoverflow.com/a/27282771/10590519
    """Return the Linux-format hashed password. The salt, if specified, must begin with
    '$' followed by an id as listed in the 'crypt' man page. If no salt is given, an MD5 salt
    is generaged for compatibility with older systems."""
    if salt == None:
        salt = crypt.mksalt(crypt.METHOD_MD5) # begins '$1$', e.g. '$1$D6/56C4p'
    # cli equivalent to crypt.crypt(): openssl passwd -1 -salt $PLAIN_SALT $PASSWORD
    return crypt.crypt(password, salt)


def generate_ssh_key_pair(): # based on https://stackoverflow.com/a/39126754/10590519
    """Return a tuple containing new public and private keys."""
    key = rsa.generate_private_key(
        backend=crypto_default_backend(),
        public_exponent=65537,
        key_size=2048
    )
    private_key = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.PKCS8,
        crypto_serialization.NoEncryption()
    ).decode()
    public_key = key.public_key().public_bytes(
        crypto_serialization.Encoding.OpenSSH,
        crypto_serialization.PublicFormat.OpenSSH
    ).decode()
    # 'RSA' needs to be in header; looks like https://github.com/paramiko/paramiko/issues/1226
    return (public_key, private_key.replace('-BEGIN PRIVATE KEY-', '-BEGIN RSA PRIVATE KEY-')
                                   .replace('-END PRIVATE KEY-', '-END RSA PRIVATE KEY-'))


def add_line_breaks(long_string, line_len=70):
    return '\n'.join(long_string[i:i+line_len] for i in range(0, len(long_string), line_len))


def possible_router_ips():
    """Return a list of IP addresses which may be a router - currently first IP of each subnet."""
    possible_routers = [] # items are type ipaddress.ip_address
    for intf in netifaces.interfaces(): # e.g. eth0, lo
        for ip_ver in [netifaces.AF_INET, netifaces.AF_INET6]: # IPv4 then IPv6
            if ip_ver in netifaces.ifaddresses(intf): # if this interface has at least one address
                for a in netifaces.ifaddresses(intf)[ip_ver]:
                    if 'addr' in a and 'netmask' in a:
                        addr = a['addr'].split('%')[0] # strip away '%' and interface name
                        prefix_len = bin(
                            int.from_bytes(
                                ipaddress.ip_address(a['netmask']).packed,
                                byteorder='big'
                            )
                        ).count('1')
                        subnet = ipaddress.ip_network(addr + '/' + str(prefix_len), strict=False)
                        if (prefix_len < subnet.max_prefixlen # not a /32 (IPv4) address
                                and not ipaddress.ip_address(addr).is_link_local): # not link local
                            first_ip = subnet[1] # assume router is first IP in subnet
                            if not first_ip == ipaddress.ip_address(addr): # if not our IP
                                possible_routers.append(first_ip)
    return possible_routers


def ssh_keyscan(ip, port=22):
    try:
        transport = paramiko.Transport((ip, port)) # FIXME: may block for a very long time
        transport.connect()
        key = transport.get_remote_server_key()
        transport.close()
        return key.get_name() + ' ' + key.get_base64()
    except (paramiko.ssh_exception.SSHException, gaierror):
        return None


def new_nickname(mac=None):
    manuf = ''
    known_macs = '''
    # small subset of OUI database from ...
    #     https://code.wireshark.org/review/gitweb?p=wireshark.git;a=blob_plain;f=manuf
    # note literal tab characters don't work
    E4:95:6E:40:00:00/28  GL.iNet
    B8:27:EB              Raspberry Pi
    94:B8:6D              Intel
    9C:B6:D0              RivetNet
    '''
    if mac != None and mac != '00:00:00:00:00:00':
        # mac_digits is mac without separators
        mac_digits = mac.translate({ord(c):None for c in [':', '-', '.', ' ']}).lower()
        r_line = re.compile(r'^\s*([0-9a-fA-F:\.-]+)(/[0-9]+)?\s+([^#]+)')
        r_comment = re.compile(r'^\s*(#.*)?$')
        for line in known_macs.split('\n'):
            match = r_line.match(line)
            if match:
                mask = 24 if match[2] == None else int(re.sub(r'\D', '', match[2]))
                assert (mask/4).is_integer(), "mask not multiple of 4: {}".format(line)
                mask_div_4 = int(mask/4) # ¼ of address mask is the number of hex digits needed
                line_digits = match[1].translate(
                    {ord(c):None for c in [':', '-', '.', ' ']}
                ).lower()
                if mac_digits[0:mask_div_4] == line_digits[0:mask_div_4]:
                    manuf = ' ' + match[3].rstrip()
            elif not r_comment.match(line):
                raise CGError("Invalid OUI line: {}".format(line))
        return 'new' + manuf + ' device'


class Router(yaml.YAMLObject):
    yaml_loader = yaml.SafeLoader
    yaml_tag = '!Router' # https://stackoverflow.com/a/2890073/10590519

    def __init__(self, ip, mac):
        assert mac != None and mac != '00:00:00:00:00:00'
        self.ip = str(ip)
        self.mac = mac
        self.nickname = new_nickname(mac)
        self.create = time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime())
        self.version_map = ''
        self.client = None

    def generate_passwords(self):
        self.first_password = generate_new_password(length=12)
        self.router_password = generate_new_password(length=12)
        self.wifi_password = generate_new_password(length=10)

    def generate_ssh_keys(self):
        # instead of ssh-keyscan, a safer option would be to convert ...
        #     /etc/dropbear/dropbear_rsa_host_key to OpenSSH format; see ...
        #     https://github.com/mkj/dropbear/blob/master/dropbearconvert.c
        self.ssh_hostkey = add_line_breaks(ssh_keyscan(self.ip), line_len=64) # 64 is privkey width
        (pub, priv) = generate_ssh_key_pair()
        self.ssh_pubkey = add_line_breaks(pub, line_len=64)
        self.ssh_privkey = priv

    def set_password_on_router(self):
        # it is also possible to set the router password via http, but this is ...
        #     programmatically more complex, plus on older GL-iNet firmware, this ...
        #     changes the WiFi password as well
        # it would be more secure to use first_password below, and then set it again ...
        #     with router_password via ssh
        root_shadow_line = 'root:' + hashed_md5_password(self.router_password) + ':0:0:99999:7:::'
        # possible better way to do following line: re.sub(r' *\r*[\t\n] *', '', self.ssh_pubkey)
        authorized_keys_line = self.ssh_pubkey.translate({ord(c):None for c in ['\t', '\n', '\r']})
        prompt = '[\r\n]root@'
        exit_cmd = 'exit\n'
        phase1 = {
            '[Ll]]ogin:' : 'root\n',
            '[Pp]assword:' : '\n',
            prompt : None, # None == we have arrived
        }
        phase2 = [
            'cat /etc/openwrt_release\n', # info for the logs
            'uname -a\n',
            'lsb_release -d\n',
            'echo 12③4✔\n',
            '''echo '{}' >/tmp/shadow\n'''.format(root_shadow_line),
            '''grep -v '^root:' /etc/shadow >>/tmp/shadow\n''',
            '''mv /tmp/shadow /etc/shadow\n''',
            '''echo '{}' >>/etc/dropbear/authorized_keys\n'''.format(authorized_keys_line),
            exit_cmd, # exit_cmd must be last item in list
        ]
        # after above 'mv' command, this should connect you to router:
        #     ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@192.168.8.1
        phase1_prompts = [re.compile(p.encode()) for p in phase1]
        esc_seq_re = re.compile(r'\x1b\[[0-9;]+m')
        print_msg(1, "<telnet_log>")
        try:
            with telnetlib.Telnet(self.ip, timeout=5) as t:
                cycles = 0
                while cycles < 7: # phase 1 - logging into router
                    (index, __, data) = t.expect(phase1_prompts, timeout=5)
                    print_msg(1, ''.join(esc_seq_re.split(data.decode())), end='')
                    if index >=0:
                        to_send = phase1[phase1_prompts[index].pattern.decode()]
                        if to_send == None:
                            break
                        t.write(to_send.encode())
                    else:
                        raise CGError("Timeout connecting to {}".format(self.nickname))
                    cycles += 1
                if cycles >= 7:
                    raise CGError("Unable to log in to {}".format(self.nickname))
                for to_send in phase2: # phase 2 - commands to send router
                    try:
                        t.write(to_send.encode())
                        (__, __, data) = t.expect([re.compile(prompt.encode())], timeout=3)
                    except EOFError:
                        if to_send == exit_cmd: # successful disconnect
                            pass
                    print_msg(1, ''.join(esc_seq_re.split(data.decode())), end='')
                print_msg(1, '') # make sure we end with a newline
        except (ConnectionRefusedError, EOFError):
            raise CGError("Unable to connect to {} at {}. ".format(self.nickname, self.ip)
                    + "Please factory-reset your router and try again.")
        print_msg(1, "</telnet_log>")

    def connect_ssh(self):
        if self.client != None:
            return
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.RejectPolicy) # ensure correct host key
        # host key (normally in ~/.ssh/known_hosts)
        hostkey = self.ssh_hostkey.split(' ')
        self.client.get_host_keys().add(
            self.ip, 
            hostkey[0], 
            paramiko.RSAKey(data=base64.b64decode(hostkey[1]))
        )
        # private key (normally in ~/.ssh/id_rsa)
        privkey_file = io.StringIO()
        privkey_file.write(self.ssh_privkey)
        privkey_file.seek(0)
        privkey = paramiko.RSAKey.from_private_key(privkey_file)
        connect_method = 'none'
        try: # first try to connect using private ssh key
            self.client.connect(
                hostname=self.ip,
                username='root',
                pkey=privkey,
                # don't use password this time because we want to know if ssh key fails; ...
                #     could improve speed by using low-level class, but key should normally ...
                #     work so not worth it; see https://stackoverflow.com/questions/54296230
                password=None,
                allow_agent=False,
                look_for_keys=False,
            )
            connect_method = 'ssh key'
        except paramiko.ssh_exception.AuthenticationException:
            try: # if private ssh key fails, try the password
                self.client.connect(
                    hostname=self.ip,
                    username='root',
                    pkey=None,
                    password=self.router_password,
                    allow_agent=False,
                    look_for_keys=False,
                )
                print_msg(1, "Warning: connecting via ssh key failed")
                connect_method = 'password'
            except paramiko.ssh_exception.AuthenticationException:
                self.client = None
        self.last_connect = (time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime()) 
                + " {}".format(connect_method))
        print_msg(1, "Connected to {} via {}".format(self.nickname, connect_method))

    def exec(self, command, okay_to_fail=False):
        print_msg(1, 'Router cmd:    ' + command)
        (__, stdout, stderr) = self.client.exec_command(command)
        exitc = stdout.channel.recv_exit_status()
        out = ''
        out_count = 0
        for line in stdout:
            out += line
            out_count += 1
            print_msg(1, 'Router stdout: ' + line.rstrip())
        err0 = ''
        err_count = 0
        for line in stderr:
            if err_count == 0:
                err0 = line.rstrip()
            err_count += 1
            print_msg(1, 'Router stderr: ' + line.rstrip())
        if exitc != 0:
            if okay_to_fail:
                return(err0)
            else:
                raise RemoteExecutionError("Error running '{}' on router: {}"
                        .format(command, err0))
        return out.rstrip() if out_count==1 else out

    def put(self, data, remote_path):
        # SFTP would be nice, but OpenWrt only supports SCP
        scp = SCPClient(self.client.get_transport()) # https://github.com/jbardin/scp.py
        data_file = io.BytesIO() # in-memory file-like object
        data_file.write(data)
        data_file.seek(0)
        scp.putfo(data_file, remote_path)
        scp.close()
        data_file.close()

    def close(self):
        if self.client:
            print_msg(1, "Closing client connection")
            self.client.close()
            self.client = None

    def install_files(self):
        vpn_conf = {
                'vpn_username'    : self.vpn_username,
                'vpn_password'    : self.vpn_password,
                'vpn_server_host' : self.vpn_server_host,
        }
        for f, d in PrivateInternetAccess.files().items():
            self.put(PrivateInternetAccess.file(filename=f, data=vpn_conf), d + '/' + f)

    def update_group(self, name, from_ver, to_ver, code):
        if from_ver >= to_ver: # FIXME: update needed if any {...} values changed
            return
        print_msg(1, "Updating from {}{} to {}{}".format(name, from_ver, name, to_ver))
        for line in code:
            first_word = line.split(' ')[0]
            if first_word == 'cg:install-files':
                self.install_files()
            elif first_word == 'cg:assert': # very simplistic parser
                # following line based on https://stackoverflow.com/a/2787064/10590519
                r = re.compile(r'''((?:[^ "'`]|"[^"]*"|'[^']*'|`[^`]*`)+)''')
                words = r.split(line)[1::2]
                tokens = [] # words without quotes
                for w in words:
                    q = w[0]
                    if q == '#':
                        break; # comment - ignore rest of line
                    if q == '"' or q == "'":
                        tokens.append(w[1:-1])
                    elif q == '`': # use backticks as in bash shell
                        tokens.append(self.exec(w[1:-1])) # output when executed on router
                    else:
                        tokens.append(w)
                if len(tokens) != 4 or (tokens[2] != '==' and tokens[2] != '!='):
                    raise CGError("Error parsing: {}".format(line))
                if (tokens[2] == '==') ^ (tokens[1] == tokens[3]):
                    raise RemoteExecutionError("Assertion failed: {}".format(line))
            else:
                self.exec(line)

    def update_groups(self, code_text):
        groups_updated_count = 0
        http_password_sha256 = sha256(self.router_password.encode()).hexdigest()
        code = code_text.format(
            http_password_sha256 = http_password_sha256,
            wifi_password = self.wifi_password,
        )
        versions = {} # router's current version number for each group
        for group in re.split(r'\s+', self.version_map): # parse current version map from conf file
            if len(group) == 0:
                continue
            m = re.match(r'([a-z]+)([0-9]+)', group)
            if m:
                versions[m[1]] = int(m[2])
            else:
                raise CGError("Invalid group name or version: {}".format(group))
        line_re = re.compile(r'\n\s*')
        group_title_re = re.compile(r'^---\s+group\s+([a-z]+)([0-9]+)($|\s)')
        gname = None
        gver = None
        gcode = []
        names_seen = set()
        try:
            for line in line_re.split(code): # parse code text blob and execute commands on router
                if len(line) == 0 or line[0] == '#':
                    continue
                m = group_title_re.match(line)
                if m:
                    if gname: # group title signals end of prior group, so execute now
                        # following line may raise RemoteExecutionError
                        self.update_group(gname, versions[gname], gver, gcode)
                        if versions[gname] != gver:
                            versions[gname] = gver # successful - update to new version number
                            groups_updated_count += 1
                    gname = m[1]
                    gver = int(m[2])
                    gcode = []
                    if gname not in versions:
                        versions[gname] = 0
                    assert gver > 0, "version for group '{}' must be positive".format(gname)
                    assert gname not in names_seen, "group '{}' listed twice".format(gname)
                    names_seen.add(gname)
                else:
                    gcode.append(line)
            assert gcode == [], "final group '{}' must have no code".format(gname)
            del versions[gname] # don't store final group in conf file
        except RemoteExecutionError as err:
            print_msg(1, err)
            raise
        finally: # make sure version_map gets updated, even if success is only partial
            versions_text = ' '.join([g+str(v) for g, v in versions.items()])
            vt_width = 64 if len(versions_text) > 64 else 52
            self.version_map = '\n'.join(textwrap.wrap(versions_text, width=vt_width))
        return groups_updated_count


class Config():

    def __init__(self):
        self.dir = os.path.expanduser('~/.cleargopher')
        try:
            os.mkdir(self.dir)
        except FileExistsError:
            pass
        self.__conf_path__ = os.path.join(self.dir, 'cleapher.conf')

    # def str_representer(dumper, data):
    #     return dumper.represent_str(str(data))

    def long_str_representer(dumper, data): # https://stackoverflow.com/a/33300001/10590519
        if len(data.splitlines()) > 1:  # check for multiline string
            return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
        return dumper.represent_scalar('tag:yaml.org,2002:str', data)

    def load():
        self = Config()
        try:
            with open(self.__conf_path__, 'r') as conf_file:
                try:
                    self.routers = yaml.safe_load(conf_file.read())
                except yaml.YAMLError as yaml_err:
                    raise CGError("Error parsing {}: {}".format(self.__conf_path__, yaml_err))
        except FileNotFoundError:
            self.routers = [] # no config file - start fresh
        if self.routers == None:
            self.routers = [] # empty config file - start fresh
        for r in self.routers:
            r.client = None
        return self
    
    def save(self):
        # yaml.add_representer(ipaddress.IPv4Address, Config.str_representer)
        # yaml.add_representer(ipaddress.IPv6Address, Config.str_representer)
        yaml.add_representer(str, Config.long_str_representer)
        try:
            header = ("Clear Gopher YAML configuration file - be very careful when editing " 
                    + "because indent, colons, and many other characters have special meaning")
            body = yaml.dump(self.routers, default_flow_style=False)
            with open(self.__conf_path__+'.0', 'w') as conf_file:
                os.chmod(self.__conf_path__+'.0', 0o600) # protect passwords, keys from other users
                conf_file.write('# ' + '\n# '.join(textwrap.wrap(header, width=66)) + '\n')
                # don't save routers.client
                conf_file.write(re.sub(r'\n *client:[^\n]+\n', '\n', body))
        except OSError as err:
            raise CGError("Error saving configuration {}: {}".format(self.__conf_path__+'.0', err))
        try:
            os.rename(self.__conf_path__, self.__conf_path__+'.bak') # keep a backup
            os.rename(self.__conf_path__+'.0', self.__conf_path__) # move new version to real name
        except FileNotFoundError as err:
            raise CGError("Error saving configuration {}: {}".format(self.__conf_path__, err))


### main ###
def main():
    conf = Config.load()
    # FIXME: connect to correct WiFi network - maybe python-networkmanager
    ip_list_full = [ipaddress.ip_address(r.ip) for r in conf.routers] # IPs from config file
    ip_list_full += possible_router_ips() # first IP of each detected network
    # note ip_list_full will normally include 192.168.8.1
    ip_list = [i for n,i in enumerate(ip_list_full) if i not in ip_list_full[:n]] # kill duplicates
    mac_to_ip = {}
    router_options = [] # computed list of what could be a router
    for ip in ip_list: # for each IP that might be a router
        if isinstance(ip, ipaddress.IPv4Address):
            mac = getmac.get_mac_address(ip=str(ip))
        elif isinstance(ip, ipaddress.IPv6Address):
            mac = getmac.get_mac_address(ip6=str(ip))
        else:
            raise TypeError("ip must be ipaddress")
        if mac == None: # unroutable IP
            continue
        if mac == '00:00:00:00:00:00': # unreachable (no host at IP)
            continue
        if mac in mac_to_ip: # duplicate MAC
            continue
        mac_to_ip[mac] = ip
        found = False
        hostkey = add_line_breaks(ssh_keyscan(str(ip)), line_len=64) # takes a few seconds
        # note we don't match based on MAC because routers can be reset, plus some ...
        #     routers generate the MAC address for certain interfaces at boot time
        for r in conf.routers: # look for matching hostkey in conf data
            if r.ssh_hostkey == hostkey:
                r.ip = str(ip) # update IP if it has changed since config file was saved
                r.mac = mac # update MAC if it has changed
                router_options.append(r)
                found = True
                break
        if not found:
            r = Router(ip, mac) # previously-unknown router
            router_options.append(r)
    if len(router_options) > 1:
        err = ''
        for r in router_options:
            err += "Possible router: {} (ip {}, mac {})\n".format(r.nickname, r.ip, r.mac)
        raise CGError(err + "Multiple possible routers found") # FIXME: allow user to choose one
    if len(router_options) == 0:
        raise CGError("No possible routers found") # FIXME: help user get router connected
    try:
        router = router_options[0]
        print_msg(1, "Using router {} (ip {}, mac {})".format(r.nickname, r.ip, r.mac))
        try:
            router.router_password
        except AttributeError: # if no passwords, then it's a previously-unknown router
            router.generate_passwords()
            router.generate_ssh_keys()
            # FIXME: guide user on setting up a new PIA account (i.e. ...
            #     sign up at https://www.privateinternetaccess.com/, check email, etc.)
            router.vpn_username = input("Enter the PIA username to use on this router: ")
            router.vpn_password = input("Enter the PIA password to use on this router: ")
            # FIXME: guide user on choosing region; see ...
            #     https://www.privateinternetaccess.com/pages/network/
            router.vpn_server_host = input("Enter the PIA region to use on this router: ")
            conf.routers.append(router)
            conf.save()
            router.set_password_on_router()
        router.connect_ssh()
        if router.client == None: # couldn't authenticate - maybe router was reset
            print_msg(1, "Unable to connect to {} at {}. Trying to reset password."
                    .format(router.nickname, router.ip))
            router.set_password_on_router()
            router.connect_ssh()
        if router.client == None: # couldn't authenticate
            raise CGError("Unable to connect to {} at {}.".format(router.nickname, router.ip))
        # group titles must begin (rest of line is a comment): --- group {name}
        # group names must be lowercase letters followed by a version number > 0
        # in-line comments are allowed but sent to router
        # newline within quotes must be written: \\n
        groups_gl_inet = '''
            --- group sysinfoa1 ---
            # FIXME: don't abort if commands in this group fail
            uname -a
            date --utc '+%Y-%m-%d_%H:%M:%S'
            cat /etc/banner |grep -v -e '^ ---------------' -e '^  \* ' -e '^ |' -e '^  __'
            cat /etc/glversion
            cat /etc/openwrt_release
            cat /proc/cpuinfo
            opkg print-architecture
            traceroute -n -m 6 141.1.1.1
            --- group sysinfob1 ---
            #uptime
            #ip address show
            #ip rule show
            #ip route show table all
            #ls -l /etc/openvpn
            #cat /etc/openvpn/*.conf
            #cat /etc/config/openvpn |grep -v -e '^#' -e '^\W#' -e '^$'
            #cat /etc/firewall.user
            #uci show |grep -v '^wireless..wifi-iface....key='
            #cat /tmp/openvpn.log
            #iptables-save
            --- group safecheck1 --- # verify router WiFi password has not yet been ...
            #     changed; FIXME: allow user to continue anyhow
            cg:assert `uci get wireless.@wifi-iface[0].key` == 'goodlife'
            --- group pwlangtz1 passwords, timezone ---
            uci set glconfig.general.password={http_password_sha256}
            uci set wireless.@wifi-iface[0].key={wifi_password} # does not take effect until ...
            #     router is rebooted
            uci set glconfig.general.language=en # choose English for the http UI
            uci set luci.main.lang=en
            uci set system.@system[0].zonename=UTC # use UTC
            uci set system.@system[0].timezone=GMT0
            echo GMT0 >/etc/TZ
            uci commit # save changes on router
            --- group filesa1 ---
            mkdir -p /etc/openvpn
            --- group filesb1 ---
            cg:install-files # copy files to router via Router.install_files()
            --- group filesc1 ---
            chmod 660 /etc/openvpn/*
            chmod 770 /etc/openvpn/restart-if-needed.sh
            --- group dns1 ---
            # set specific DNS servers so that the ISP's servers are not used
            # FIXME: uci commands using '[-1]' cannot be harmlessly re-run; maybe use a ...
            #     'from' and 'to' version for each group
            uci add_list dhcp.@dnsmasq[-1].server='9.9.9.9'
            uci add_list dhcp.@dnsmasq[-1].server='149.112.112.112'
            uci add_list dhcp.@dnsmasq[-1].noresolv=1
            uci set network.wan.peerdns=0
            uci set network.wan.custom_dns=1
            uci set network.wan.dns='9.9.9.9 149.112.112.112'
            uci set glconfig.general.force_dns=yes
            uci commit
            --- group sysctl1 ---
            # note IPv6 should be disabled until we can properly address the security ...
            #     implications; see ...
            #     https://www.privateinternetaccess.com/helpdesk/kb/articles/why-do-you-block-ipv6
            # FIXME: needs blank line and comment before these lines, but then ...
            #     wouldn't be re-doable
            grep -v -e ^net.ipv6.conf.all.disable_ipv6 -e ^net.ipv6.conf.default.disable_ipv6 -e ^net.ipv6.conf.lo.disable_ipv6 /etc/sysctl.conf >/tmp/sysctl
            echo 'net.ipv6.conf.all.disable_ipv6=1' >>/tmp/sysctl
            echo 'net.ipv6.conf.default.disable_ipv6=1' >>/tmp/sysctl
            echo 'net.ipv6.conf.lo.disable_ipv6=1' >>/tmp/sysctl
            cp /tmp/sysctl /etc/sysctl.conf
            --- group dhcpsix1 ---
            # prevent 'dhcp6 solicit' to the ISP
            # FIXME: uci commands using '[-1]' cannot be harmlessly re-run
            uci add firewall rule
            uci set firewall.@rule[-1].name='Block all IPv6 to ISP'
            uci set firewall.@rule[-1].dest=wan
            uci set firewall.@rule[-1].family=ipv6
            uci set firewall.@rule[-1].target=REJECT
            uci commit firewall
            --- group ovpn1 ---
            # configure OpenVPN
            uci delete firewall.@forwarding[]
            uci set firewall.vpn_zone=zone
            uci set firewall.vpn_zone.name=VPN_client
            uci set firewall.vpn_zone.input=ACCEPT
            uci set firewall.vpn_zone.forward=REJECT
            uci set firewall.vpn_zone.output=ACCEPT
            uci set firewall.vpn_zone.network=VPN_client
            uci set firewall.vpn_zone.masq=1
            uci set firewall.forwarding_vpn1=forwarding
            uci set firewall.forwarding_vpn1.dest=VPN_client
            uci set firewall.forwarding_vpn1.src=lan
            uci set network.VPN_client=interface
            uci set network.VPN_client.proto=none
            uci set network.VPN_client.ifname=tun0
            uci set system.vpn=led
            uci set system.vpn.default=0
            uci set system.vpn.name=vpn
            uci set system.vpn.sysfs='gl-ar300m:lan'
            uci set system.vpn.trigger=netdev
            uci set system.vpn.dev=tun0
            uci set system.vpn.mode='link tx rx'
            uci commit
            --- group opkga1 ---
            # install OpenVPN and iptables tools (OpenVPN is pre-installed on GL-iNet routers)
            # FIXME: 'opkg update' may take a long time so provide status to user
            opkg update # FIXME: if opkg fails, reboot router and retry
            if   [ $(grep -o '^[0-9]*' /etc/openwrt_version) -lt 15 ] ; then opkg install openvpn; fi # OpenWrt older than Chaos Calmer
            if ! [ $(grep -o '^[0-9]*' /etc/openwrt_version) -lt 15 ] ; then opkg install openvpn-openssl; fi # Chaos Calmer and later
            --- group opkgb1 ---
            if ! ( [ -f /tmp/opkg-lists/packages ] || [ -f /tmp/opkg-lists/*_packages ] ) ; then opkg update; fi # FIXME: if opkg fails, reboot router and retry
            opkg install kmod-ipt-filter iptables-mod-filter # for iptables --match string
            --- group noleak1 ---
            # prevent leaking data to the ISP
            # FIXME: uci commands using '[-1]' cannot be harmlessly re-run
            uci add firewall rule
            uci set firewall.@rule[-1].name='Block all DNS to ISP except *.privateinternetaccess.com'
            uci set firewall.@rule[-1].dest=wan
            uci set firewall.@rule[-1].family=ipv4
            uci set firewall.@rule[-1].proto=tcpudp
            uci set firewall.@rule[-1].dest_port=53
            uci set firewall.@rule[-1].extra='--match string --algo bm ! --hex-string |15|privateinternetaccess|03|com|00| --from 40 --to 66'
            uci set firewall.@rule[-1].target=REJECT
            uci add firewall rule
            uci set firewall.@rule[-1].name='Allow LAN clients DNS to ISP for *.privateinternetaccess.com'
            uci set firewall.@rule[-1].src=lan
            uci set firewall.@rule[-1].dest=wan
            uci set firewall.@rule[-1].family=ipv4
            uci set firewall.@rule[-1].proto=tcpudp
            uci set firewall.@rule[-1].dest_port=53
            uci set firewall.@rule[-1].extra='--match string --algo bm   --hex-string |15|privateinternetaccess|03|com|00| --from 40 --to 66'
            uci set firewall.@rule[-1].target=ACCEPT
            uci add firewall rule
            uci set firewall.@rule[-1].name='Block LAN to ISP (TCP) except ssh'
            uci set firewall.@rule[-1].src=lan
            uci set firewall.@rule[-1].dest=wan
            uci set firewall.@rule[-1].family=ipv4
            uci set firewall.@rule[-1].proto=tcp
            uci set firewall.@rule[-1].extra='--match multiport ! --dports 22'
            uci set firewall.@rule[-1].target=REJECT
            uci add firewall rule
            uci set firewall.@rule[-1].name='Block LAN to ISP (UDP) except OpenVPN'
            uci set firewall.@rule[-1].src=lan
            uci set firewall.@rule[-1].dest=wan
            uci set firewall.@rule[-1].family=ipv4
            uci set firewall.@rule[-1].proto=udp
            uci set firewall.@rule[-1].extra='--match multiport ! --dports 1194,1198'
            uci set firewall.@rule[-1].target=REJECT
            uci commit firewall
            --- group starta1 ---
            # it seems that `/etc/init.d/openvpn enable` isn't reliable and ...
            #     `/etc/init.d/openvpn start` (run at boot) starts a new process every 5 seconds
            # use cron to check every 60 seconds if OpenVPN is working
            (crontab -l 2>/dev/null; echo '* * * * * /etc/openvpn/restart-if-needed.sh') |crontab -
            --- group complete1 --- # end marker
        '''
        try:
            update_count = router.update_groups(groups_gl_inet)
            if update_count > 0:
                router.exec('reboot')
        except RemoteExecutionError:
            raise CGError("Unable to fully configure router {}. ".format(router.nickname)
                    + "Reboot reboot router and try again.") # FIXME: automate this
        # all groups successfully updated
    except:
        router.close() # it's important to close Paramiko client
        conf.save()
        raise
    else:
        router.close()
        conf.save()


if __name__ == '__main__':
    try:
        main()
    except CGError as err:
        print_msg(0,err)


# FIXME: implement unit tests
# FIXME: implement router testing (#14 in README.md)
# test that your IP is from PIA via: wget -q -O- 'https://www.privateinternetaccess.com/'  ...
#     |grep 'You are protected by PIA'
