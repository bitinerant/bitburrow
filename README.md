# Clear Gopher
A safe internet tunnel for the whole home that anyone can set up.

The goal of the Clear Gopher project is to make it really easy for non-technical people to set up a secure VPN for their whole home. We hope to eventually automate most of these steps.

For these instructions, you will need a computer with Ubuntu Linux installed.

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


#### 2. purchase VPN service
* Go to [Private Internet Access](https://www.privateinternetaccess.com/) (PIA) and sign up for service.
	* From the home page, click Get Started or Join Now.
	* Choose a plan and payment method.
	* Enter your email address and payment details.
	* Complete the payment.
* Check your email for the username and password assigned to you by PIA and store these.


#### 3. choose a server location
* Go to <https://www.privateinternetaccess.com/pages/network/> and find the best server in the country of the user's choice.
* Store the chosen location, e.g.:  ``us-east.privateinternetaccess.com``


#### 4. plug the VPN router into your existing router
* If you have a VPN router with external antennas, screw on the 2 antennas.
* Plug one end of the Ethernet cable into the port labeled 'WAN' on the VPN router.
* Plug the other end of the Ethernet cable into one of the LAN ports on your existing router. If the ports are not labeled and there are 3 or 4 identical-looking ports, use one of those.
* Plug the micro-USB end of the USB cable into the VPN router.
* Plug the other end of the USB cable into the USB charger.
* Plug the USB charger into a wall socket.
* Wait about 1 minute for the VPN router to boot (the red LED should be on or flashing) before trying the next step.


#### 5. reset the router
* If the VPN router has been used or configured before, reset it to its factory settings:
	* Power it on and wait 1 minute for it to boot.
	* Press and hold the reset button on the router for a full 10 seconds.
	* Release the button and wait about 3 minutes.


#### 6. configure the router

* Use an Ubuntu 18.04 host.

* Clone this project
    
    ```bash
    $ git clone https://github.com/bitinerant/cleargopher.git
    $ cd cleargopher
    ```

* Install required host dependencies.

    ```bash
    $ sudo apt install python3-venv python3-dbus python3-networkmanager
    ```

* Create a Python [virtual environment](https://docs.python.org/3/library/venv.html) and also use system packages
  so that `python-dbus` can be properly linked in.

    ```bash
    $ python3 -m venv --system-site-packages venv
    ```

* Activate the virtual environment and install the required dependencies from PyPI.

    ```bash
    $ source venv/bin/activate
    (venv) $ pip install --upgrade pip
    (venv) $ pip install -r requirements.txt
    ```

* Run the main script within the activated virtual environment.

    ```bash
    (venv) $ ./main.py -v configure
    ```

* You will be prompted to enter the VPN username, password, and location from steps 2 and 3, above.

#### 7. test
* Wait for the router to reboot.
* Reconnect the WiFi to the VPN router. The password should be saved in Network Manager. (It is also in ``~/.cleargopher/cleapher.conf``.)
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

