# -*- coding: utf-8 -*-
#

from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton, MDRectangleFlatButton
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
import textwrap
import webbrowser


Builder.load_string('''
<BackNextBar>:
    orientation: 'vertical'
    size_hint_y: None
    height: self.ids.button_next.height + 40  # padding 20 above + 20 below
    AnchorLayout:
        anchor_x: 'left'
        anchor_y: 'bottom'
        padding: dp(20)
        MDRectangleFlatButton:
            id: button_back
            markup: True
            on_release: root.callback('back')
    AnchorLayout:
        anchor_x: 'right'
        anchor_y: 'bottom'
        padding: dp(20)
        MDRaisedButton:
            id: button_next
            markup: True
            on_release: root.callback('next')

<GuideTextLabel>:
    markup: True
    size_hint_y: None
    height: self.texture_size[1]
    text_size: self.width, None
    padding: 20, 4
    color: 0, 0, 0, 1
    font_size: '16sp'

<GuideScreenBase>:
    StackLayout:
        ScrollView:
            id: view_scroll
            do_scroll_x: False
            do_scroll_y: True
            size_hint: 1, None
            width: self.parent.width
            height: self.parent.height - root.ids.back_next_bar.height
            StackLayout:
                id: scrollarea
                size_hint_y: None
                Label:
                    id: padtop
                    size_hint_y: None
                    height: 22
                StackLayout:
                    id: content_stack
                    size_hint_y: None
                    #height: 0
    BackNextBar:
        id: back_next_bar

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


class GuideTextLabel(Label):
    pass


class BackNextBar(FloatLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.callback = self.button_press
        Clock.schedule_once(self.build)

    def build(self, *args):
        #self.height = self.ids.button_next.height
        self.ids.button_next.text = 'NEXT  [b]>[/b]'
        if self.parent.name == 'guide_intro':
            self.ids.button_back.text = 'CANCEL'
        else:
            self.ids.button_back.text = '[b]<[/b]  BACK'

    def button_press(self, btn_name):
        app = MDApp.get_running_app()
        current_index = app.manager.screen_names.index(app.manager.current)
        if btn_name == 'next':
            app.manager.current = app.manager.screen_names[current_index + 1]
            app.manager.transition.direction = "left"
        else:
            app.manager.current = app.manager.screen_names[current_index - 1]
            app.manager.transition.direction = "right"


class GuideScreenBase(Screen):

    def build(self, *args):
        self.app = MDApp.get_running_app()
        scroll_widget = self.ids.scrollarea
        scroll_widget.bind(minimum_height=scroll_widget.setter('height'))

    def open_url(self, instance, url):
        print("opening {} in instance {}".format(url, instance))
        webbrowser.open(url)

    def link_mu(self, text, url):
        return "[ref={}][color=0000ff]{}[/color][/ref]".format(url, text)


class GuideIntro(GuideScreenBase):

    def __init__(self, **kvargs):
        self.name = 'guide_intro'
        super().__init__(**kvargs)
        Clock.schedule_once(self.build)

    def build(self, *args):
        super().build(*args)
        content_stack = self.ids.content_stack
        heading = GuideTextLabel(
            text = self.app.translation._('[size=30][b]Introduction[/b][/size]'),
        )
        content_stack.add_widget(heading)
        main_text = GuideTextLabel(
            text = self.app.translation._('\
                Welcome to the BitBurrow app. If you have not already done so, visit\
                '+self.link_mu("bitburrow.com", "https://bitburrow.com")+'\
                for information about BitBurrow, requirements, and how this app fits in.\
                A list of suported routers is available '+self.link_mu("here", "router_list")+'.\
                ', normalize_spaces=True),
        )
        main_text.bind(on_ref_press=self.open_url)
        content_stack.add_widget(main_text)
        content_stack.bind(minimum_height=content_stack.setter('height'))

    def open_url(self, instance, url):
        if url == "router_list":
            dialog = MDDialog(
                size_hint=(0.8, 0.7),
                title='Supported routers',
                text="one two three four five six seven eight nine zero "*60,
                text_button_ok='Ok',
            )
            dialog.open()
        else:
            super().open_url(instance, url)


class GuideVpnProvider(GuideScreenBase):

    def __init__(self, **kvargs):
        self.name = 'guide_vpn_provider'
        super().__init__(**kvargs)
        Clock.schedule_once(self.build)

    def build(self, *args):
        super().build(*args)
        content_stack = self.ids.content_stack
        heading = GuideTextLabel(
            text = self.app.translation._('[size=30][b]Step 1[/b][/size]'),
        )
        content_stack.add_widget(heading)
        main_text = GuideTextLabel(
            text = self.app.translation._('\
                Choose a VPN provider and sign up for a service plan.\
                ', normalize_spaces=True),
        )
        main_text.bind(on_ref_press=self.open_url)
        content_stack.add_widget(main_text)
        content_stack.bind(minimum_height=content_stack.setter('height'))


class GuideVpnCredentials(GuideScreenBase):

    def __init__(self, **kvargs):
        self.name = 'guide_vpn_credentials'
        super().__init__(**kvargs)
        Clock.schedule_once(self.build)

    def build(self, *args):
        super().build(*args)
        content_stack = self.ids.content_stack
        heading = GuideTextLabel(
            text = self.app.translation._('[size=30][b]Step 2[/b][/size]'),
        )
        content_stack.add_widget(heading)
        main_text = GuideTextLabel(
            text = self.app.translation._('\
                Enter your VPN credentials.\
                ', normalize_spaces=True),
        )
        main_text.bind(on_ref_press=self.open_url)
        content_stack.add_widget(main_text)
        for i in range(10):
            btn = Button(text=str(i), size_hint_y=None, height=30+i*7)
            content_stack.add_widget(btn)
        content_stack.bind(minimum_height=content_stack.setter('height'))


class GuideVpnLocation(GuideScreenBase):

    def __init__(self, **kvargs):
        self.name = 'guide_vpn_location'
        super().__init__(**kvargs)
        Clock.schedule_once(self.build)

    def build(self, *args):
        super().build(*args)
        content_stack = self.ids.content_stack
        heading = GuideTextLabel(
            text = self.app.translation._('[size=30][b]Step 3[/b][/size]'),
        )
        content_stack.add_widget(heading)
        main_text = GuideTextLabel(
            text = self.app.translation._('\
                Select where the VPN will terminate.\
                ', normalize_spaces=True),
        )
        main_text.bind(on_ref_press=self.open_url)
        content_stack.add_widget(main_text)
        content_stack.bind(minimum_height=content_stack.setter('height'))


class GuideRouterName(Screen):
    pass


class GuideConnectWiFi(Screen):
    #ideas: https://cdn.yankodesign.com/images/design_news/2019/06/what-if-you-could-trick-big-corporations-from-stealing-your-data/winston13.jpg
    #above link from: https://www.yankodesign.com/2019/06/14/this-design-encrypts-your-network-to-prevent-tech-companies-hackers-governments-from-spying-on-you/
    pass


class GuideLogin(Screen):
    pass


class GuideConfigure(Screen):
    pass
