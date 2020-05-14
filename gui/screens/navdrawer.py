# -*- coding: utf-8 -*-
#

from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder

Builder.load_string('''
#:import os os
#:import SingleIconItem libs.lists.SingleIconItem

<LabelSection@Label>:
    markup: True
    bold: True
    font_size: '16sp'
    color: 0, 0, 0, 1
    size_hint_y: None
    height: dp(45)
<NavDrawer>:
    orientation: 'vertical'
    BoxLayout:
        id: box_avatar
        orientation: 'vertical'
        padding: dp(10)
        spacing: dp(10)
        size_hint_y: .3
        canvas:
            Color:
                rgba: app.theme_cls.primary_color
            Rectangle:
                pos: self.pos
                size: self.size
        Image:
            id: navigation_image
            size_hint: None, None
            size: dp((box_avatar.height * 30) // 100), dp((box_avatar.height * 30) // 100)
            source: 'gui/data/images/icon.png'
        Widget:
        Label:
            id: user_name
            size_hint: None, None
            height: dp(20)
            width: self.texture_size[0]
            halign: 'left'
            text: '[b]%s[/b]\\n[size=12]0.3[/size]\\n' % app.title
            markup: True
            font_size: '14sp'
    ScrollView:
        id: scroll
        size_hint_y: .7
        GridLayout:
            cols: 1
            size_hint_y: None
            height: self.minimum_height
            spacing: dp(10)
            LabelSection:
                text:  app.translation._('Меню:')
                events_callback: lambda x: x
            SingleIconItem:
                icon: 'web'
                text: app.translation._('Язык')
                events_callback: app.select_locale
            SingleIconItem:
                icon: 'language-python'
                text: app.translation._('Лицензия')
                events_callback: app.show_license
            SingleIconItem:
                icon: 'alert-decagram'
                text: app.translation._('Force app crash')
                events_callback: lambda x: app.this_key_does_not_exist
            SingleIconItem:
                icon: 'information'
                text: 'About'
                events_callback: app.show_about
''')

class NavDrawer(BoxLayout):
    pass
