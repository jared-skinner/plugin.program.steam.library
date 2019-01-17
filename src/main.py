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

from config import *

from steam import Steam
steam = Steam()

@plugin.route('/')
def index():
    xbmcplugin.addDirectoryItem(handle=HANDLE, url=plugin.url_for(all),            listitem=xbmcgui.ListItem('All games'),             isFolder=True)
    xbmcplugin.addDirectoryItem(handle=HANDLE, url=plugin.url_for(installed),      listitem=xbmcgui.ListItem('Installed games'),       isFolder=True)
    xbmcplugin.addDirectoryItem(handle=HANDLE, url=plugin.url_for(recent),         listitem=xbmcgui.ListItem('Recently played games'), isFolder=True)

    for view in VIEW_LIST:
        xbmcplugin.addDirectoryItem(handle=HANDLE, url=plugin.url_for(get_view, view_name=view),    listitem=xbmcgui.ListItem(view),     isFolder=True)

    xbmcplugin.addDirectoryItem(handle=HANDLE, url=plugin.url_for(update_cache),   listitem=xbmcgui.ListItem('Update Cache'),          isFolder=True)
    xbmcplugin.endOfDirectory(HANDLE, succeeded=True)

@plugin.route('/all')
def all():
    games = steam.get_all_games()
    for game in games:
        item = add_menu_item(game['name'], game['appid'], set_context_menu=True)
        if not xbmcplugin.addDirectoryItem(handle=HANDLE, url=plugin.url_for(run, id=str(game['appid'])), listitem=item, totalItems=len(games)):
            break

    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(HANDLE, succeeded=True)

@plugin.route('/installed')
def installed():
    games = steam.get_installed_games()
    for game in games:
        item = add_menu_item(game['name'], game['appid'], set_context_menu=True)
        if not xbmcplugin.addDirectoryItem(handle=HANDLE, url=plugin.url_for(run, id=str(game['appid'])), listitem=item, totalItems=len(games)):
            break

    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(HANDLE, succeeded=True)

@plugin.route('/recent')
def recent():
    games = steam.get_recent_games()
    for game in games:
        item = add_menu_item(game['name'], game['appid'], set_context_menu=True)
        if not xbmcplugin.addDirectoryItem(handle=HANDLE, url=plugin.url_for(run, id=str(game['appid'])), listitem=item, totalItems=len(games)):
            break

    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(HANDLE, succeeded=True)

@plugin.route('/get_view/<view_name>')
def get_view(view_name):
    # convert view_name to sql argument
    view_name = view_name.lower().replace(" ", "_")
    games = steam.get_view(view_name)
    for game in games:
        item = add_menu_item(game['name'], game['appid'], set_context_menu=True)
        if not xbmcplugin.addDirectoryItem(handle=HANDLE, url=plugin.url_for(run, id=str(game['appid'])), listitem=item, totalItems=len(games)):
            break

    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(HANDLE, succeeded=True)

@plugin.route('/install/<id>')
def install(id):
    steam.install_game(id)

@plugin.route('/run/<id>')
def run(id):
    steam.run_game(id)

@plugin.route('/mark_for_view/<id>/<view_name>')
def mark_for_view(id, view_name):
    steam.mark_game_for_view(id, view_name.lower().replace(" ", "_"))

@plugin.route('/update_cache/')
def update_cache():
    steam.update_cache()

def main():
    initialize()
    plugin.run()
