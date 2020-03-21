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

from kivy.uix.screenmanager import Screen
from kivymd.uix.tab import MDTabsBase
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.properties import ObjectProperty

class BaseScreen(Screen):
    def guide_begin(self, instance):
        webbrowser.open(url)

class Tab(FloatLayout, MDTabsBase):
    '''Class implementing content for a tab.'''
    pass

def plus_button(self):
    self.parent.parent.parent.parent.parent.parent.parent.parent.manager.current = "guide_intro"  # FIXME
    self.parent.parent.parent.parent.parent.parent.parent.parent.manager.transition.direction = "left"

class FloatButton(AnchorLayout):
    callback = plus_button  # ObjectProperty()
    icon = ObjectProperty()

