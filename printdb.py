import sys
import local
import db
db.init(sys.argv[1], 'r')
import db_corruption

print(f'\nUSER IDS:\n{db.user_ids}')
for this_user_ID, user in db.user_ids.items():
    # print(f'  {this_user_ID} : User({user.email}, {user.user_ID}, {user.activity}, {user.votes}, {user.obselete})')
    print(f'  {this_user_ID} : User({user.email}, {user.user_ID}, activity, {user.votes}, {user.obselete})')

print(f'\nCOOKIE DATABASE:\n{db.cookie_database}')
for cookie, this_secure in db.cookie_database.items():
    print(f'  {cookie} : {this_secure}')

print(f'\nVERIFICATION LINKS:\n{db.verification_links}')
for link, email in db.verification_links.items():
    print(f'  {link} : {email}')

print(f'\nOPINIONS DATABASE:\n{db.opinions_database}')
for ID, opinion in db.opinions_database.items():
    print(f'  {ID} : Opinion({opinion.ID}, {opinion.text}, {opinion.activity}, {opinion.approved}, {opinion.scheduled}, {opinion.reserved_for}, {opinion.bill}, {opinion.resolved})')

print(f'\nOPINIONS CALENDAR:\n{db.opinions_calendar}')
sorted_calendar = list(db.opinions_calendar.keys())
sorted_calendar.sort()
for this_date in sorted_calendar:
    ID_set = db.opinions_calendar[this_date]
    print(f'  {this_date} : {ID_set}')

print(f'\nDEVICE INFO:\n{db.device_info}')
for cookie, info in db.device_info.items():
    print(f'  {cookie} : {info}')

try:
    db_corruption.check_corruption((db.user_ids, db.opinions_database, db.cookie_database, db.verification_links, db.opinions_calendar, db.device_info))
except ValueError as e:
    print(e)
    if len(sys.argv) > 2:
        if sys.argv[2] == 'last_healthy':
            print(f'last healthy on backup {db_corruption.last_healthy()}')
        else:
            raise ValueError(f'sys.argv[2] is {sys.argv[2]}, should be last_healthy')
