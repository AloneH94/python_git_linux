# CRON JOB CONFIGURATION
# Objective: Run the daily report automatically every day at 8:00 PM.
# Requirement of the project

#Launch the Linux terminal's crontab editor:
#    crontab -e

#Put the following line at the file's conclusion.:

SHELL=/bin/bash

0 20 * * * cd /ABS/PATH/python_git_linux && /usr/bin/flock -n /tmp/daily_report.lock /usr/bin/python3 scripts/daily_report.py >> scripts/daily_report.log 2>&1


# EXPLANATION
# 0 20        Runs at 20:00 (8 PM) every day.
# >>          Appends the output (print statements) to a log file for debugging.
# 2>&1        Captures errors as well.
