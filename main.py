import os
import platform
import rumps
import xerox
import requests as rq
import json
import configparser


def get_path(filename):
    name = os.path.splitext(filename)[0]
    ext = os.path.splitext(filename)[1]
    if platform.system() == "Darwin":
        from AppKit import NSBundle

        file = NSBundle.mainBundle().pathForResource_ofType_(name, ext)
        return file or os.path.realpath(filename)
    else:
        return os.path.realpath(filename)


config_file = "~/.config/synology_dl.conf"


class NoDefaultHeaderConfigParser(configparser.ConfigParser):
    """ConfigParser without the need of default section."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_config_name = "BASE_CONFIG_98f93"

    def read_file(self, f, source=None):
        def no_default_header_config_file(config_file):
            """Generator which wraps config_file and gives DEFAULT section header as
            the first line.
            Parameters:
                config_file: file like object. Open config file.
            """
            yield "[DEFAULT]\n"
            yield "[" + self.base_config_name + "]\n"
            for line in config_file:
                yield line

        return super().read_file(no_default_header_config_file(f), source)

    def get_default(self, option, *args, **kwargs):
        """Gets an option from the default context."""
        return super().get(self.base_config_name, option, *args, **kwargs)


class SynologyDLApp(object):
    def set_destination(self, sender, destination):
        for btn in [self.button_default_destination, *self.buttons.values()]:
            if sender.title == btn.title:
                self.destination = destination
                btn.state = True
            elif sender.title != btn.title:
                btn.state = False

    def read_config(self, config_fn):
        def get_option(opt_name):
            try:
                return config.get_default(opt_name)
            except configparser.NoOptionError as e:
                print(e)
                print(
                    "Config file did not contain value for '{}'.".format(
                        opt_name
                    )
                )
            return None

        config = NoDefaultHeaderConfigParser()
        config_fn = os.path.expanduser(config_fn)

        # Parse config file to the config
        if os.path.exists(config_fn):
            file = get_path(config_fn)
            with open(file) as cf:
                config.read_file(cf, source=config_fn)
        else:
            print("Could not open config file: {}".format(config_fn))
            return None, None, None

        username = get_option("username")
        host = get_option("host")
        password = get_option("password")
        destinations = get_option("destinations")
        return username, host, password, destinations

    def auth(self):
        auth_endpoint = f"{self.url_auth}?api=SYNO.API.Auth&version=6&method=login&account={self.username}&passwd={self.password}&session=FileStation&format=cookie"
        r = rq.get(auth_endpoint)
        print("a",auth_endpoint)
        print("b",r.text)
        rj = json.loads(r.text)
        if r.status_code != 200 or not rj["success"]:
            print("Auth failed with response data: {}".format(rj))
            rumps.notification(
                title="Error", subtitle="Auth failed...", message=""
            )
            return False
        else:
            print("Auth successful")
            sid = rj["data"]["sid"]
            return sid

    def logout(self):
        data = {
            "api": "SYNO.API.Auth",
            "version": "1",
            "method": "logout",
            "session": "DownloadStation",
        }
        r = rq.post(url=self.url_auth, data=data)
        rj = json.loads(r.text)
        if r.status_code != 200 or not rj["success"]:
            print("Logout failed with response data: {}".format(rj))
            rumps.notification(
                title="Error", subtitle="Logout failed...", message=""
            )
            return False
        else:
            print("Logout successful")
            return True

    def create(self, magnet, destination):
        sid = self.auth()
        print("sid", sid)
        data = {
            "api": "SYNO.DownloadStation.Task",
            "version": "1",
            "method": "create",
            "session": "DownloadStation",
            "_sid": sid,
            "uri": magnet,
            "destination": destination,
        }
        r = rq.post(self.url_ds, data=data)
        rj = json.loads(r.text)
        if r.status_code != 200 or not rj["success"]:
            print("Create failed with response data: {}".format(rj))
            rumps.notification(
                title="Error", subtitle="Create failed...", message=""
            )
            return False
        else:
            print("Create successful")
            rumps.notification(
                title="Success",
                subtitle="Added to " + destination,
                message="",
            )
        self.logout()

    def add_magnet(self, sender):
        clipboard = xerox.paste()
        if clipboard.startswith("magnet:"):
            print("Adding magnet for ...", clipboard)
            magnet = clipboard
            # send_url(clipboard, config_file, self.destination)
            self.create(magnet, self.destination)
        else:
            window = rumps.Window(
                "Use right click + paste to add magnet:", "Add Magnet"
            )
            window.title = "Manually add magnet"
            response = window.run()
            if response.text.startswith("magnet:"):
                print("Adding magnet for ...", response.text)
                magnet = response.text
                # send_url(response.text, config_file, self.destination)
                self.create(magnet, self.destination)

    def __init__(self, timer_interval=1):

        self.app = rumps.App("Synology DL", "🌚")
        self.destination = ""
        self.clipboard_button = rumps.MenuItem(
            title="Paste from clipboard", callback=self.add_magnet
        )
        self.button_default_destination = rumps.MenuItem(
            title="Default Destination",
            callback=lambda _: self.set_destination(_, ""),
        )
        self.button_default_destination.state = True
        self.buttons = {}
        self.buttons_callback = {}
        (
            self.username,
            self.host,
            self.password,
            self.destinations,
        ) = self.read_config(config_file)

        self.host = self.host + "/webapi"
        self.url_auth = self.host + "/entry.cgi"
        self.url_ds = self.host + "/DownloadStation/task.cgi"

        self.destinations = self.destinations.split(",")

        for i in self.destinations:
            title = str(i)
            callback = lambda _, j=i: self.set_destination(_, j)
            self.buttons["btn_" + str(i)] = rumps.MenuItem(
                title=title, callback=callback
            )
            self.buttons_callback[title] = callback
        self.app.menu = [
            self.clipboard_button,
            None,
            self.button_default_destination,
            *self.buttons.values(),
        ]

    def run(self):
        self.app.run()


if __name__ == "__main__":
    app = SynologyDLApp()
    app.run()
