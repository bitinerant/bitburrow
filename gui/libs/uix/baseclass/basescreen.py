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
    print("plus button")
    self.parent.parent.parent.parent.parent.parent.parent.parent.manager.current = "guide_intro"  # FIXME

class FloatButton(AnchorLayout):
    callback = plus_button  # ObjectProperty()
    icon = ObjectProperty()

