# CRON JOB CONFIGURATION
# Objective: Run the daily report automatically every day at 8:00 PM.
# Requirement: Project PDF - Core Feature #6

# 1. Open the crontab editor in your Linux terminal:
#    crontab -e

# 2. Add the following line at the end of the file:

SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
MAILTO=""

0 20 * * * cd /ABS/PATH/python_git_linux && /usr/bin/flock -n /tmp/daily_report.lock /usr/bin/python3 scripts/daily_report.py >> scripts/daily_report.log 2>&1


# EXPLANATION
# 0 20 * * * -> Runs at 20:00 (8 PM) every day.
# >> ...      -> Appends the output (print statements) to a log file for debugging.
# 2>&1        -> Captures errors as well.
