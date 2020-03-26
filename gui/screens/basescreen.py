# -*- coding: utf-8 -*-
#

from kivy.lang import Builder

Builder.load_string('''
<FloatButton>
    anchor_x: 'right'
    anchor_y: 'bottom'
    size_hint_y: None
    height: dp(56)
    padding: dp(10)
    MDFloatingActionButton:
        size_hint: None, None
        size:dp(56), dp(56)
        icon: 'plus'  # maybe set per instance: https://stackoverflow.com/a/30220800
        opposite_colors: True
        elevation: 8
        on_release: root.callback()

<BaseScreen>:
    name: 'base_screen'

    FloatLayout:
        orientation: 'vertical'

        MDTabs:
            id: base_screen_tabs
            on_tab_switch: self.on_tab_switch(*args)

            Tab:
                text: "ROUTERS"
                FloatLayout:
                    ScrollView:
                        MDList:
                            id: routers_list
                    FloatButton:
            Tab:
                text: "VPN ACCOUNTS"
                ScrollView:
                    MDList:
                        id: accounts_list
''')

from kivymd.app import MDApp
from kivy.uix.screenmanager import Screen
from kivymd.uix.tab import MDTabsBase
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.properties import ObjectProperty
from kivymd.uix.list import TwoLineAvatarIconListItem, ImageLeftWidget
from kivymd.uix.card import MDCard, MDSeparator
from kivymd.uix.label import MDLabel
from os.path import join
import random

class BaseScreen(Screen):

    def build(self):
        self.app = MDApp.get_running_app()
        for i in range(12):
            m = random.choice(self.app.router_models[1:])
            self.new_router(
                " or ".join(m.display_names),
                #m.mfg_page if exists(m.mfg_page) else "N/A",
                m.mfg_page if hasattr(m, 'mfg_page') else "N/A",
                join("models", m.id + ".jpg"),
            )
        self.new_provider("PIA", "Private Internet Access", "")
        self.new_provider("Mullvad", "Mullvad", "")

    def new_router(self, name, message, image_name):
        router = TwoLineAvatarIconListItem(text=name, secondary_text=message)
        router.add_widget(ImageLeftWidget(source=image_name))
        self.app.screen.ids.base_screen.ids.routers_list.add_widget(router)

    def new_provider(self, name, message, image_name):
        #provider = MDCard(orientation="vertical", padding="8dp", size_hint=(.7, None), pos_hint={"center_x": .5, "center_y": 0}, size=("280dp", "180dp"))
        provider = MDCard(orientation="vertical", padding="8dp", size_hint=(None, None), size=("280dp", "180dp"))
        label = MDLabel(text=name, theme_text_color="Secondary", size_hint_y=1)
        provider.add_widget(label)
        provider.add_widget(MDSeparator(height="10dp"))
        provider.add_widget(MDLabel(text=message))
        self.app.screen.ids.base_screen.ids.accounts_list.add_widget(provider)

    def guide_begin(self, instance):
        webbrowser.open(url)


class Tab(FloatLayout, MDTabsBase):
    pass

class FloatButton(AnchorLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.callback = self.plus_button
        icon = ObjectProperty()

    def plus_button(self):
        app = MDApp.get_running_app()
        app.manager.current = "guide_intro"
        app.manager.transition.direction = "left"

