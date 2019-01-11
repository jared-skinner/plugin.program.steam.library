# python modules
import os

# 3rd party modules
import routing
plugin = routing.Plugin()

# our modules
import registry
from utility import *
if os.name == 'nt':
    import _winreg

from steam import Steam
steam = Steam()

@plugin.route('/')
def index():
    xbmcplugin.addDirectoryItem(handle=HANDLE, url=plugin.url_for(all),       listitem=xbmcgui.ListItem('All games'),             isFolder=True)
    xbmcplugin.addDirectoryItem(handle=HANDLE, url=plugin.url_for(installed), listitem=xbmcgui.ListItem('Installed games'),       isFolder=True)
    xbmcplugin.addDirectoryItem(handle=HANDLE, url=plugin.url_for(recent),    listitem=xbmcgui.ListItem('Recently played games'), isFolder=True)
    xbmcplugin.endOfDirectory(HANDLE, succeeded=True)

@plugin.route('/all')
def all():
    games = steam.get_all_games()
    for game in games:
        item = add_menu_item(game['name'], game['app_id'], set_context_menu=True)
        if not xbmcplugin.addDirectoryItem(handle=HANDLE, url=plugin.url_for(run, id=str(game['app_id'])), listitem=item, totalItems=len(games)):
            break

    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(HANDLE, succeeded=True)

@plugin.route('/installed')
def installed():
    games = steam.get_installed_games()
    for game in games:
        item = add_menu_item(game['name'], game['app_id'], set_context_menu=True)
        if not xbmcplugin.addDirectoryItem(handle=HANDLE, url=plugin.url_for(run, id=str(game['app_id'])), listitem=item, totalItems=len(games)):
            break

    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(HANDLE, succeeded=True)

@plugin.route('/recent')
def recent():
    games = steam.get_recent_games()
    for game in games:
        item = add_menu_item(game['name'], game['app_id'], set_context_menu=True)
        if not xbmcplugin.addDirectoryItem(handle=HANDLE, url=plugin.url_for(run, id=str(game['app_id'])), listitem=item, totalItems=len(games)):
            break

    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(HANDLE, succeeded=True)

@plugin.route('/install/<id>')
def install(id):
    steam.install_game(id)

@plugin.route('/run/<id>')
def run(id):
    steam.run_game(id)

def main():
    initialize()
    plugin.run()
