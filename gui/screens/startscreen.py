# -*- coding: utf-8 -*-
#

from kivymd.uix.navigationdrawer import NavigationLayout
from kivy.lang import Builder

Builder.load_string('''
#:import NavDrawer screens.navdrawer.NavDrawer
#:import License screens.license.License
#:import BaseScreen screens.basescreen.BaseScreen
#:import Guide0 screens.guide.Guide0
#:import Guide1 screens.guide.Guide1
#:import Guide2 screens.guide.Guide2
#:import Guide3 screens.guide.Guide3
#:import Guide4 screens.guide.Guide4
#:import Guide5 screens.guide.Guide5
#:import Guide6 screens.guide.Guide6
#:import Guide7 screens.guide.Guide7
#:import About screens.about.About

<StartScreen>:
    MDToolbar:
        id: action_bar
        background_color: app.theme_cls.primary_color
        title: app.title
        # for full icon list, run: python images/preview_icons.py
        left_action_items: [ ['menu', lambda x: nav_drawer.toggle_nav_drawer()], ]
        right_action_items: [ ['linux', lambda x: print('linux')], ['help', lambda x: print('help')], ]
        elevation: 10
        md_bg_color: app.theme_cls.primary_color
        pos_hint: {"top": 1}
    ScreenManager:
        id: manager
        size_hint_y: None
        height: root.height - action_bar.height
        BaseScreen:
            id: base_screen
        Guide0:
            id: guide0
        Guide1:
            id: guide1
        Guide2:
            id: guide2
        Guide3:
            id: guide3
        Guide4:
            id: guide4
        Guide5:
            id: guide5
        Guide6:
            id: guide6
        Guide7:
            id: guide7
        License:
            id: license
        About:
            id: about
    MDNavigationDrawer:
        id: nav_drawer
        NavDrawer:
''')

class StartScreen(NavigationLayout):
    pass
