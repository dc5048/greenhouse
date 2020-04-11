import RaspberryPI_HTU21DF.HTU21DF as Sensor
from time import sleep  # , localtime, time,
from os import listdir, remove
from os.path import expanduser, sep, exists
from array import array
from RPi import GPIO
from datetime import datetime
from multiprocessing import Process
from shutil import chown
import matplotlib.pyplot as plt
from matplotlib.dates import date2num


class greenhouse:
    # Module Data
    # RaspberryPi GPIO Pinout
    VALVE_1 = 22  # Raised Beds
    VALVE_2 = 27  # Greenhouse
    VALVE_3 = 17  # Orchard

    # Valve aliases
    RAISED_BEDS = VALVE_1
    GREENHOUSE = VALVE_2
    ORCHARD = VALVE_3

    # Control characters
    VERBOSE = True
    INIT = False

    def runHourlyCronJob(self):
        """ actions to be performed when called by cron on hourly basis"""
        self.VERBOSE = False  # be silent!
        self.initBoard()
        t = datetime.now()
        if t.hour == 6:  # or t.hour == 18:
            self.openSingleValveOnTimer(self.RAISED_BEDS, 2*60)
            # self.openSingleValveOnTimer(self.GREENHOUSE, 2*60)
        self.logReading()  # do this last so failure won't prevent watering

    def initBoard(self):
        """ setup the GPIO of the Raspberry Pi"""
        GPIO.setmode(GPIO.BCM)  # BCM is used in order to match PIGPIO
        GPIO.setup(self.VALVE_1, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.VALVE_2, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.VALVE_3, GPIO.OUT, initial=GPIO.LOW)
        self.INIT = True

    def openSingleValve(self, valve):
        """ Open single valve, close all others

        valve: a valve number, see class constants for aliases

        To close all valves set 'valve' to zero"""
        GPIO.setmode(GPIO.BCM)  # This matches PIGPIO
        GPIO.output(self.VALVE_1, valve == self.VALVE_1)
        GPIO.output(self.VALVE_2, valve == self.VALVE_2)
        GPIO.output(self.VALVE_3, valve == self.VALVE_3)
        self.logValveCommand(valve)

    def openSingleValveOnTimer(self, valve, nSeconds):
        """ Open single valve, close all others, close after timer expires

        valve: a valve number, see class constants for aliases
        nSeconds: the number of seconds to remain open

        Example: g.openSingleValveOnTimer(g.GREENHOUSE,3*60)
        Opens the greenhouse watering valve for 3 minutes"""
        GPIO.setmode(GPIO.BCM)  # This matches PIGPIO
        self.openSingleValve(valve)
        sleep(nSeconds)
        self.openSingleValve(0)  # close all valves
        if self.VERBOSE is True:
            print('time complete')

    def logReading(self):
        """ Append data to the log file"""
        dt = self.makeNewTimeStampArray()
        with open(self.getLogFile(), 'ab') as f:
            # retry a few times in case I2C or sensor fail to return value
            rTemp = None
            attempt = 0
            while rTemp is None and attempt < 3:
                try:
                    rTemp = Sensor.read_temperature()
                except Exception:
                    sleep(1)
                    attempt += attempt

            rHum = None
            attempt = 0
            while rHum is None and attempt < 3:
                try:
                    rHum = Sensor.read_humidity()
                except Exception:
                    sleep(1)
                    attempt += attempt

            if rTemp is None or rHum is None:
                # return silently, allow other commands to proceed.
                return

            data = [0, rTemp, rHum]
            wrstr = dt + data
            array('f', wrstr).tofile(f)

    def logValveCommand(self, valve):
        """ Append a record of the valve command to the log file

        valve: a valve number, see class constants for aliases"""

        dt = self.makeNewTimeStampArray()
        with open(self.getLogFile(), 'ab') as f:
            data = [1, valve, 0]
            wrstr = dt + data
            array('f', wrstr).tofile(f)

    def printLog(self, filename=None):
        """ Print data from a log file

        filename: file to read from, default the current log"""
        if filename is None:
            filename = self.getLogFile()
        with open(filename, 'rb') as f:
            fin = False
            while not(fin):
                try:
                    a = array('f')
                    a.fromfile(f, 9)
                except(EOFError):
                    fin = True

                if a.buffer_info()[1] > 0:
                    data = a.tolist()
                    dt = datetime(*(int(data.pop(0)) for ii in range(0, 6)))
                    dt_st = dt.strftime('%Y-%b-%d %H:%M:%S')
                    logType = data.pop(0)
                    if logType == 0:
                        # This is a sensor reading log
                        records = '{:0.2f} degC, {:0.2f} %rh'.format(*data)
                    elif logType == 1:
                        # Valve command log
                        records = 'Valve command {:0.0f}'.format(data.pop(0))
                        records = records + ' was issued'

                    print(dt_st+' '+records)

    def plotLog(self, filename=None):
        """ Plot data from a log file

        filename: file to read from, default the current log"""
        if filename is None:
            filename = self.getLogFile()

        with open(filename, 'rb') as f:
            tlog = []
            hlog = []
            vlog = []
            tlogdt = []
            vlogdt = []
            fin = False
            while not(fin):
                try:
                    a = array('f')
                    a.fromfile(f, 9)
                except(EOFError):
                    fin = True

                if a.buffer_info()[1] > 0:
                    data = a.tolist()
                    dt = datetime(*(int(data.pop(0)) for ii in range(0, 6)))
                    # dt_st = dt.strftime('%Y-%b-%d %H:%M:%S')
                    logType = data.pop(0)
                    if logType == 0:
                        # This is a sensor reading log
                        tlogdt.append(dt)
                        tlog.append(data.pop(0))
                        hlog.append(data.pop(0))
                    elif logType == 1 and tlog:
                        # Valve command log
                        vlogdt.append(dt)
                        vlog.append(tlog[-1])  # overlay on temperatures

        tlogdt = date2num(tlogdt)
        fig, ax = plt.subplots(2, 1, sharex=True)
        ax[0].plot_date(tlogdt, tlog, '-', label='temperature')
        ax[0].plot_date(vlogdt, vlog, 'ro', label='watering times')
        handles, labels = ax[0].get_legend_handles_labels()
        ax[0].legend(handles, labels)
        ax[0].xaxis.set_tick_params(rotation=30)
        ax[0].grid(which='both')
        ax[0].set_ylabel('deg C')
        ax[1].plot_date(tlogdt, hlog, 'r--')
        ax[1].xaxis.set_tick_params(rotation=30)
        ax[1].grid(which='both')
        ax[1].set_ylabel('rel humidity %')
        plt.show()

    def plotDateRange(self, start_yymmdd, end_yymmdd):
        """ Grab any data from specified date range and plot it

        start_yymmdd: a string or int containing a date as yymmdd
        end_yymmdd:   a string or int containing a date as yymmdd"""
        if type(start_yymmdd) is int:
            start_yymmdd = str(start_yymmdd)
        if type(end_yymmdd) is int:
            end_yymmdd = str(end_yymmdd)

        p = expanduser('~pi')+sep+'ghlogs'+sep
        tmppth = p + 'templogfile'
        if exists(tmppth):
            remove(tmppth)

        logfiles = listdir(p)
        startdt = datetime.strptime(start_yymmdd, '%y%m%d')
        enddt = datetime.strptime(end_yymmdd, '%y%m%d')
        lgstoread = []
        dtstoread = []
        for logfile in logfiles:
            if logfile == 'current':
                # current is just a pointer to current log file
                continue
            else:
                fdt = self.makeDateTimeFromStamp(logfile)

            if (fdt >= startdt and fdt <= enddt):
                lgstoread.append(logfile)
                dtstoread.append(fdt)

        if len(lgstoread) == 0:
            print('No logs found in the date range')
            return

        zipped = zip(dtstoread, lgstoread)
        srt = sorted(zipped, key=lambda t: t[0])
        dts, lgs = zip(*srt)

        with open(tmppth, 'wb') as f:
            for logfile in lgs:
                with open(p+logfile, 'rb') as lf:
                    f.write(lf.read())

        self.plotLog(tmppth)
        remove(tmppth)

    def debugLog(self):
        """ Modify data from corrupted log file into temporary file

        This is a convenience method for repairing a bad log entry I
        encountered."""
        tmppth = '/home/pi/ghlogs/repairtemp'
        with open(self.getLogFile(), 'rb') as f, open(tmppth, 'wb') as tmp:
            fin = False
            while not(fin):
                try:
                    a = array('f')
                    a.fromfile(f, 9)
                except(EOFError):
                    fin = True

                if a.buffer_info()[1] > 0:
                    if a[0] > 1:
                        a.tofile(tmp)

    def getLogFile(self):
        """ get path string to the current log file"""
        # archives old file and starts new if past duration threshold
        p = expanduser('~pi')+sep+'ghlogs'+sep
        try:
            with open(p+'current', 'r') as f:
                crnt = f.readline()
        except(FileNotFoundError):
            with open(p+'current', 'w') as f:
                crnt = ""

        if not crnt or not self.isLogFileFresh(crnt):
            if self.VERBOSE is True:
                print("Starting new log")
            stamp = self.makeNewTimeStamp()
            with open(p+'current', 'w') as f:
                f.write(stamp)
                crnt = stamp
            with open(p+crnt, 'w') as f:
                pass  # create the empty file
            chown(p+crnt, user='pi', group='pi')

        return p+crnt

    def isLogFileFresh(self, crnt):
        """ sniff check the date stamp

        crnt: the current time stamp"""
        logFile = self.makeDateTimeFromStamp(crnt)
        now = datetime.now()
        diff = now - logFile
        if diff.days > 7:
            return False
        else:
            return True

    def makeNewTimeStampArray(self):
        """ Grab current time & convert to array of ints"""
        t = datetime.now()
        return [t.year, t.month, t.day, t.hour, t.minute, t.second]

    def makeNewTimeStamp(self):
        """ datestamp string of current time"""
        dt = self.makeNewTimeStampArray()
        st = ''
        while len(dt) > 0:
            st = st + str(dt.pop(0)) + "_"

        return st[0:-1]

    def makeDateTimeFromStamp(self, stamp):
        """ Convert the date stamp string to a datetime obj for comparisons

        stamp: the time stamp to be converted"""
        dt = stamp.split("_")
        return datetime(*(int(dt.pop(0)) for ii in range(0, 6)))

    def test(self):
        """ scratchpad method """
        try:
            # Setup the board
            self.initBoard()
            p = Process(target=self.testTimer, args=('test string',))
            p.start()
        except KeyboardInterrupt:
            print('Keyboard interrupt detected; terminating greenhouse')

    def __del__(self):
        """ greenhouse class destructor"""
        try:
            if self.INIT:
                GPIO.cleanup()
        except RuntimeWarning:
            # Allow this to fail silently on exit
            pass


if __name__ == '__main__':
    """ Main entry point set up for hourly cron job"""
    a = greenhouse()
    a.runHourlyCronJob()
