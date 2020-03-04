import os
import queues
import shutdown
import state
import time

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import BooleanProperty
from kivy.clock import Clock
from kivy.properties import ObjectProperty, StringProperty, ListProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput
from kivymd.theming import ThemeManager
from kivymd.toolbar import Toolbar
from kivymd.toast import toast

from addresses import decodeAddress, addBMIfNotPresent
from navigationdrawer import NavigationDrawer
from bmconfigparser import BMConfigParser
from helper_ackPayload import genAckPayload
from helper_sql import sqlExecute
import kivy_helper_search

statusIconColor = 'red'


class NavigateApp(App, TextInput):
    """Application uses kivy in which base Class of Navigate App inherits from the App class."""

    theme_cls = ThemeManager()
    nav_drawer = ObjectProperty()

    def build(self):
        """Return a main_widget as a root widget.

        An application can be built if you return a widget on build(), or if you set
        self.root.
        """
        main_widget = Builder.load_file(
            os.path.join(os.path.dirname(__file__), 'main.kv'))
        self.nav_drawer = Navigator()
        return main_widget

    def getCurrentAccountData(self, text):
        """Get Current Address Account Data."""
        state.association = text
        self.root.ids.sc1.clear_widgets()
        self.root.ids.sc2.clear_widgets()
        self.root.ids.sc3.clear_widgets()
        self.root.ids.sc1.add_widget(Inbox())
        self.root.ids.sc2.add_widget(Sent())
        self.root.ids.sc3.add_widget(Trash())
        self.root.ids.toolbar.title = BMConfigParser().get(
            state.association, 'label') + '({})'.format(state.association)
        Inbox()
        Sent()
        Trash()

    def say_exit(self):
        """Exit the application as uses shutdown PyBitmessage."""
        print("**************************EXITING FROM APPLICATION*****************************")
        App.get_running_app().stop()
        shutdown.doCleanShutdown()

    @staticmethod
    def showmeaddresses(name="text"):
        """Show the addresses in spinner to make as dropdown."""
        if name == "text":
            addrs = BMConfigParser().addresses()
            return addrs[0] if addrs else ''
        elif name == "values":
            return BMConfigParser().addresses()

    def update_index(self, data_index, index):
        """Update index after archieve message to trash."""
        if self.root.ids.scr_mngr.current == 'inbox':
            self.root.ids.sc1.data[data_index]['index'] = index
        elif self.root.ids.scr_mngr.current == 'sent':
            self.root.ids.sc2.data[data_index]['index'] = index
        elif self.root.ids.scr_mngr.current == 'trash':
            self.root.ids.sc3.data[data_index]['index'] = index

    def delete(self, data_index):
        """It will make delete using remove function."""
        print("delete {}".format(data_index))
        self._remove(data_index)

    def archive(self, data_index):
        """It will make archieve using remove function."""
        print("archive {}".format(data_index))
        self._remove(data_index)

    def _remove(self, data_index):
        """It will remove message by resetting the values in recycleview data."""
        screen = {
            'inbox': self.root.ids.sc1,
            'sent': self.root.ids.sc2,
            'trash': self.root.ids.sc3,
        }[self.root.ids.scr_mngr.current]
        screen.data.pop(data_index)
        screen.data = [{
            'data_index': i,
            'index': d['index'],
            'height': d['height'],
            'text': d['text']}
            for i, d in enumerate(self.root.ids.sc1.data)
        ]

    def getInboxMessageDetail(self, instance):
        """It will get message detail after make selected message description."""
        try:
            self.root.ids.scr_mngr.current = 'page'
        except AttributeError:
            self.parent.manager.current = 'page'
        print('Message Clicked {}'.format(instance))

    @staticmethod
    def getCurrentAccount():
        """It uses to get current account label."""
        account_name = BMConfigParser().safeGet(state.association, 'label')
        if account_name is None:
            return "No account"
        return account_name + '({})'.format(state.association)


class Navigator(NavigationDrawer):
    """Navigator class uses NavigationDrawer.

    It is an UI panel that shows our app's main navigation menu
    It is hidden when not in use, but appears when the user swipes
    a finger from the left edge of the screen or, when at the top
    level of the app, the user touches the drawer icon in the app bar
    """

    image_source = StringProperty('images/qidenticon_two.png')
    title = StringProperty('Navigation')


class MessageScreen(Screen):
    data = ListProperty()
    def __init__(self, *args, **kwargs):
        super(MessageScreen, self).__init__(*args, **kwargs)
        if state.association == '':
            state.association = Navigator().ids.btn.text
        Clock.schedule_once(self.init_ui, 0)
    def init_ui(self, dt=0):
        self.screenInit()

    def screenInit(self):
        account = state.association
        self.loadMessagelist(account, 'All', '')


    def loadMessagelist(self, account, where="", what=""):
        queryreturn = kivy_helper_search.search_sql(
            self.xAddress, account, self.box, where, what, False)
        if not queryreturn:
            self.data = [{
                'data_index': 1,
                'index': 1,
                'address': "ebin",
                'height': 48,
                'text': "No incoming for this account."}
            ]
            return
        self.data = [self.parse_row(i, r) for i, r in enumerate(queryreturn)]



class Inbox(MessageScreen):
    box = "inbox"
    xAddress = "toaddress"

    def parse_row(self, i, row):
        return {
            'data_index': i,
            'index': 1,
            "address": row[3],
            "msgid": row[1],
            'height': 48,
            'text': row[4]
        }

class Sent(MessageScreen):
    box = 'sent'
    xAddress = 'fromaddress'

    def parse_row(self, i, row):
        return {
            'data_index': i,
            'index': 1,
            'height': 48,
            'address': row[2],
            'msgid': row[1],
            'text': row[3]
        }

class Trash(MessageScreen):
    box = 'trash'
    xAddress = 'toaddress'

    def parse_row(self, i, row):
        return {
            'data_index': i,
            'index': 1,
            'msgid': row[1],
            'height': 48,
            'text': row[4]
        }



class Message(Screen):
    pass


class AddressSuccessful(Screen):
    pass


class Dialog(Screen):
    """Dialog Screen uses screen to show widgets of screens."""

    pass


class Test(Screen):
    """Test Screen uses screen to show widgets of screens."""

    pass


class Create(Screen):
    """Create Screen uses screen to show widgets of screens."""

    def __init__(self, *args, **kwargs):
        super(Create, self).__init__(*args, **kwargs)

    def send(self):
        """Send message from one address to another."""
        sender = self.ids.sender.text
        recipient = self.ids.recipient.text
        message = self.ids.message.text
        subject = self.ids.subject.text
        encoding = 3
        print("message: ", self.ids.message.text)
        sendMessageToPeople = True
        if sendMessageToPeople:
            if recipient != '':
                status, addressVersionNumber, streamNumber, ripe = decodeAddress(
                    recipient)
                if status != 'success':
                    toast("address {} is invalid".format(recipient))
                    return

                recipient = addBMIfNotPresent(recipient)
                if addressVersionNumber > 4 or addressVersionNumber <= 1:
                    print("addressVersionNumber > 4 or addressVersionNumber <= 1")
                if streamNumber > 1 or streamNumber == 0:
                    print("streamNumber > 1 or streamNumber == 0")
                if statusIconColor == 'red':
                    print("shared.statusIconColor == 'red'")
                stealthLevel = BMConfigParser().safeGetInt(
                    'bitmessagesettings', 'ackstealthlevel')
                ackdata = genAckPayload(streamNumber, stealthLevel)
                t = ()
                sqlExecute(
                    '''INSERT INTO sent VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                    '',
                    recipient,
                    ripe,
                    sender,
                    subject,
                    message,
                    ackdata,
                    int(time.time()),
                    int(time.time()),
                    0,
                    'msgqueued',
                    0,
                    'sent',
                    encoding,
                    BMConfigParser().getint('bitmessagesettings', 'ttl'))
                toLabel = ''
                queues.workerQueue.put(('sendmessage', recipient))
                print("sqlExecute successfully #####    ##################")

                toast("messge sent")
                self.ids.message.text = ''
                self.ids.subject.text = ''
                self.ids.recipient.text = ''
                return None

    def cancel(self):
        """Reset values for send message."""
        self.ids.message.text = ''
        self.ids.subject.text = ''
        self.ids.recipient.text = ''
        return None


class NewIdentity(Screen):
    """Create new address for PyBitmessage."""

    is_active = BooleanProperty(False)
    checked = StringProperty("")
    # self.manager.parent.ids.create.children[0].source = 'images/plus-4-xxl.png'

    def generateaddress(self):
        """Generate new address."""
        if self.checked == 'use a random number generator to make an address':
            queues.apiAddressGeneratorReturnQueue.queue.clear()
            streamNumberForAddress = 1
            label = self.ids.label.text
            eighteenByteRipe = False
            nonceTrialsPerByte = 1000
            payloadLengthExtraBytes = 1000

            queues.addressGeneratorQueue.put((
                'createRandomAddress',
                4, streamNumberForAddress,
                label, 1, "", eighteenByteRipe,
                nonceTrialsPerByte,
                payloadLengthExtraBytes)
            )
            self.manager.current = 'add_sucess'


if __name__ == '__main__':
    NavigateApp().run()
