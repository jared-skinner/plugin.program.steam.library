import requests
import subprocess
import shlex
import sqlite3
import time

from utility import *
import registry

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

class SteamGame():
    def __init__(self, name, app_id, recent_games):
        self.name          = name
        self.app_id        = app_id
        self.is_installed  = False
        self.is_recent     = False

        # it's kinda dumb to have to pass this in, but I couldn't think of a
        # better way to make a single call to the steam api for recent games
        # without doing something dumber...
        self.recent_games = recent_games

        self.registry_vals = []

        self.refresh_registry_vals()
        self.is_game_installed()
        self.is_game_recent()

    def is_game_installed(self):
        # filter out any applications not listed as installed
        if str(self.app_id) in self.registry_vals:
            self.is_installed = True

    def is_game_recent(self):
        for game in self.recent_games:
            if game['appid'] == self.app_id:
                self.is_recent = True

    def refresh_registry_vals(self):
        self.registry_vals = registry.get_registry_values(os.path.join(addon.getSetting('steam-path'), 'registry.vdf'))

    def update_game_data(self):
        self.is_game_installed()
        self.is_game_recent()
        self.refresh_registry_vals()


class Steam():
    def __init__(self):
        self.games = []
        self.sql_conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..\cache\game_cache.db"))
        self.sql_conn.row_factory = dict_factory
        self.sql = self.sql_conn.cursor()

        self.sql.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='games';")
        row = self.sql.fetchone()
        if row is None:
            self.get_games()
            self.rebuild_games_cache()

    def get_games(self):
        self.games = []
        try:
            # query the steam web api for a full list of steam
            # applications/games that belong to the user
            owned_games = requests.get('https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=' + addon.getSetting('steam-key') + '&steamid=' + addon.getSetting('steam-id') + '&include_appinfo=1&format=json', timeout=10)
            owned_games.raise_for_status()

            # sleep so the api has time between requests.  It denies requests
            # if they are too close together
            time.sleep(1)

            recent_games = requests.get('https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/?key=' + addon.getSetting('steam-key') + '&steamid=' + addon.getSetting('steam-id') + '&include_appinfo=1&format=json', timeout=10)
            recent_games.raise_for_status()
            recent_games = recent_games.json()['response']['games']


            for game in owned_games.json()['response']['games']:
                self.games.append(SteamGame(game["name"], game["appid"], recent_games))

        except requests.exceptions.RequestException as e:
            # something went wrong, can't scan the steam library
            notify.notification('Error', 'An unexpected error has occurred while contacting Steam. Please ensure your Steam credentials are correct and then try again. If this problem persists please contact support.', xbmcgui.NOTIFICATION_ERROR)
            log(str(e), xbmc.LOGERROR)
            return

    def build_games_cache(self):
        self.create_cache_table()
        self.cache_games()

    def rebuild_games_cache(self):
        self.drop_cache_table()
        self.create_cache_table()
        self.cache_games()

    def drop_cache_table(self):
        self.sql.execute('DROP TABLE IF EXISTS games')

    def create_cache_table(self):
        self.sql.execute('CREATE TABLE IF NOT EXISTS games (app_id NUMERIC PRIMARY KEY, name TEXT, is_installed NUMERIC, is_recent NUMERIC)')

    def cache_games(self):
        '''
        Store game data in a sqlite database for quick retrival
        '''
        game_data = []
        for game in self.games:
            #log(game.name, xbmc.LOGERROR)
            game_data.append((game.name, game.app_id, game.is_installed, game.is_recent))

            if game.is_installed:
                is_installed = "1" 
            else:
                is_installed = "0"

            if game.is_recent:
                is_recent = "1" 
            else:
                is_recent = "0"

            self.sql.execute("INSERT INTO games (app_id, name, is_installed, is_recent) VALUES (?,?,?,?);", (game.app_id, game.name, is_installed, is_recent))

        self.sql_conn.commit()

    def get_all_games(self):
        self.sql.execute("SELECT * FROM games")
        return self.sql.fetchall()

    def get_installed_games(self):
        self.sql.execute("SELECT * FROM games WHERE is_installed = 1")
        return self.sql.fetchall()

    def get_recent_games(self):
        self.sql.execute("SELECT * FROM games WHERE is_recent = 1")
        return self.sql.fetchall()

    def install_game(self, id):
        log('executing ' + addon.getSetting('steam-exe') + ' steam://install/' + id)

        # https://developer.valvesoftware.com/wiki/Steam_browser_protocol
        subprocess.call([addon.getSetting('steam-exe'), 'steam://install/' + id])

    def run_game(self, id):
        userArgs = shlex.split(addon.getSetting('steam-args'))
        log('executing ' + addon.getSetting('steam-exe') + ' ' + addon.getSetting('steam-args') + ' steam://rungameid/' + id)

        # https://developer.valvesoftware.com/wiki/Steam_browser_protocol
        subprocess.call([addon.getSetting('steam-exe')] + userArgs + ['steam://rungameid/' + id])
