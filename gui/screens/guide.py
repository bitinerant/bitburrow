# -*- coding: utf-8 -*-
#

from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton, MDRectangleFlatButton, MDFlatButton
from kivymd.uix.list import MDList, TwoLineAvatarListItem, ImageLeftWidget
from kivymd.uix.textfield import MDTextField
from kivy.uix.stacklayout import StackLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivymd.uix.list import TwoLineAvatarListItem, ImageLeftWidget
from kivymd.toast import toast
from kivy.uix.screenmanager import Screen
import kivy.clock
import providers.endpointmanager
import os.path
import textwrap
import webbrowser


Builder.load_string('''
<RetryButtonBar>:
    orientation: 'vertical'
    size_hint_y: None
    height: self.ids.button_retry.height + 40  # padding 20 above + 20 below
    AnchorLayout:
        anchor_x: 'center'
        anchor_y: 'bottom'
        padding: dp(20)
        MDRaisedButton:
            id: button_retry
            markup: True
            on_release: root.callback('retry')

<SpinnerBar>:
    orientation: 'vertical'
    size_hint_y: None
    height: self.ids.spinner.height + 40  # padding 20 above + 20 below
    AnchorLayout:
        anchor_x: 'center'
        anchor_y: 'bottom'
        padding: dp(20)
        MDSpinner:
            id: spinner
            size_hint: None, None
            size: dp(46), dp(46)
            #pos_hint: {'center_x': .5, 'center_y': .5}


<BackNextBar>:
    orientation: 'vertical'
    size_hint_y: None
    height: self.ids.button_next.height + 40  # padding 20 above + 20 below
    AnchorLayout:
        anchor_x: 'left'
        anchor_y: 'bottom'
        padding: dp(20)
        MDRectangleFlatButton:
            id: button_back
            markup: True
            on_release: root.callback('back')
    AnchorLayout:
        anchor_x: 'right'
        anchor_y: 'bottom'
        padding: dp(20)
        MDRaisedButton:
            id: button_next
            markup: True
            on_release: root.callback('next')

<GuideTextLabel>:
    markup: True
    size_hint_y: None
    height: self.texture_size[1]
    text_size: self.width, None
    padding: 20, 4
    color: 0, 0, 0, 1
    font_size: '16sp'

<SelectOne>:
    on_release: root.set_icon(check)  # tap to right of checkbox
    CheckboxRightWidget:
        id: check
        group: "check"
        on_active: root.callback(*args)

<GuideScreenBase>:
    StackLayout:
        ScrollView:
            id: view_scroll
            do_scroll_x: False
            do_scroll_y: True
            size_hint: 1, None
            width: self.parent.width
            height: self.parent.height - root.ids.back_next_bar.height
            StackLayout:
                id: scroll_area
                size_hint_y: None
                Label:
                    id: padtop
                    size_hint_y: None
                    height: 22
    BackNextBar:
        id: back_next_bar

<GuideRouterName>:
    name: 'guide_router_name'
    BoxLayout:
        orientation: 'vertical'

<GuideConnectWiFi>:
    name: 'guide_connect_wifi'
    BoxLayout:
        orientation: 'vertical'

<GuideLogin>:
    name: 'guide_login'
    BoxLayout:
        orientation: 'vertical'

<GuideConfigure>:
    name: 'guide_configure'
    BoxLayout:
        orientation: 'vertical'
''')


class GuideTextLabel(Label):
    pass


class SelectOne(TwoLineAvatarListItem):
    divider = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.callback = self.on_item_tap
    
    def on_item_tap(self, instance_check, active):
        # note: assumes number of active checks is NEVER more than 1 (current KivyMD behavior)
        self.callback_select(self.index if active else None)

    def set_icon(self, instance_check):
        instance_check.active = True
        check_list = instance_check.get_widgets(instance_check.group)
        for check in check_list:
            if check != instance_check:
                check.active = False
        self.on_item_tap(instance_check, True)


class RetryButtonBar(FloatLayout):
    pass


class SpinnerBar(FloatLayout):
    pass


class BackNextBar(FloatLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.callback = self.on_backnext_button
        kivy.clock.Clock.schedule_once(self.build)

    def build(self, *args):
        self.ids.button_next.text = 'NEXT  [b]>[/b]'
        if self.parent.name == 'guide_intro':
            self.ids.button_back.text = 'CANCEL'
        else:
            self.ids.button_back.text = '[b]<[/b]  BACK'

    def on_backnext_button(self, btn_name):
        app = MDApp.get_running_app()
        if btn_name == 'next':
            if app.manager.current_screen.is_data_valid():
                next_screen = app.manager.next()
                app.screen.ids[next_screen].build()  # build next screen if needed
                app.manager.current = next_screen
                app.manager.transition.direction = "left"
            # else force user to fix fields before moving to next screen
        else:  # 'back'
            app.manager.current = app.manager.previous()
            app.manager.transition.direction = "right"


class GuideScreenBase(Screen):
    form_data = dict()  # user-entered data from all screens
    providers = None  # shared list of VPN provider data

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = MDApp.get_running_app()
        self.scroll_area = None
        self.content_stack = None
        if GuideScreenBase.providers is None:
            GuideScreenBase.providers = providers.endpointmanager.EndpointManagerList(self.app.user_data_dir)

    def build(self, *args):
        #print(f"building   {type(self)}")
        if self.scroll_area is None:  # first build
            self.scroll_area = self.ids.scroll_area
            self.scroll_area.bind(minimum_height=self.scroll_area.setter('height'))
        if self.content_stack is not None:
            print(f"rebuilding {type(self)} content_stack")
            self.scroll_area.remove_widget(self.content_stack)
        self.content_stack = StackLayout(  # create or recreate content_stack
            id = "content_stack",
            size_hint_y = None,
        )
        self.content_stack.bind(minimum_height = self.content_stack.setter('height'))
        self.scroll_area.add_widget(self.content_stack)
        
    def open_url(self, instance, url):
        try:
            getattr(self, url)()  # it's either a local method
        except AttributeError:
            print(f"opening {url} in web browser")
            webbrowser.open(url)  # ... or a web address

    def link_mu(self, text, url):
        return "[ref={}][color=0000ff]{}[/color][/ref]".format(url, text)

    def is_data_valid(self):  # override with method that checks user input
        toast("This method should never be called.")
        return False


class GuideIntro(GuideScreenBase):

    def __init__(self, **kvargs):
        self.name = 'guide_intro'
        super().__init__(**kvargs)
        self.built = False

    def build(self, *args):
        if self.built:
            return
        self.built = True
        super().build(*args)
        heading = GuideTextLabel(
            text = self.app.translation._('[size=30][b]Introduction[/b][/size]'),
        )
        self.content_stack.add_widget(heading)
        main_text = GuideTextLabel(
            text = self.app.translation._(
                'Welcome to the BitBurrow app. If you have not already done so, visit ' + 
                self.link_mu("bitburrow.com", "https://bitburrow.com") + 
                ' for information about BitBurrow, requirements, and how this app fits in. ',
                #'You can also view ' +
                #self.link_mu("a list of supported routers", "router_dialog") + '.',
                normalize_spaces=True),
        )
        main_text.bind(on_ref_press=self.open_url)
        self.content_stack.add_widget(main_text)

    def router_dialog(self):
        items = list()
        for m in self.app.router_models[1:]:
            if m.bb_status == "supported":
                r = TwoLineAvatarListItem(
                    text = " or ".join(m.display_names),
                    secondary_text = m.mfg_page if hasattr(m, 'mfg_page') else "N/A",
                )
                r.add_widget(ImageLeftWidget(source=os.path.join("models", m.id + ".jpg")))
                items.append(r)
        dialog = MDDialog(
            title = 'Supported routers',
            type = "simple",
            items = items,
            #markup = True,  # not available, but on by default
            buttons = [MDFlatButton(
                text = "OK",
                text_color = self.app.theme_cls.primary_color,
                on_press = lambda button: dialog.dismiss(),
            ),],
            size_hint = (0.8, 0.7),
            auto_dismiss = True,
        )
        dialog.open()

    def is_data_valid(self):
        return True


class GuideVpnProvider(GuideScreenBase):

    def __init__(self, **kvargs):
        self.name = 'guide_vpn_provider'
        super().__init__(**kvargs)
        self.previously_selected = dict()
        self.built = False

    def build(self, *args):
        if self.built:
            return
        self.built = True
        super().build(*args)
        heading = GuideTextLabel(
            text = self.app.translation._('[size=30][b]Step 1[/b][/size]'),
        )
        self.content_stack.add_widget(heading)
        main_text = GuideTextLabel(
            text = self.app.translation._(
                'Choose a VPN provider from the list below. ' +
                'If you have not already done so, sign up for a VPN plan ' +
                "on the provider's website.", normalize_spaces=True),
        )
        main_text.bind(on_ref_press=self.open_url)
        self.content_stack.add_widget(main_text)
        provider_list = MDList()
        for i, p in enumerate(GuideScreenBase.providers):
            widget = SelectOne(
                text = "[b]" + p.display_name + "[/b]",
                secondary_text = "website: " + self.link_mu(p.website, p.url)
            )
            widget.ids._lbl_secondary.bind(on_ref_press=self.open_url)  # tapping link opens browser
            widget.index = i
            widget.callback_select = self.set_selected
            provider_list.add_widget(widget)
        self.content_stack.add_widget(provider_list)
    
    def set_selected(self, p):
        GuideScreenBase.form_data['vpn_provider'] = p  # index of VPN provider, 0..n-1
        if p is None:
            return  # UNchecked
        if not self.previously_selected.get(p, False):  # trigger pre-fetch on first tap only
            GuideScreenBase.providers[p].prepare_phonebook()  # pre-fetch endpoint list
            self.previously_selected[p] = True

    def is_data_valid(self):
        if GuideScreenBase.form_data.get('vpn_provider', None) is None:
            toast("Please select a VPN provider.")
            return False
        return True


class GuideVpnCredentials(GuideScreenBase):

    def __init__(self, **kvargs):
        self.name = 'guide_vpn_credentials'
        super().__init__(**kvargs)
        self.build_index = None

    def build(self, *args):
        p = GuideScreenBase.form_data.get('vpn_provider', None)  # user-selected provider
        if p == self.build_index:
            return  # keep existing layout
        self.build_index = p
        super().build(*args)
        provider = GuideScreenBase.providers[p]
        heading = GuideTextLabel(
            text = self.app.translation._('[size=30][b]Step 2[/b][/size]'),
        )
        self.content_stack.add_widget(heading)
        main_text = GuideTextLabel(
            text = self.app.translation._(
                'Enter your credentials for ' +
                provider.display_name + '.', normalize_spaces=True),
        )
        main_text.bind(on_ref_press=self.open_url)
        self.content_stack.add_widget(main_text)
        for cred in provider.credentials:  # fields for user to fill in
            frame = AnchorLayout()
            frame.ffid = True
            frame.size_hint = (1, None)
            frame.padding = dp(20)
            field = MDTextField()
            id = list(cred)[0]
            field.id = id
            for attr in cred[id]:  # cred[id] is a dictionary of MDTextField() attributes
                setattr(field, attr, cred[id][attr])
            frame.add_widget(field)
            self.content_stack.add_widget(frame)

    def is_data_valid(self):
        for cred in self.content_stack.children:  # find the user-entered text fields
            if getattr(cred, 'ffid', False) == False or len(cred.children) != 1:
                continue
            id = cred.children[0].id
            text = cred.children[0].text
            if getattr(cred.children[0], 'required', False) and text == "":
                toast("The {} field cannot be empty.".format(cred.children[0].hint_text.lower()))
                return False
            GuideScreenBase.form_data[id] = text
        return True


class GuideVpnLocation(GuideScreenBase):

    def __init__(self, **kvargs):
        self.name = 'guide_vpn_location'
        super().__init__(**kvargs)
        #self.built = False

    def build(self, *args):
        #if self.built:
        #    return
        #self.built = True
        super().build(*args)
        heading = GuideTextLabel(
            text = self.app.translation._('[size=30][b]Step 3[/b][/size]'),
        )
        self.content_stack.add_widget(heading)
        p = GuideScreenBase.form_data['vpn_provider']
        dl_status = GuideScreenBase.providers[p].status
        if not dl_status.startswith("done"):  # download in progress
            main_text = GuideTextLabel(
                text = self.app.translation._(
                    'Please wait a moment while the list of available locations ' +
                    'finishes downloading.', normalize_spaces=True),
            )
            main_text.bind(on_ref_press=self.open_url)
            self.content_stack.add_widget(main_text)
            spinner = SpinnerBar()
            self.content_stack.add_widget(spinner)
            kivy.clock.Clock.schedule_interval(self.check_dl_status, 0.3)  # call every X seconds
        elif dl_status == "done_failed":  # download failed
            main_text = GuideTextLabel(
                text = self.app.translation._(
                    'Downloading of the list of available locations has failed. Please check ' +
                    'your internet connection and try again.', normalize_spaces=True),
            )
            main_text.bind(on_ref_press=self.open_url)
            self.content_stack.add_widget(main_text)
            retry_bar = RetryButtonBar()
            retry_bar.ids.button_retry.text = "RETRY"
            retry_bar.callback = self.on_retry_button
            self.content_stack.add_widget(retry_bar)
        else:  # download succeeded
            main_text = GuideTextLabel(
                text = self.app.translation._(
                    'Choose a location for your VPN connection from the list below. This will ' +
                    'be used to hide your physical location on the ' +
                    'internet.', normalize_spaces=True),
            )
            main_text.bind(on_ref_press=self.open_url)
            self.content_stack.add_widget(main_text)
            endpoint_list = MDList()
            p = GuideScreenBase.form_data['vpn_provider']
            for country in GuideScreenBase.providers[p].phonebook['providers'][0]['countries']:
                for city in country['cities']:
                    widget = TwoLineAvatarListItem()
                    icon = ImageLeftWidget()
                    icon.source = f"flags/png/256/{country['code']}.png"
                    widget.divider = None
                    widget.type = "two-line"
                    if city['name'] == "":
                        widget.text = country['name']
                    else:
                        widget.text = f"{city['name']}, {country['name']}"
                    l = len(city['servers'])
                    widget.secondary_text = f"{l} server{'' if l == 1 else 's'}"
                    widget.add_widget(icon)
                    widget.on_release = self.on_city_tap
                    endpoint_list.add_widget(widget)
                    # dig further via: for server in city['servers']:
                    # and: for range in server['port_rages_wg_udp']:
            self.content_stack.add_widget(endpoint_list)
    
    def check_dl_status(self, *args):
        p = GuideScreenBase.form_data['vpn_provider']
        dl_status = GuideScreenBase.providers[p].status
        if dl_status.startswith("done"):
            self.build()
            return False  # cancel scheduled check_dl_status()
        return True

    def on_retry_button(self, btn_name):
        p = GuideScreenBase.form_data['vpn_provider']  # index of VPN provider, 0..n-1
        assert p is not None
        GuideScreenBase.providers[p].prepare_phonebook()
        kivy.clock.Clock.schedule_once(self.build)

    def on_city_tap(self):
        print("city clicked")
        # FIXME: access hostname for clicked list item 
        # FIXME: do weighted random choice via random.choices(options, weights)

    def is_data_valid(self):
        toast("Please select a city.")
        return False


class GuideRouterName(Screen):
    pass


class GuideConnectWiFi(Screen):
    #ideas: https://cdn.yankodesign.com/images/design_news/2019/06/what-if-you-could-trick-big-corporations-from-stealing-your-data/winston13.jpg
    #above link from: https://www.yankodesign.com/2019/06/14/this-design-encrypts-your-network-to-prevent-tech-companies-hackers-governments-from-spying-on-you/
    pass


class GuideLogin(Screen):
    pass


class GuideConfigure(Screen):
    pass
