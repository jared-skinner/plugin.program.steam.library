# python modules
import sys
import os

# xbmc modules
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

from config import *

notify = xbmcgui.Dialog()
addon = xbmcaddon.Addon()

HANDLE = int(sys.argv[1])

CACHE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..\\cache")

def log(msg, level=xbmc.LOGDEBUG):
    if addon.getSetting('debug') == 'true' or level != xbmc.LOGDEBUG:
        xbmc.log('[%s] %s' % (addon.getAddonInfo('id'), msg), level=level)

def initialize():
    log('steam-id = ' + addon.getSetting('steam-id'))
    log('steam-key = ' + addon.getSetting('steam-key'))
    log('steam-exe = ' + addon.getSetting('steam-exe'))
    log('steam-path = ' + addon.getSetting('steam-path'))

    # backwards compatibility for versions prior to 0.6.0
    if addon.getSetting('steam-id') != '' and addon.getSetting('steam-key') != '' and addon.getSetting('steam-path') != '' and addon.getSetting('steam-exe') == '':
        addon.setSetting('steam-exe', addon.getSetting('steam-path'));

        if sys.platform == "linux" or sys.platform == "linux2":
            addon.setSetting('steam-path', os.path.expanduser('~/.steam'));
        elif sys.platform == "win32":
            addon.setSetting('steam-path', os.path.expandvars('%ProgramFiles%\\Steam\\Steam.exe'))
        elif sys.platform == "win64":
            addon.setSetting('steam-path', os.path.expandvars('%ProgramFiles(x86)%\\Steam\\Steam.exe'))

    # all settings are empty, assume this is the first run
    # best guess at steam executable path
    if addon.getSetting('steam-id') == '' and addon.getSetting('steam-key') == '' and addon.getSetting('steam-exe') == '':
        if sys.platform == "linux" or sys.platform == "linux2":
            addon.setSetting('steam-exe', '/usr/bin/steam')
            addon.setSetting('steam-path', os.path.expanduser('~/.steam'));
        elif sys.platform == "darwin":
            addon.setSetting('steam-exe', os.path.expanduser('~/Library/Application Support/Steam/Steam.app/Contents/MacOS/steam_osx'))
            # TODO: not a clue
        elif sys.platform == "win32":
            addon.setSetting('steam-exe', os.path.expandvars('%ProgramFiles%\\Steam\\Steam.exe'))
            addon.setSetting('steam-path', os.path.expandvars('%ProgramFiles%\\Steam\\Steam.exe'))
        elif sys.platform == "win64":
            addon.setSetting('steam-exe', os.path.expandvars('%ProgramFiles(x86)%\\Steam\\Steam.exe'))
            addon.setSetting('steam-path', os.path.expandvars('%ProgramFiles(x86)%\\Steam\\Steam.exe'))

    if addon.getSetting('version') == '':
        # first time run, store version
        addon.setSetting('version', '0.6.0');

    # prompt the user to configure the plugin with their steam details
    if addon.getSetting('steam-id') == '' or addon.getSetting('steam-key') == '':
        addon.openSettings()

    # ensure required data is available
    if os.path.isfile(addon.getSetting('steam-exe')) == False:
        notify.notification('Error', 'Unable to find your Steam executable, please check your settings.', xbmcgui.NOTIFICATION_ERROR)
        return

def add_menu_item(name, appid, set_context_menu=False):
    image_file_path = os.path.join(CACHE_DIR, str(appid) + '.jpg')
    image_url = 'http://cdn.akamai.steamstatic.com/steam/apps/' + str(appid) + '/header.jpg'
    if os.path.exists(image_file_path):
        image_path = image_file_path
    else:
        image_path = image_url

    item  = xbmcgui.ListItem(name, iconImage=image_path, thumbnailImage=image_path)
    item.addContextMenuItems([('Play', 'RunPlugin(plugin://plugin.program.steam.library/run/' + str(appid) + ')'), ('Install', 'RunPlugin(plugin://plugin.program.steam.library/install/' + str(appid) + ')')])
    item.setArt({ 'thumb': image_path})

    if set_context_menu:
        menu_items = [('Play', 'RunPlugin(plugin://plugin.program.steam.library/run/' + str(appid) + ')'),
                      ('Install', 'RunPlugin(plugin://plugin.program.steam.library/install/' + str(appid) + ')')]

        for view in VIEW_LIST:
            menu_items.append(('Mark ' + view, 'RunPlugin(plugin://plugin.program.steam.library/mark_for_view/' + str(appid) + '/' + view + ')'))

        item.addContextMenuItems(menu_items)

    return item
