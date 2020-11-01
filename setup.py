# python3 setup.py py2app

from setuptools import setup

APP = ["main.py"]
DATA_FILES = []
OPTIONS = {
    "argv_emulation": True,
    "iconfile": "icon.icns",
    "plist": {
        "CFBundleShortVersionString": "0.3.0",
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
