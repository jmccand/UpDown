import sys
import time
import db
import local
import datetime
import os

def check_corruption(db_files, raise_error=True):
    corruption_cases = [[],[]]
    ids_db, opinions_db, cookies_db, verification_db, calendar_db, device_db = db_files
    for cookie, secure in cookies_db.items():
        if not secure[0] in ids_db:
            corruption_cases[0].append(cookie)
        if not cookie in device_db:
            corruption_cases[1].append(cookie)
    if len(corruption_cases[0]) != 0:
        for cookie in corruption_cases[0]:
            print(f'    {cookie}')
        raise ValueError('DATABASE CORRUPTED!!! Cookie exists with no account!')
    if len(corruption_cases[1]) != 0:
        for cookie in corruption_cases[1]:
            print(f'    {cookie}')
        raise ValueError('DATABASE CORRUPTED!!! Cookie exists with no device info!')
    u_emails = set()
    for u_id, u_account in ids_db.items():
        u_emails.add(u_account.email)
    for v_link, u_email in verification_db.items():
        if u_email not in u_emails:
            if raise_error:
                raise ValueError('DATABASE CORRUPTED!!! Verification link exists with no user account!')
            else:
                return True
            
    print(f'database is healthy as of {datetime.datetime.now()}')
    if raise_error == False:
        return False

def last_healthy():
    file_list = os.listdir(local.BACKUP_DIRECTORY)
    file_list.sort()
    for filename in file_list[::-1]:
        if os.path.isdir(f'{local.BACKUP_DIRECTORY}/{filename}'):
            for ending in local.FILE_ENDINGS:
                if not os.path.exists('{local.BACKUP_DIRECTORY}/{filename}/{ending}'):
                    print(f'WARNING: {filename} is missing some files')
                    break
            else:
                if not check_corruption(tuple(db.open_db(f'{local.BACKUP_DIRECTORY}/{filename}/{ending}', o_type='r') for ending in local.FILE_ENDINGS), raise_error=False):
                    return filename
    return local.LAUNCH_DATE

def excise_corrupted(db_files):
    corruption_cases = [[],[]]
    ids_db, opinions_db, cookies_db, verification_db, calendar_db, device_db = db_files
    for cookie, secure in cookies_db.items():
        if not secure[0] in ids_db:
            corruption_cases[0].append(cookie)
        if not cookie in device_db:
            corruption_cases[1].append(cookie)
    for cookie in corruption_cases[0]:
        print(f'    deleting cookie {cookie}; link to nonexistent account')
        del cookies_db[cookie]
    cookies_db.sync()
    for cookie in corruption_cases[1]:
        print(f'    deleting cookie {cookie}; no device data')
        del cookies_db[cookie]
    cookies_db.sync()
    u_emails = set()
    bad_verification = []
    for u_id, u_account in ids_db.items():
        u_emails.add(u_account.email)
    for v_link, u_email in verification_db.items():
        if u_email not in u_emails:
            bad_verification.append((v_link, u_email))
    for v_link, u_email in bad_verification:
        print(f'    deleting verification link {v_link}; no account under email {u_email}')
        del verification_db[v_link]
    verification_db.sync()

    print(f'    excised corrupted ({len(corruption_cases[0]) + len(corruption_cases[1]) + len(bad_verification)} cases)')

def unverify_all(db_files):
    ids_db, opinions_db, cookies_db, verification_db, calendar_db, device_db = db_files
    u_cookies = list(cookies_db.keys())
    unverify_count = 0
    for u_cookie in u_cookies:
        assert len(cookies_db[u_cookie]) == 2
        if cookies_db[u_cookie][1] != 'unsure':
            cookies_db[u_cookie] = (cookies_db[u_cookie][0], 'unsure')
            unverify_count += 1
    cookies_db.sync()
    print(f'unverified {unverify_count} users')

def main():
    db.init(sys.argv[1])
    if sys.argv[2] == 'check':
        check_corruption((db.user_ids, db.opinions_database, db.cookie_database, db.verification_links, db.opinions_calendar, db.device_info))
    elif sys.argv[2] == 'excise':
        print('EXCISING DATABASE after 10 secs... make sure you have a backup. ctrl-c ctrl-c to cancel')
        for count in range(10, 0, -1):
            print(f'{count} secs...')
            time.sleep(1)
        excise_corrupted((db.user_ids, db.opinions_database, db.cookie_database, db.verification_links, db.opinions_calendar, db.device_info))
    elif sys.argv[2] == 'unverify':
        print('UNVERIFYING ALL USERS after 10 secs... make sure you have a basckup. ctrl-c ctrl-c to cancel')
        for count in range(10, 0, -1):
            print(f'{count} secs...')
            time.sleep(1)
        unverify_all((db.user_ids, db.opinions_database, db.cookie_database, db.verification_links, db.opinions_calendar, db.device_info))


if __name__ == '__main__':
    main()