import local
import dbm.gnu
import shelve
import threading

def open_db(filename):
    db = dbm.gnu.open(filename, 'c')
    shelf = shelve.Shelf(db)
    return shelf

user_ids = open_db(local.PATH_TO_IDS)
opinions_database = open_db(local.PATH_TO_OPINIONS)
cookie_database = open_db(local.PATH_TO_COOKIES)
verification_links = open_db(local.PATH_TO_VERIFICATION)
opinions_calendar = open_db(local.PATH_TO_CALENDAR)

user_cookies_lock = threading.Lock()
opinions_database_lock = threading.Lock()
verification_links_lock = threading.Lock()
opinions_calendar_lock = threading.Lock()
