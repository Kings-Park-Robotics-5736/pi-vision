import io
import json
import typing
import cv2
import flask
from flask_cors import CORS

import app_contexts
import shared_context


app = flask.Flask(__name__, static_folder='./build/', static_url_path='/')
CORS(app)


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/api/current-config' , methods = ['GET'])
def get_config():
    response = flask.make_response(json.dumps(shared_context.app_context.to_json()))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    # response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.route('/api/last-seen.jpg' , methods = ['GET'])
def get_image():
    last_seen = shared_context.last_seen

    frame, circle = last_seen.get_frame_and_circle()

    frame = cv2.cvtColor(frame, cv2.COLOR_HSV2RGB)

    if circle:
        x, y, radius = circle
        cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 0), 5)

    _, buffer = cv2.imencode('.jpg', frame)
    response = flask.make_response(buffer.tobytes())
    response.headers['Content-Type'] = 'image/jpeg'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    # response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.route('/api/config-update' , methods = ['PUT'])
def set_config():
    json_dict: typing.Union[dict, list] = flask.request.json
    updates = []
    if type(json_dict) == list:
        updates = [app_contexts.AppContextUpdate.from_json(update) for update in json_dict]
    elif type(json_dict) == dict:
        updates = [app_contexts.AppContextUpdate.from_json(json_dict)]
    else:
        raise Exception(f'Unexpected type {type(json_dict)}')

    for update in updates:
        shared_context.app_context.update(update)

    app_contexts.save_app_context(shared_context.config_file, shared_context.app_context)

    response = flask.make_response(json.dumps(shared_context.app_context.to_json()))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    # response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.route("/<path:path>")
def static_proxy(path):
    return app.send_static_file(path)


def start_server():
    app.run(host='0.0.0.0', port=5000)


if __name__ == "__main__":
    start_server()
