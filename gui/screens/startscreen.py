# -*- coding: utf-8 -*-
#

from kivymd.uix.navigationdrawer import NavigationLayout
from kivy.lang import Builder

Builder.load_string('''
#:import NavDrawer screens.navdrawer.NavDrawer
#:import License screens.license.License
#:import BaseScreen screens.basescreen.BaseScreen
#:import GuideIntro screens.guide.GuideIntro
#:import GuideVpnProvider screens.guide.GuideVpnProvider
#:import GuideVpnCredentials screens.guide.GuideVpnCredentials
#:import GuideVpnLocation screens.guide.GuideVpnLocation
#:import GuideRouterName screens.guide.GuideRouterName
#:import GuideConnectWiFi screens.guide.GuideConnectWiFi
#:import GuideLogin screens.guide.GuideLogin
#:import GuideConfigure screens.guide.GuideConfigure
#:import About screens.about.About

<StartScreen>:
    MDToolbar:
        id: action_bar
        background_color: app.theme_cls.primary_color
        title: app.title
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
        GuideIntro:
        GuideVpnProvider:
        GuideVpnCredentials:
        GuideVpnLocation:
        GuideRouterName:
        GuideConnectWiFi:
        GuideLogin:
        GuideConfigure:
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
