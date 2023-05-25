import subprocess
import local
import time
import datetime

while True:
  # this deletes the files that were backed up, but not the empty directories!
  run_command = 'rsync -rva --exclude "*.new" --remove-source-files %s %s' % (local.PULL_BACKUP_FROM, local.PULL_BACKUP_TO)
  print('\nNow running rsync at time %s\nCOMMAND: %s' % (datetime.datetime.now(), run_command))
  p = subprocess.run(run_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  print('%s\n%s' % (p.stderr.decode("utf-8"), p.stdout.decode("utf-8")))
  print('rsync done!')

  run_command = 'find %s -type d -empty -delete' % local.PULL_BACKUP_FROM
  print('\nNow running empty directory cleanup at time %s\nCOMMAND: %s' % (datetime.datetime.now(), run_command))
  p = subprocess.run(run_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  print('%s\n%s' % (p.stderr.decode("utf-8"), p.stdout.decode("utf-8")))
  print('empty directory cleanup done!; now sleep for %s seconds' % local.DB_SLEEP_DELAY)
  time.sleep(local.DB_SLEEP_DELAY)
