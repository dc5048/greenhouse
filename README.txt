A greenhouse controller implemented on a Raspberry Pi 3+ running Raspian and Python 3.5.3.

To set up, git clone the project, then initialize the git submodules to get the sensor interface python module.  Set up a Python virtual environment, then use pip3 install -r with requirements.txt to get the necessary dependencies. Optionally, set up an hourly cron job on the RPi that calls the greenhouse_cron.bash script with /bin/bash.

This controller module reads sensors and actuates valves to monitor and regulate a greenhouse, garden, and orchard. Named GPIO pins activate optical relays, which power 20v AC solenoid valves (these are typical irrigation valves found in most big American hardware store chains.)  Valves can be opened on a timer.

Methods for manual manipulation of sensors, valve actuators, and log data are provided.  The __main__ method serves as an entry point for an hourly cron job.  On Raspian (Debain) this should be set up using crontab with the appropriate username (i.e. not root or the the system crontab files) to avoid permissions conflicts for the log files.

This ongoing personal project has three goals:
1. Automate my garden
2. Learn some new python skills
3. Experiment with an RPi

Because of 2. and 3., not everything is done optimally with regard to 1.  Feedback is welcome, but keep do keep in mind the "why" behind some some questionable choices might just be because it was a way to learn more Python.  :)

Examples:

See "manual_start.py" for initializing the board for manual use, with "g" as the greenhouse object.

# Open valve
g.openSingleValve(g.RAISEDBEDS)

# Close all valves
g.closeValves()

# Water the greenhouse for 30 minutes (valves closed automatically when timer expires)
g.openSingleValveOnTimer(g.GREENHOUSE,30*60)

# Log a temperature/humidity reading from the sensor
g.logReading()

# Look at the most recent log file data
g.printLog

# Plot a log file (defaults to the most recent.)
g.plotLog

# Collate and plot data from log files from June 2019 to May 2020
g.plotDateRange(190601,200501)

