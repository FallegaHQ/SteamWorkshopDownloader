"""
Configuration file for the Steam Workshop Downloader.
"""

DATA_FILE = "mods.json"
STEAMCMD_PATH = r"steamcmd/steamcmd.exe"

MAIN_WINDOW_WIDTH = 700
MAIN_WINDOW_HEIGHT = 650
MAIN_WINDOW_DIMS = "700x650"
LOG_WINDOW_WIDTH = 700
LOG_WINDOW_HEIGHT = 450
DESCRIPTION_WINDOW_WIDTH = 800
DESCRIPTION_WINDOW_HEIGHT = 600

STEAM_API_URL = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"
REQUEST_TIMEOUT = 10

PROGRESS_UPDATE_INTERVAL = 100

try:
    import tkinterweb as tkweb

    TKINTERWEB_AVAILABLE = True
except ImportError:
    TKINTERWEB_AVAILABLE = False
