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

import os
import sys
from ast import literal_eval

from kivy.lang import Builder
from kivy.core.window import Window
from kivy.config import ConfigParser
from kivy.clock import Clock
from kivy.utils import get_hex_from_color
from kivy.properties import ObjectProperty, StringProperty

from main import __version__
from libs.translation import Translation
from libs.uix.baseclass.startscreen import StartScreen
from libs.uix.lists import Lists

from kivymd.app import MDApp
from kivymd.toast import toast
from kivymd.uix.list import TwoLineAvatarIconListItem, ImageLeftWidget
from kivymd.uix.card import MDCard, MDSeparator
from kivymd.uix.label import MDLabel
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.modalview import ModalView

class bitburrow(MDApp):
    title = 'BitBurrow'
    icon = 'icon.png'
    nav_drawer = ObjectProperty()
    lang = StringProperty('en')

    def __init__(self, **kvargs):
        super(bitburrow, self).__init__(**kvargs)
        Window.bind(on_keyboard=self.events_program)
        Window.soft_input_mode = 'below_target'

        self.list_previous_screens = ['base_screen']
        self.window = Window
        self.config = ConfigParser()
        self.manager = None
        self.window_language = None
        self.exit_interval = False
        self.dict_language = literal_eval(
            open(
                os.path.join(self.directory, 'data', 'locales', 'locales.txt')).read()
        )
        self.translation = Translation(
            self.lang, 'Ttest', os.path.join(self.directory, 'data', 'locales')
        )

    def get_application_config(self):
        return super(bitburrow, self).get_application_config(
                        '{}/%(appname)s.ini'.format(self.directory))

    def build_config(self, config):
        config.adddefaultsection('General')
        config.setdefault('General', 'language', 'en')

    def set_value_from_config(self):
        self.config.read(os.path.join(self.directory, 'bitburrow.ini'))
        self.lang = self.config.get('General', 'language')

    def build(self):
        self.set_value_from_config()
        self.load_all_kv_files(os.path.join(self.directory, 'libs', 'uix', 'kv'))
        self.screen = StartScreen()
        self.manager = self.screen.ids.manager
        self.nav_drawer = self.screen.ids.nav_drawer

        self.new_router("Jason's home router", "GL-AR300M16-ext", "icons/gl-inet-gl-ar300m.jpg")
        self.new_router("SamD", "GL-AR750", "icons/gl-ar750.jpg")
        self.new_router("office, room 311", "GL-AR150-676", "icons/gl-ar150.jpg")
        self.new_router("Trance", "GL-AR750", "icons/gl-ar750.jpg")
        self.new_router("Taco Bell #10088", "GL-AR150-676", "icons/gl-ar150.jpg")
        self.new_router("unnamed", "GL-AR300M16-ext", "icons/gl-inet-gl-ar300m.jpg")
        self.new_router("backup - kept in travel packpack", "GL-AR300M16-ext", "icons/gl-inet-gl-ar300m.jpg")

        self.new_provider("PIA", "Private Internet Access", "")
        self.new_provider("Mullvad", "Mullvad", "")

        return self.screen

    def new_router(self, name, message, image_name):
        router = TwoLineAvatarIconListItem(text=name, secondary_text=message)
        router.add_widget(ImageLeftWidget(source=image_name))
        self.screen.ids.base_screen.ids.routers_list.add_widget(router)

    def new_provider(self, name, message, image_name):
        #provider = MDCard(orientation="vertical", padding="8dp", size_hint=(.7, None), pos_hint={"center_x": .5, "center_y": 0}, size=("280dp", "180dp"))
        provider = MDCard(orientation="vertical", padding="8dp", size_hint=(None, None), size=("280dp", "180dp"))
        label = MDLabel(text=name, theme_text_color="Secondary", size_hint_y=1)
        provider.add_widget(label)
        provider.add_widget(MDSeparator(height="10dp"))
        provider.add_widget(MDLabel(text=message))
        self.screen.ids.base_screen.ids.accounts_list.add_widget(provider)

    def load_all_kv_files(self, directory_kv_files):
        for kv_file in os.listdir(directory_kv_files):
            kv_file = os.path.join(directory_kv_files, kv_file)
            if os.path.isfile(kv_file) and kv_file.endswith(".kv"):  # ignore temp files, etc.
                with open(kv_file, encoding='utf-8') as kv:
                    Builder.load_string(kv.read())

    def events_program(self, instance, keyboard, keycode, text, modifiers):
        if keyboard in (1001, 27):
            if self.nav_drawer.state == 'open':
                self.nav_drawer.toggle_nav_drawer()
            self.back_screen(event=keyboard)
        elif keyboard in (282, 319):
            pass

        return True

    def back_screen(self, event=None):
        if event in (1001, 27):
            if self.manager.current == 'base_screen':
                self.dialog_exit()
                return
            try:
                self.manager.current = self.list_previous_screens.pop()
                self.manager.transition.direction = "right"
            except:
                self.manager.current = 'base_screen'
            self.screen.ids.action_bar.title = self.title
            self.screen.ids.action_bar.left_action_items = \
                [['menu', lambda x: self.nav_drawer.toggle_nav_drawer()]]

    def show_about(self, *args):
        self.nav_drawer.toggle_nav_drawer()
        self.screen.ids.about.ids.label.text = \
            self.translation._(
                u'[size=20][b]bitburrow[/b][/size]\n\n'
                u'[b]Version:[/b] {version}\n'
                u'[b]License:[/b] MIT\n\n'
                u'[size=20][b]Developer[/b][/size]\n\n'
                u'[ref=SITE_PROJECT]'
                u'[color={link_color}]NAME_AUTHOR[/color][/ref]\n\n'
                u'[b]Source code:[/b] '
                u'[ref=https://github.com/bitinerant/bitburrow]'
                u'[color={link_color}]GitHub[/color][/ref]').format(
                version=__version__,
                link_color=get_hex_from_color(self.theme_cls.primary_color)
            )
        self.manager.current = 'about'
        self.screen.ids.action_bar.left_action_items = \
            [['chevron-left', lambda x: self.back_screen(27)]]

    def show_license(self, *args):
        self.nav_drawer.toggle_nav_drawer()
        self.screen.ids.license.ids.text_license.text = \
            self.translation._('%s') % open(
                os.path.join(self.directory, 'LICENSE'), encoding='utf-8').read()
        self.manager.current = 'license'
        self.screen.ids.action_bar.left_action_items = \
            [['chevron-left', lambda x: self.back_screen(27)]]
        self.screen.ids.action_bar.title = \
            self.translation._('MIT LICENSE')

    def card(self, content, title=None, background_color=None, size=(0.7, 0.5)):
        if not background_color:
            background_color = [1.0, 1.0, 1.0, 1]

        card = MDCard(size_hint=(1, 1), padding=5)  # , background_color=background_color)

        if title:
            box = BoxLayout(orientation="vertical", padding="8dp")
            box.add_widget(
                MDLabel(
                    text=title,
                    theme_text_color="Secondary",
                    font_style="Title",
                    size_hint_y=None,
                    height="36dp",
                )
            )
            box.add_widget(MDSeparator(height="1dp"))
            box.add_widget(content)
            card.add_widget(box)
        else:
            card.add_widget(content)

        dialog = ModalView(size_hint=size, background_color=[0, 0, 0, 0.2])
        dialog.add_widget(card)
        return dialog

    def select_locale(self, *args):
        def select_locale(name_locale):
            for locale in self.dict_language.keys():
                if name_locale == self.dict_language[locale]:
                    self.lang = locale
                    self.config.set('General', 'language', self.lang)
                    self.config.write()

        dict_info_locales = {}
        for locale in self.dict_language.keys():
            dict_info_locales[self.dict_language[locale]] = \
                ['locale', locale == self.lang]

        if not self.window_language:
            self.window_language = self.card(
                Lists(
                    dict_items=dict_info_locales,
                    events_callback=select_locale, flag='one_select_check'
                ),
                size=(.85, .55)
            )
        self.window_language.open()

    def dialog_exit(self):
        def check_interval_press(interval):
            self.exit_interval += interval
            if self.exit_interval > 5:
                self.exit_interval = False
                Clock.unschedule(check_interval_press)

        if self.exit_interval:
            sys.exit(0)
            
        Clock.schedule_interval(check_interval_press, 1)
        toast(self.translation._('Press Back to Exit'))

    def on_lang(self, instance, lang):
        self.translation.switch_lang(lang)
