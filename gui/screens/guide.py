# -*- coding: utf-8 -*-
#

from kivy.lang import Builder

Builder.load_string('''
<GuideIntro>:
    name: 'guide_intro'

    BoxLayout:
        orientation: 'vertical'

        Label:
            color: 0, 0, 0, 1
            font_size: '15sp'
            markup: True
            text:
                app.translation._('Hello\\n[size=30]Prerequisites\\n[size=15]Hello [b]World[/b]')

<GuideVpnProvider>:
    name: 'guide_vpn_provider'

    BoxLayout:
        orientation: 'vertical'

<GuideVpnCredentials>:
    name: 'guide_vpn_credentials'

    BoxLayout:
        orientation: 'vertical'

<GuideVpnLocation>:
    name: 'guide_vpn_location'

    BoxLayout:
        orientation: 'vertical'

<GuideRouterName>:
    name: 'guide_router_name'

    BoxLayout:
        orientation: 'vertical'

<GuideConnectWiFi>:
    name: 'guide_connect_wifi'

    BoxLayout:
        orientation: 'vertical'

<GuideLogin>:
    name: 'guide_login'

    BoxLayout:
        orientation: 'vertical'

<GuideConfigure>:
    name: 'guide_configure'

    BoxLayout:
        orientation: 'vertical'
''')

from kivy.uix.screenmanager import Screen


class GuideIntro(Screen):
    pass

class GuideVpnProvider(Screen):
    pass

class GuideVpnCredentials(Screen):
    pass

class GuideVpnLocation(Screen):
    pass

class GuideRouterName(Screen):
    pass

class GuideConnectWiFi(Screen):
    pass

class GuideLogin(Screen):
    pass

class GuideConfigure(Screen):
    pass

