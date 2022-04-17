import subprocess
import local
import time
import datetime

while True:
    time.sleep(local.DB_SLEEP_DELAY)
    print(f'\nNow running rsync at time {datetime.datetime.now()}')
    run_command = f'rsync -rv --exclude "*.new" {local.PULL_BACKUP_FROM} {local.PULL_BACKUP_TO}'
    p = subprocess.run(run_command, shell=True, capture_output=True)
    if p.returncode != 0:
        print(f'{p.standarderr}\n{p.standardout}')
