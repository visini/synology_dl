![icon](icon.png)

# Synology DL – macOS Menubar App

Menu bar utility app (macOS) for controlling synology download station.

## Config and customization

```conf
# Example config file, by default it should be located at:
# ~/.config/synology_dl.conf

username     = admin
host         = http://nas.local:5000
password     = password
destinations = NAS/folder_1,NAS/folder_2
```

See `Makefile` for how to debug, build, and release.
