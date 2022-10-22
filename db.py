import local
import dbm.gnu
import shelve
import threading

already_init = False

def open_db(filename, o_type='c'):
    db = dbm.gnu.open(filename, o_type)
    shelf = shelve.Shelf(db)
    return shelf

def init(d_path=local.DIRECTORY_PATH, o_type='c'):
    global already_init
    if not already_init:
        global user_ids, opinions_database, cookie_database, verification_links, opinions_calendar, device_info, user_ids_lock, opinions_database_lock, cookie_database_lock, verification_links_lock, opinions_calendar_lock, device_info_lock
        # user_cookies = open_db(local.PATH_TO_COOKIES)
        user_ids = open_db(f'{d_path}/ids', o_type)
        opinions_database = open_db(f'{d_path}/opinions', o_type)
        cookie_database = open_db(f'{d_path}/cookies', o_type)
        verification_links = open_db(f'{d_path}/verification', o_type)
        opinions_calendar = open_db(f'{d_path}/calendar', o_type)
        device_info = open_db(f'{d_path}/device', o_type)

        # user_cookies_lock = threading.Lock()
        user_ids_lock = threading.Lock()
        opinions_database_lock = threading.Lock()
        cookie_database_lock = threading.Lock()
        verification_links_lock = threading.Lock()
        opinions_calendar_lock = threading.Lock()
        device_info_lock = threading.Lock()
        already_init = True
