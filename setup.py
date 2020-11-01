import os
from setuptools import setup

VERSION = "0.0.1"
if "VERSION" in os.environ:
    VERSION = os.getenv("VERSION")


APP = ["main.py"]
DATA_FILES = []
OPTIONS = {
    "argv_emulation": True,
    "iconfile": "icon.icns",
    "plist": {
        "CFBundleShortVersionString": VERSION,
        "LSUIElement": True,
    },
    "packages": ["rumps"],
}

setup(
    app=APP,
    name="Synology DL",
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
