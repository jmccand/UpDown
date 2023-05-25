import subprocess
import local
import time
import datetime

while True:
    run_command = f'rsync -rv --exclude --remove-source-files "*.new" {local.PULL_BACKUP_FROM} {local.PULL_BACKUP_TO}'
    print(f'\nNow running rsync at time {datetime.datetime.now()}\nCOMMAND: {run_command}')
    p = subprocess.run(run_command, shell=True, capture_output=True)
    print(f'{p.stderr.decode("utf-8")}\n{p.stdout.decode("utf-8")}')
    print('rsync done!')
    time.sleep(local.DB_SLEEP_DELAY)
