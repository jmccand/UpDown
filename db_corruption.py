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
