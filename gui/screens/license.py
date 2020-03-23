# -*- coding: utf-8 -*-
#

from kivy.uix.screenmanager import Screen
from kivy.lang import Builder

Builder.load_string('''
# #:import License screens.license.License

<License>:
    name: 'license'

    BoxLayout:
        orientation: 'vertical'
        padding: dp(10), dp(10)
        spacing: dp(10)

        Label:
            size_hint: None, None
            height: dp(20)
            width: self.texture_size[0]
            halign: 'left'
            color: app.theme_cls.primary_color
            font_size: '18sp'
            text: app.translation._('GPL v3.0 LICENSE')

        MDSeparator:

        Image:
            source: 'gui/data/images/open-source-logo.png'

        ScrollView:

            Label:
                id: text_license
                font_size: '13sp'
                text_size: self.width, None
                size_hint_y: None
                markup: True
                height: self.texture_size[1]
''')

class License(Screen):
    pass
