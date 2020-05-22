# -*- coding: utf-8 -*-
#

# Entry point to the application. Runs the main program.py program code.
# In case of error, displays a window with its text.

import os
import sys
import webbrowser  # FIXME: test without
import kivy.config
import kivy.utils
kivy.config.Config.set('kivy', 'keyboard_mode', 'system')
kivy.config.Config.set('kivy', 'log_enable', 0)
if kivy.utils.platform != 'android' and kivy.utils.platform != 'ios': # approximate an Android phone
    kivy.config.Config.set('graphics', 'width', '413')  # from https://stackoverflow.com/a/30332167
    kivy.config.Config.set('graphics', 'height', '733')  # must happen before: import kivy
import kivy
import textwrap
import logging


__version__ = '0.3'


def main():
    app = None
    global kivy
    try:
        min_ver = (3, 6)
        if sys.version_info < min_ver:
            assert False, f"This app requires Python version {min_ver[0]}.{min_ver[1]} or higher."
        kivy.require('1.11.1')
        directory = os.path.split(os.path.abspath(sys.argv[0]))[0]
        sys.path.insert(0, os.path.join(directory, 'gui'))
        import program
        app = program.Program()
        app.run()
    except Exception as e:
        # Could try combinations of these, but more testing is needed to know if
        # any would actually help the error to be displayed:
        #     import kivy.base
        #     kivy.base.stopTouchApp()
        #     app.screen.clear_widgets()
        #     app.close()
        #     app.root_window.close()
        import traceback
        from kivy.lang import Builder
        trace = traceback.format_exc()
        print(trace)
        error_text = f"We have a problem: [b]{str(e)}[/b]\n\n{trace}"
        layout = Builder.load_string(textwrap.dedent('''
            <BackgroundColor@Widget>:
                background_color: 0, 0, 0, 0
                canvas.before:
                    Color:
                        rgba: root.background_color
                    Rectangle:
                        size: self.size
                        pos: self.pos
            <BackgroundLabel@Label+BackgroundColor>:
            StackLayout:
                ScrollView:
                    do_scroll_x: False
                    do_scroll_y: True
                    size_hint: 1, None
                    width: self.parent.width
                    height: self.parent.height
                    StackLayout:
                        size_hint_y: None
                        height: root.ids.text_area.height
                        BackgroundLabel:
                            id: text_area
                            text_size: root.width, None
                            size: self.texture_size
                            markup: True
                            color: 1, 1, 1, 1
                            background_color: 0, 0, 0, 1
        '''))
        layout.ids.text_area.text = error_text
        kivy.base.runTouchApp(layout)

if __name__ in ('__main__', '__android__'):
    main()
