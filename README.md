# Clear Gopher
A safe internet tunnel for the whole home that anyone can set up.

The goal of the Clear Gopher project is to make it really easy for non-technical people to set up a secure VPN for their whole home. We hope to eventually automate most of these steps.

For these instructions, you will need a computer with a few tools which are not installed by default on Windows systems, such as ``telnet``, ``ssh`` client, and ``sha256sum``. Other tools used below are available on Windows by different names, such as ``wget`` and ``unzip``.

#### 1. acquire the hardware
* **VPN router**:  GL.iNet GL-AR300M
	* Similar models, such as the GL-AR300M-Lite, GL-AR300M16, and GL-AR300MD, *may* work but have not been tested.
	* The model with external antennas (GL-AR300M-Ext) should work.
	* This router is available from [Amazon U.S.](https://amzn.com/B01K6MHRJI), [GL-iNet](https://www.gl-inet.com/ar300m/), and elsewhere.
* **USB charger**:  5V/1A
	* Most smartphone chargers should work.
	* Specific models available at Amazon include [HomeSpot](https://amzn.com/B073VLTFQV), [Jahmai](https://amzn.com/B06XGCZ18T), and [Urophylla](https://amzn.com/B072XK4DP5).
	* A micro-USB power cable is included with the GL-AR300M.
* **Ethernet cable**:  10cm or longer
	* Most Ethernet cables should work.
	* Specific models available at Amazon include [2-feet](https://amzn.com/B002RBECAE) and [0.5-feet](https://amzn.com/B00ACR5LNC).


#### 2. plug the VPN router into your existing router
* If you have a VPN router with external antennas, screw on the 2 antennas.
* Plug one end of the Ethernet cable into the port labeled 'WAN' on the VPN router.
* Plug the other end of the Ethernet cable into one of the LAN ports on your existing router ([diagram](https://gl-inet.com/docs/mini/src/connections.png)). If the ports are not labeled and there are 3 or 4 identical-looking ports, use one of those.
* Plug the micro-USB end of the USB cable into the VPN router.
* Plug the other end of the USB cable into the USB charger.
* Plug the USB charger into a wall socket.
* Wait about 1 minute for the VPN router to boot (the red LED should be on or flashing) before trying the next step.


#### 3. reset the router
* If the VPN router has been used or configured before, reset it to its factory settings:
	* Power it on and wait 1 minute for it to boot.
	* Press and hold the reset button on the router for a full 10 seconds.
	* Release the button and wait about 3 minutes.


#### 4. connect via WiFi
* On your device, open WiFi settings and find the VPN router WiFi network. The network name should begin with ``GL-AR300M-``. The factory WiFi password is:  ``goodlife``
* If the WiFi network does not appear, check that the VPN router has at least one LED lit. Also try unplugging the VPN router for 10 seconds and plugging it back in.
* If there are multiple WiFi networks which begin as mentioned above, find the SSID listed on the bottom of the VPN router and connect to that one.


#### 5. set a temporary router password
* Make a random 12-character password (var firstPassword).
* Make a random 12-character password (var routerPassword).
* Make a random 10-character password (var wifiPassword).
* Store these passwords in a safe place.
* Telnet to the router:  ``telnet 192.168.8.1``
* Set the root password on the router to [firstPassword]:  ``passwd``
* Close the connection:  ``exit``
* Note--setting the root password can be done non-interactively by editing /etc/shadow. Generate the encrypted password via:  ``openssl passwd -1 -salt '[8-char salt]' '[firstPassword]``'
* Note--it is also possible to set the router password via http, but this is programmatically more complex, plus on older GL-iNet firmware, this changes the WiFi password as well.


#### 6. connect via ssh
* Use [firstPassword] to connect to the VPN router via ssh, e.g. :  ``ssh root@192.168.8.1``
* Unless noted otherwise, the rest of the commands in this document are to be done on the VPN router over ssh.


#### 7. set passwords, language, timezone
* Update the root password on the router to [routerPassword] (see step 5).
* Update the web UI password on the router via:  ``echo -n [routerPassword] |sha256sum`` (on a system with sha256sum) and ``uci set glconfig.general.password='[above hash]``'
* Update the WiFi password (does not take effect until router is rebooted):  ``uci set wireless.@wifi-iface[0].key='[wifiPassword]``'
* Create and verify the OpenVPN directory:  ``mkdir -p /etc/openvpn && cd /etc/openvpn``
* Choose English as the language:  ``uci set glconfig.general.language=en && uci set luci.main.lang=en``
* Choose UTC as the timezone:  ``uci set system.@system[0].zonename=UTC && uci set system.@system[0].timezone=GMT0 && echo GMT0 >/etc/TZ``
* Save changes:  ``uci commit``


#### 8. purchase VPN service
* Go to [Private Internet Access](https://www.privateinternetaccess.com/) (PIA) and sign up for service.
	* From the home page, click Get Started or Join Now.
	* Choose a plan and payment method.
	* Enter your email address and payment details.
	* Complete the payment.
* Check your email for the username and password assigned to you by PIA and store these (var vpnUsername and var vpnPassword).


#### 9. choose a server location
* Go to <https://www.privateinternetaccess.com/pages/network/> and find the best server in the country of the user's choice.
* Store the chosen location (var serverHostname), e.g.:  ``us-east.privateinternetaccess.com``


#### 10. copy VPN provider files and credentials to the router
* Do this on another computer (note that, except for credentials.txt, these files are not user-specific):
```
mkdir for_router && cd for_router
wget https://www.privateinternetaccess.com/openvpn/openvpn.zip
unzip openvpn.zip && rm openvpn.zip
rm *.ovpn
wget https://www.privateinternetaccess.com/openvpn/ca.crt
#in .zip:  https://www.privateinternetaccess.com/openvpn/ca.rsa.2048.crt
wget https://www.privateinternetaccess.com/openvpn/ca.rsa.4096.crt
echo [vpnUsername] >credentials.txt
echo [vpnPassword] >>credentials.txt
```

* Create a new file in this directory named ``PIA-client.conf`` containing:
```
client
dev tun
proto udp
remote [serverHostname] 1198
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
auth-nocache
pull-filter ignore "auth-token"
crl-verify crl.rsa.2048.pem
ca ca.rsa.2048.crt
reneg-sec 0
comp-lzo yes
verb 3
mute-replay-warnings
log /tmp/openvpn.log
daemon
```
* Note--``auth-nocache`` appears to greatly reduce ``AUTH_FAILED`` errors (64% -> 6% in a quick test), and adding to this ``pull-filter ignore "auth-token"`` (for OpenVPN 2.4; [source](https://www.privateinternetaccess.com/forum/discussion/24089/inactivity-timeout-ping-restart#latest)) seems eliminate the errors.
* Create a new file in this directory named ``sysinfo`` containing:
```
#!/bin/sh
echo '### date'
date --utc '+%Y-%m-%d %H:%M:%S'
echo '### uptime'
uptime
echo '### cat /etc/banner'
cat /etc/banner |grep -v -e '^ ---------------' -e '^  \* ' -e '^ |' -e '^  __'
echo '### cat /etc/glversion'
cat /etc/glversion
echo '### cat /etc/openwrt_release'
cat /etc/openwrt_release
echo '### uname -a'
uname -a
echo '### cat /proc/cpuinfo'
cat /proc/cpuinfo
echo '### ip address show'
ip address show
echo '### ip route show'
ip route show
echo '### ls -l /etc/openvpn'
ls -l /etc/openvpn
echo '### cat /etc/openvpn/*.conf'
cat /etc/openvpn/*.conf
echo '### cat /etc/config/openvpn'
cat /etc/config/openvpn |grep -v -e '^#' -e '^\W#' -e '^$'
echo '### cat /etc/firewall.user'
cat /etc/firewall.user
echo '### uci show'
uci show |grep -v '^wireless..wifi-iface....key='
echo '### traceroute -n -m 4 141.1.1.1'
traceroute -n -m 4 141.1.1.1
echo '### cat /tmp/openvpn.log'
cat /tmp/openvpn.log
echo '### iptables-save'
iptables-save
echo '### the end'
```
* Make sure all files have Linux-style line endings.
* Copy all the files to the router:
```
scp * root@192.168.8.1:/etc/openvpn
```
* Delete the ``for_router`` folder.

#### 11. DNS
* Set specific DNS servers so that the ISP's servers are not used:
```
uci add_list dhcp.@dnsmasq[-1].server='9.9.9.9'
uci add_list dhcp.@dnsmasq[-1].server='149.112.112.112'
uci add_list dhcp.@dnsmasq[-1].noresolv=1
uci set network.wan.peerdns=0
uci set network.wan.custom_dns=1
uci set network.wan.dns='9.9.9.9 149.112.112.112'
uci set glconfig.general.force_dns=yes
uci commit
```

#### 12. IPv6
* Note--IPv6 should be disabled until we can properly address the security implications ([more info](https://helpdesk.privateinternetaccess.com/hc/en-us/articles/232324908-Why-Do-You-Block-IPv6-)).
* Edit /etc/sysctl.conf and modify these values (add them if they aren't listed):
```
net.ipv6.conf.all.disable_ipv6=1
net.ipv6.conf.default.disable_ipv6=1
net.ipv6.conf.lo.disable_ipv6=1
```
* Prevent  'dhcp6 solicit' to the ISP:
```
uci add firewall rule
uci set firewall.@rule[-1].name='Block all IPv6 to ISP'
uci set firewall.@rule[-1].dest=wan
uci set firewall.@rule[-1].family=ipv6
uci set firewall.@rule[-1].target=REJECT
uci commit firewall
```

#### 13. configure OpenVPN
* Set uci values:
```
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
```
* Install OpenVPN and iptables tools (OpenVPN is pre-installed on GL-iNet routers; if opkg fails, reboot and retry):
```
opkg update
opkg install openvpn-openssl # or, for OpenWrt older than Chaos Calmer:  opkg install openvpn
opkg install kmod-ipt-filter iptables-mod-filter # for iptables --match string
```
* Prevent leaking data to the ISP:
```
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
```
* Enble automatic start-up and restart:
```
chmod 660 /etc/openvpn/*
chmod 770 /etc/openvpn/sysinfo
touch /etc/config/openvpn
uci set openvpn.vpnas=openvpn
uci set openvpn.vpnas.enabled=1
uci commit openvpn
/etc/init.d/openvpn enable
printf '\n/etc/init.d/openvpn start\n' >>/etc/firewall.user # 'enable' isn't reliable
reboot
```

#### 14. test
* Wait for the router to reboot and reconnect WiFi using [wifiPassword].
* From the client computer, test a few websites and download a large file (30 seconds or more).
* Test that your IP is from PIA (e.g. banner at top of PIA home page should say, "You are protected by PIA")
* Test that DNS is not leaking (none of the DNS addresses displayed should be in same country as the router) at <https://ipleak.net/> (an additional DNS leak test is at <https://dnsleaktest.com/>).
* Test that IPv6 is blocked:  <http://ipv6-test.com/>.
* Test that  DNS and traffic are completely blocked when OpenVPN dies or the connection is lost; this will also test that OpenVPN automatically restarts:
	* Preparation--on router:  ``opkg update && opkg install tcpdump``
	* Terminal window 1--on router:  ``tcpdump -n -i eth0 '(not port 1198) and (tcp or udp)'``
	* Terminal window 2--on router:  ``for i in `seq 10000`; do ping -c 1 -q a$i.example.com; done |grep ^PING``
	* Terminal window 3--on client computer:  ``for i in `seq 10000`; do ping -c 1 -q b$i.example.com; done |grep ^PING``
	* Terminal window 4--on router:  ``ps |grep '[o]penvpn'; sleep 1; killall openvpn; sleep 1; ps |grep '[o]penvpn'; sleep 10; ps |grep '[o]penvpn'``
	* After running the above command, watch the tcpdump window. After a couple of seconds, you should see some queries for privateinternetaccess.com but **not any other queries**. If you don't see any tcpdump activity, wait a few mintues for the DNS cache to time out. The above command should list exactly 2 lines--the old and the new OpenVPN instances.

#### notes and links
* If the VPN connects but only very simple web pages load ([example](http://www.neverhttps.com/)), add this line to the OpenVPN .conf file and reboot again:  ``mssfix 1300``
* To allow ssh via WAN port on OpenWrt:  <http://192.168.8.1/cgi-bin/luci/> > Network > Firewall > Traffic Rules > Open ports on router > open port TCP 22 > Save and apply
* For passwordless ssh:  ``vi /etc/dropbear/authorized_keys`` and add your id_rsa.pub contents; ``ssh-keyscan 192.168.8.1`` and add to known_hosts
* [PIA encryption/auth settings](https://helpdesk.privateinternetaccess.com/hc/en-us/articles/225274288-Which-encryption-auth-settings-should-I-use-for-ports-on-your-gateways-)
* [PIA OpenVPN config files](https://helpdesk.privateinternetaccess.com/hc/en-us/articles/218984968-What-is-the-difference-between-the-OpenVPN-config-files-on-your-website-)
* PIA [Setting up a Router running LEDE Firmware](https://helpdesk.privateinternetaccess.com/hc/en-us/articles/115005760646-Setting-up-a-Router-running-LEDE-Firmware) (contains lots of errors)
* [Setting an OpenWrt Based Router as OpenVPN Client](https://github.com/StreisandEffect/streisand/wiki/Setting-an-OpenWrt-Based-Router-as-OpenVPN-Client)
* It is probably possible to [upgrade the firmware via CLI](https://forum.lede-project.org/t/a-rough-writeup-for-the-commandline-firmware-upgrade-wikipage/464).

