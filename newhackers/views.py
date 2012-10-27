import logging

from flask import abort, jsonify, request

from newhackers import app, auth, controller, exceptions


@app.route("/stories")
@app.route("/stories/")
@app.route("/ask")
@app.route("/ask/")
@app.route("/ask/<page>")
@app.route("/stories/<page>")
def get_stories(page=None):
    """Return a page of HN stories"""
    if request.url_rule.rule in ('/ask', '/ask/'):
        page = 'ask'
    elif request.url_rule.rule in ('/stories/', '/stories'):
        page = ''

    try:
        resp = controller.get_stories(page)
    except exceptions.NotFound:
        abort(404)

    return app.response_class(resp, mimetype='application/json')


@app.route("/comments/<int:item_id>")
def get_comments(item_id):
    """Return story with its comments"""
    try:
        resp = controller.get_comments(item_id)
    except exceptions.NotFound:
        abort(404)

    return app.response_class(resp, mimetype='application/json')
    

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
        token = auth.get_token(request.form['user'], request.form['password'])
        return jsonify(token=token)
    except exceptions.ClientError as e:
        resp = jsonify(error=e.message)
        resp.status_code = 403
        return resp
    except exceptions.ServerError as e:
        resp = jsonify(error=e.message)
        resp.status_code = 500
        return resp
