from flask import Flask
from greenhouse import greenhouse

app = Flask(__name__)


@app.route('/')
def index():
    ''' Index function '''
    return 'Hello world'


if __name__ == '__main__':
    app.run(host='0.0.0.0')
