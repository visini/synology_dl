import os
import logging
import requests
import json
import configparser


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
            # As DEFAULT is included in all other sections when reading
            # items/options add empty DEFAULT section and use BASE as base config
            # section.
            yield "[DEFAULT]\n"
            yield "[" + self.base_config_name + "]\n"
            # Next yield the actual config file next
            for line in config_file:
                yield line
        return super().read_file(no_default_header_config_file(f), source)

    def get_default(self, option, *args, **kwargs):
        """Gets an option from the default context."""
        return super().get(self.base_config_name, option, *args, **kwargs)


def read_config(config_fn):
    """Reads (parses) given config file.

    Returns:
        (str|None, str|None, str|None). Username, host, password 3-tuple.

    Parameters:
        config_fn: str. Config file name (path).
    """
    log = logging.getLogger(__name__)

    def get_option(opt_name):
        try:
            return config.get_default(opt_name)
        except configparser.NoOptionError as e:
            log.error("Config file did not contain value for '{}'.".format(opt_name))
        return None

    config = NoDefaultHeaderConfigParser()
    config_fn = os.path.expanduser(config_fn)

    # Parse config file to the config
    if os.path.exists(config_fn):
        with open(config_fn) as cf:
            config.read_file(cf, source=config_fn)
    else:
        log.error("Could not open config file: {}".format(config_fn))
        return None, None, None

    username = get_option("username")
    host = get_option("host")
    password = get_option("password")
    return username, host, password


def read_config_destinations(config_fn):
    """Reads (parses) given config file.

    Returns:
        (str|None, str|None, str|None). Username, host, password 3-tuple.

    Parameters:
        config_fn: str. Config file name (path).
    """
    log = logging.getLogger(__name__)

    def get_option(opt_name):
        try:
            return config.get_default(opt_name)
        except configparser.NoOptionError as e:
            log.error("Config file did not contain value for '{}'.".format(opt_name))
        return None

    config = NoDefaultHeaderConfigParser()
    config_fn = os.path.expanduser(config_fn)

    # Parse config file to the config
    if os.path.exists(config_fn):
        with open(config_fn) as cf:
            config.read_file(cf, source=config_fn)
    else:
        log.error("Could not open config file: {}".format(config_fn))
        return None, None, None

    destinations = get_option("destinations").split(",")
    return destinations


def send_url(add_url, config_file, destination):
    """Sends the given url Synology DownloadStation.

    Now handles only local files and urls which start with "http:"
    """

    log = logging.getLogger(__name__)
    log.debug("Using config file: {}".format(config_file))
    log.debug("Adding url: {}".format(add_url))

    username, host, password = read_config(config_file)
    if not username or not host or not password:
        return False

    host = host + "/webapi"
    url_auth = host + "/auth.cgi"
    url_ds = host + "/DownloadStation/task.cgi"

    # Init session and geth auth token
    data = {
        'api': 'SYNO.API.Auth',
        'version': '2',
        'method': 'login',
        'account': username,
        'passwd': password,
        'session': 'DownloadStation',
        'format': 'sid'
    }
    r = requests.post(url=url_auth, data=data, verify=False)
    if r.status_code != 200:
        log.error("Auth request failed with status code: {}",format(r.status_code))
        return False
    rj = json.loads(r.text)
    if not rj['success']:
        log.error("Auth failed with response data: {}".format(rj))
        return False
    auth = rj['data']['sid']

    session = requests.session() # XXX: is this only for cookie and not sid
    # Send local file
    if not add_url.startswith("http:") and not add_url.startswith("magnet:"):
        with open(add_url,'rb') as payload:
            args = {
                    'api': 'SYNO.DownloadStation.Task',
                    'version': '1',
                    'method': 'create',
                    'session': 'DownloadStation',
                    '_sid': auth
                    }
            files = {'file': (add_url, payload)}
            r = session.post(url_ds, data=args, files=files, verify=False)
            if r.status_code != 200:
                log.error("Add file request failed with status code: {}",format(r.status_code))
                return False
            rj = json.loads(r.text)
            if not rj['success']:
                log.error("Add file failed with response data: {}".format(rj))
                return False
    else:
        # Send the url
        data = {
            'api': 'SYNO.DownloadStation.Task',
            'version': '1',
            'method': 'create',
            'session': 'DownloadStation',
            '_sid': auth,
            'uri': add_url,
            'destination': destination
        }
        r = session.post(url=url_ds, data=data, verify=False)
        if r.status_code != 200:
            log.error("Add uri request failed with status code: {}",format(r.status_code))
            return False
        rj = json.loads(r.text)
        if not rj['success']:
            log.error("Add uri failed with response data: {}".format(rj))
            return False

    # Logout
    data = {
        'api': 'SYNO.API.Auth',
        'version': '1',
        'method': 'logout',
        'session': 'DownloadStation',
    }
    r = session.post(url_auth, data=data, verify=False)
    if r.status_code != 200:
        log.error("Logout request failed with status code: {}",format(r.status_code))
        return False
    rj = json.loads(r.text)
    if not rj['success']:
        log.error("Logout failed with response data: {}".format(rj))
        return False

    return True


