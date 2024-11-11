import flask
from database import Database

app = flask.Flask(__name__)
database = Database()


@app.route('/', methods=['POST'])
def receive_json():
    json = flask.request.json
    print(json)
    database.data_received(json)
    return '', 200
