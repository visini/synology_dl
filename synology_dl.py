import rumps
import xerox
from ds_down import send_url, read_config_destinations

config_file = "~/.config/synology_dl.conf"

class SynologyDLApp(object):

    def set_destination(self, sender, destination):
        for btn in [self.button_default_destination, *self.buttons.values()]:
            if sender.title == btn.title:
                self.destination = destination
                btn.state = True
            elif sender.title != btn.title:
                btn.state = False

    def add_magnet(self, sender):
        clipboard = xerox.paste()
        if clipboard.startswith("magnet:"):
            print("adding magnet for ...", clipboard)
            send_url(clipboard, config_file, self.destination)
        else:
            window = rumps.Window('Use right click + paste to add magnet:', 'Add Magnet')
            window.title = 'Manually add magnet'
            response = window.run()
            if response.text.startswith("magnet:"):
                print("adding magnet for ...", clipboard)
                send_url(response.text, config_file, self.destination)

    def __init__(self, timer_interval=1):
        self.app = rumps.App("Synology DL", "🌚")
        self.destination = ""
        self.clipboard_button = rumps.MenuItem(title='Paste from clipboard', callback=self.add_magnet)
        self.button_default_destination = rumps.MenuItem(title="Default Destination", callback=lambda _: self.set_destination(_, ""))
        self.button_default_destination.state = True
        self.buttons = {}
        self.buttons_callback = {}
        config_destinations = read_config_destinations(config_file)
        for i in config_destinations:
            title = str(i)
            callback = lambda _, j=i: self.set_destination(_, j)
            self.buttons["btn_" + str(i)] = rumps.MenuItem(title=title, callback=callback)
            self.buttons_callback[title] = callback
        self.app.menu = [
            self.clipboard_button,
            None,
            self.button_default_destination,
            *self.buttons.values()
        ]

    def run(self):
        self.app.run()


if __name__ == "__main__":
    app = SynologyDLApp()
    app.run()
