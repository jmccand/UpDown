import db
from wsgi_main import *

print(f'\n{db.user_cookies}')
for cookie, user in db.user_cookies.items():
    print(f'  {cookie} : User({user.email}, {user.cookie_code}, {user.activity}, {user.votes}, {user.verified_email})')

print(f'\n{db.verification_links}')
for link, ID in db.verification_links.items():
    print(f'  {link} : {ID}')

print(f'\n{db.opinions_database}')
for ID, opinion in db.opinions_database.items():
    print(f'  {ID} : Opinion({opinion.ID}, {opinion.text}, {opinion.activity}, {opinion.approved})')

print(f'\n{db.opinions_calendar}')
sorted_calendar = list(db.opinions_calendar.keys())
sorted_calendar.sort()
for this_date in sorted_calendar:
    ID_set = db.opinions_calendar[this_date]
    print(f'  {this_date} : {ID_set}')
