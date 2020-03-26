# -*- coding: utf-8 -*-
#

from kivy.lang import Builder
from kivymd.uix.dialog import MDDialog

Builder.load_string('''
<GuideIntro>:
    name: 'guide_intro'

    BoxLayout:
        orientation: 'vertical'

        ScrollView:
            do_scroll_x: False
            do_scroll_y: True

            Label:
                size_hint_y: None
                height: self.texture_size[1]
                text_size: self.width, None
                size_hint_x: 1
                padding: 40, 40
                color: 0, 0, 0, 1
                font_size: '16sp'
                halign: 'left'
                valign: 'top'
                markup: True
                text:
                    app.translation._('[size=30]Prerequisites\\n[/size]Hello [b]World[/b]\\none two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty twenty-one twenty-two one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty twenty-one twenty-two one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty twenty-one twenty-two one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty twenty-one twenty-two one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty twenty-one twenty-two etc.')

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

    def on_enter(self):
        self.show_supported_routers_dialog()

    def show_supported_routers_dialog(self):
        dialog = MDDialog(
            size_hint=(0.8, 0.7),
            title='Supported routers',
            text="one two three four five six seven eight nine zero "*60,
            text_button_ok='Ok',
            #events_callback=self.callback_for_menu_items
        )
        dialog.open()

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

