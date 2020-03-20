# -*- coding: utf-8 -*-
#
# This file created with KivyCreatorProject
# <https://github.com/HeaTTheatR/KivyCreatorProgect
#
# Copyright (c) 2020 Ivanov Yuri and KivyMD
#
# For suggestions and questions:
# <kivydevelopment@gmail.com>
#
# LICENSE: MIT

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

<StartScreen>

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
            id: base_screen

        GuideIntro:
            id: guide_intro

        GuideVpnProvider:
            id: guide_vpn_provider

        GuideVpnCredentials:
            id: guide_vpn_credentials

        GuideVpnLocation:
            id: guide_vpn_location

        GuideRouterName:
            id: guide_router_name

        GuideConnectWiFi:
            id: guide_connect_wifi

        GuideLogin:
            id: guide_login

        GuideConfigure:
            id: guide_configure

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
