'''
get registry values for steam games
'''

# python modules
import os, _winreg
from utility import log

# xbmc modules
import xbmc

# https://github.com/lutris/lutris/blob/master/lutris/util/steam.py
def vdf_parse(steam_config_file, config):
    """Parse a Steam config file and return the contents as a dict."""
    line = " "
    while line:
        try:
            line = steam_config_file.readline()
        except UnicodeDecodeError:
            log("Error while reading Steam VDF file {}. Returning {}".format(steam_config_file, config), xbmc.LOGERROR)
            return config
        if not line or line.strip() == "}":
            return config
        while not line.strip().endswith("\""):
            nextline = steam_config_file.readline()
            if not nextline:
                break
            line = line[:-1] + nextline

        line_elements = line.strip().split("\"")
        if len(line_elements) == 3:
            key = line_elements[1]
            steam_config_file.readline()  # skip '{'
            config[key] = vdf_parse(steam_config_file, {})
        else:
            try:
                config[line_elements[1]] = line_elements[3]
            except IndexError:
                log('Malformed config file: {}'.format(line), xbmc.LOGERROR)
    return config

def is_installed(app_id):
    app = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, "Software\\Valve\\Steam\\Apps\\" + app_id)
    try:
        i = 0
        while 1:
            name, value, type = _winreg.EnumValue(app, i)
            if name == "Installed":
                return value
            i += 1
    except WindowsError:
        return None

def get_registry_values(registry_path):
    app_dict = {}

    if os.name == 'nt':
        apps = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, "Software\\Valve\\Steam\\Apps")
        try:
            i = 0
            while True:
                app_id = _winreg.EnumKey(apps, i)
                #print(app_id)
                installed = is_installed(app_id)
                if installed is None:
                    i += 1
                    continue
                else:
                    app_dict[app_id] = installed
                    i += 1
        
        except WindowsError:
            pass
    else:
        with open(registry_path, 'r') as file:
            vdf = vdf_parse(file, {})
            apps = vdf['Registry']['HKCU']['Software']['Valve']['Steam']['Apps']
            app_dict = dict((k, v) for (k, v) in apps.iteritems() if v.get('installed', '0') == '1')

    return app_dict
