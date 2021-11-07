import local
import dbm.dumb
import shelve

def open_db(filename):
    db = dbm.dumb.open(filename)
    shelf = shelve.Shelf(db)
    return shelf

user_cookies = open_db(local.PATH_TO_COOKIES)
opinions_database = open_db(local.PATH_TO_OPINIONS)
