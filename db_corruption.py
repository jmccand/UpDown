import db
import local
import datetime
import os

def check_corruption(raise_error=True):
    for cookie, secure in db.cookie_database.items():
        if not secure[0] in db.user_ids:
            raise ValueError('DATABASE CORRUPTED!!! Cookie exists with no account!')
        if not cookie in db.device_info:
            raise ValueError('DATABASE CORRUPTED!!! Cookie exists with no device info!')
    u_emails = set()
    for u_id, u_account in db.user_ids.items():
        u_emails.add(u_account.email)
    for v_link, u_email in db.verification_links.items():
        if u_email not in u_emails:
            if raise_error:
                raise ValueError('DATABASE CORRUPTED!!! Verification link exists with no user account!')
            else:
                return False
    print(f'database is healthy as of {datetime.datetime.now()}')
    if raise_error == False:
        return True
