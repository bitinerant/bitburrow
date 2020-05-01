# -*- coding: utf-8 -*-
#

# Entry point to the application. Runs the main program.py program code.
# In case of error, displays a window with its text.

import os
import sys
import traceback

directory = os.path.split(os.path.abspath(sys.argv[0]))[0]
sys.path.insert(0, os.path.join(directory, 'gui'))

try:
    import webbrowser
    import kivy
    kivy.require('1.9.2')
    from kivy.utils import platform
    from kivy.config import Config
    Config.set('kivy', 'keyboard_mode', 'system')
    Config.set('kivy', 'log_enable', 0)
    if platform != 'android' and platform != 'ios': # for testing, approximate an Android phone
        Config.set('graphics', 'width', '413')  # from https://stackoverflow.com/a/30332167
        Config.set('graphics', 'height', '733')
    from kivymd.theming import ThemeManager
except Exception:
    traceback.print_exc(file=open(os.path.join(directory, 'error.log'), 'w'))
    print(traceback.print_exc())
    sys.exit(1)

__version__ = '0.3'

def main():
    if sys.version_info < (3, 6):
        sys.exit("This app requires Python version 3.6 or higher.\n")
    def create_error_monitor():
        class _App(App):
            theme_cls = ThemeManager()
            theme_cls.primary_palette = 'BlueGray'

            def build(self):
                box = BoxLayout()
                return box
        app = _App()
        app.run()

    app = None

    try:
        from bitburrow import bitburrow
        app = bitburrow()
        app.run()
    except Exception:
        from kivy.app import App
        from kivy.uix.boxlayout import BoxLayout

        text_error = traceback.format_exc()
        traceback.print_exc(file=open(os.path.join(directory, 'error.log'), 'w'))
        if app:
            try:
                app.stop()
            except AttributeError:
                app = None
        if app:
            try:
                app.screen.clear_widgets()
            except AttributeError:
            	create_error_monitor()
        else:
            create_error_monitor()

if __name__ in ('__main__', '__android__'):
    main()
