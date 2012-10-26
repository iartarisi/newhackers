import logging

from flask import abort, jsonify, request

from newhackers import backend
from newhackers.utils import make_json_app


app = make_json_app(__name__)
logging.basicConfig(filename="/tmp/newhackers.log", level=logging.INFO)


@app.route("/stories")
@app.route("/stories/")
@app.route("/stories/<page>")
def stories(page=None):
    """Return a page of HN stories"""
    stories = backend.get_stories(page)

    if not stories:
        abort(404)
    return jsonify(stories=stories)


@app.route("/get_token", methods=["POST"])
def get_token():
    """Login on HN and return a user token

    :user: username string
    :password: password string

    Returns a user `token` string which needs to be given as a parameter
    for API methods which require a user to be signed in such as
    commenting or voting.

    Note: your user/password are not stored on the server, but they are
    transmitted through it.

    """
    try:
        token = backend.get_token(request.form['user'], request.form['password'])
        return jsonify(token=token)
    except backend.ClientError as e:
        resp = jsonify(error=e.message)
        resp.status_code = 403
        return resp
    except backend.ServerError as e:
        resp = jsonify(error=e.message)
        resp.status_code = 500
        return resp


if __name__ == "__main__":
    app.run(debug=True)
