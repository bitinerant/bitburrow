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

import webbrowser

from kivy.uix.screenmanager import Screen


class About(Screen):
    def open_url(self, instance, url):
        webbrowser.open(url)
