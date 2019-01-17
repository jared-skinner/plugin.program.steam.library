import requests
import subprocess
import shlex
import sqlite3
import time
import threading
import urllib

from utility import *
from config import *
import registry

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

class Steam():
    def __init__(self):
        self.all_games    = None
        self.recent_games = None

        self.registry_vals = None

        self.sql_conn = sqlite3.connect(os.path.join(CACHE_DIR, "game_cache.db"))
        self.sql_conn.row_factory = dict_factory
        self.sql = self.sql_conn.cursor()

        self.sql.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='games';")
        number_of_rows = self.sql.fetchone()
        if number_of_rows['count(*)'] == 0:
            self.update_cache()

    def get_games_from_steam_api(self):
        try:
            # query the steam web api for a full list of steam
            # applications/games that belong to the user
            all_games = requests.get('https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=' + addon.getSetting('steam-key') + '&steamid=' + addon.getSetting('steam-id') + '&include_appinfo=1&format=json', timeout=10)
            all_games.raise_for_status()
            self.all_games = all_games.json()['response']['games']

            # sleep so the api has time between requests.  It denies requests
            # if they are too close together
            time.sleep(1)

            recent_games = requests.get('https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/?key=' + addon.getSetting('steam-key') + '&steamid=' + addon.getSetting('steam-id') + '&include_appinfo=1&format=json', timeout=10)
            recent_games.raise_for_status()
            self.recent_games = recent_games.json()['response']['games']
        except requests.exceptions.RequestException as e:
            notify.notification('Error', 'An unexpected error has occurred while contacting Steam. Please ensure your Steam credentials are correct and then try again. If this problem persists please contact support.', xbmcgui.NOTIFICATION_ERROR)
            log(str(e), xbmc.LOGERROR)
            return

    def cache_game_thumbs(self, appids):
        # add image to cache
        for appid in appids:
            if not os.path.isfile(os.path.join(CACHE_DIR, str(appid) + '.jpg')):
                urllib.urlretrieve('http://cdn.akamai.steamstatic.com/steam/apps/' + str(appid) + '/header.jpg', os.path.join(CACHE_DIR, str(appid) + '.jpg'))

    def update_cache(self):
        self.get_games_from_steam_api()
        self.refresh_registry_vals()
        self.create_cache_table()

        appids = []
        for game in self.all_games:
            is_recent = self.is_game_recent(game)
            is_installed = self.is_game_installed(game)
            self.sql.execute("INSERT OR IGNORE INTO games (appid, name, is_installed, is_recent VALUES (?,?,?,?);", (game['appid'], game['name'], is_installed, is_recent))
            appids.append(game["appid"]) 

        t = threading.Thread(target=self.cache_game_thumbs, args=(appids,))
        t.start()

        self.sql_conn.commit()

        # ensure we own all games in sql database
        # TODO: we should be able to do this in a single query
        for appid in appids:
            self.sql.execute("SELECT count(*) FROM games WHERE appid=?;", (appid,))
            number_of_rows = self.sql.fetchone()
            if number_of_rows['count(*)'] == 0:
                self.sql.execute("DELETE FROM games where appid=?;", (appid,))

    def refresh_registry_vals(self):
        self.registry_vals = registry.get_registry_values(os.path.join(addon.getSetting('steam-path'), 'registry.vdf'))

    def is_game_installed(self, game):
        # filter out any applications not listed as installed
        if str(game['appid']) in self.registry_vals:
            return True
        return False

    def is_game_recent(self, game):
        for recent_game in self.recent_games:
            if recent_game['appid'] == game['appid']:
                return True
        return False

    def create_cache_table(self):
        query = 'CREATE TABLE IF NOT EXISTS games (appid NUMERIC PRIMARY KEY, name TEXT, is_installed NUMERIC, is_recent NUMERIC'
        for view in VIEW_LIST:
            query += ', ' + view.lower().replace(" ", "_") + ' NUMERIC DEFAULT 0'
        query += ")"
        self.sql.execute(query)

    def get_all_games(self):
        self.sql.execute("SELECT * FROM games")
        return self.sql.fetchall()

    def get_installed_games(self):
        self.sql.execute("SELECT * FROM games WHERE is_installed = 1")
        return self.sql.fetchall()

    def get_recent_games(self):
        self.sql.execute("SELECT * FROM games WHERE is_recent = 1")
        return self.sql.fetchall()

    def get_view(self, view_name):
        log(view_name, xbmc.LOGERROR)
        self.sql.execute("SELECT * FROM games WHERE "+view_name+"=1")
        return self.sql.fetchall()

    def mark_game_for_view(self, appid, view):
        self.sql.execute("UPDATE games SET "+view+"=1 WHERE appid=?;", (appid,))
        self.sql_conn.commit()

    def install_game(self, id):
        log('executing ' + addon.getSetting('steam-exe') + ' steam://install/' + id)
        subprocess.call([addon.getSetting('steam-exe'), 'steam://install/' + id])

    def run_game(self, id):
        userArgs = shlex.split(addon.getSetting('steam-args'))
        log('executing ' + addon.getSetting('steam-exe') + ' ' + addon.getSetting('steam-args') + ' steam://rungameid/' + id)
        subprocess.call([addon.getSetting('steam-exe')] + userArgs + ['steam://rungameid/' + id])
