import logging

from flask import abort, jsonify, request

from newhackers import app, exceptions, token, stories


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
        resp = stories.get_stories(page)
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
        tok = token.get_token(request.form['user'], request.form['password'])
        return jsonify(token=tok)
    except exceptions.ClientError as e:
        resp = jsonify(error=e.message)
        resp.status_code = 403
        return resp
    except exceptions.ServerError as e:
        resp = jsonify(error=e.message)
        resp.status_code = 500
        return resp
