from flask import Flask, request, redirect, url_for
from flask import render_template
import RaspberryPI_HTU21DF.HTU21DF as Sensor
import greenhouse
from time import sleep


APP = Flask(__name__)
GH = greenhouse.greenhouse()


@APP.route('/')
def index():
    ''' Index function '''
    attempt = 0
    rTemp = None
    while rTemp is None and attempt < 3:
        # try a few times in case i2c service fails
        try:
            rTemp = Sensor.read_temperature()
        except Exception:
            sleep(1)
            attempt += attempt

    attempt = 0
    rHumi = None
    while rHumi is None and attempt < 3:
        try:
            rHumi = Sensor.read_humidity()
        except Exception:
            sleep(1)
            attempt += attempt

    msg = GH.__statusthreads__()
    if rTemp is None or rHumi is None:
        report = "Failed to read the temperature sensor.  Sorry :("
    else:
        sTemp = "{:0.2f}".format(rTemp)
        sHumi = "{:0.2f}".format(rHumi)
        report = render_template('index.html', temp=sTemp, humi=sHumi,
                                 msg=msg)

    return report


@APP.route('/water', methods=['POST'])
def water():
    ''' apply the watering commands '''
    t_min = int(request.form['raisedbedstime'])
    if t_min > 0:
        GH.openSingleValveOnTimer(GH.RAISED_BEDS, t_min*60)

    t_min = int(request.form['greenhousetime'])
    if t_min > 0:
        GH.openSingleValveOnTimer(GH.GREENHOUSE, t_min*60)

    t_min = int(request.form['orchardtime'])
    if t_min > 0:
        GH.openSingleValveOnTimer(GH.ORCHARD, t_min*60)

    return redirect(url_for('index'))


if __name__ == '__main__':
    GH.VERBOSE = False
    APP.run(host='0.0.0.0')
