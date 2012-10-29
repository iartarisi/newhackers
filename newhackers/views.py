# -*- coding: utf-8 -*-
# This file is part of newhackers.
# Copyright (c) 2012 Ionuț Arțăriși

# cuZmeură is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.

# cuZmeură is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with cuZmeură. If not, see <http://www.gnu.org/licenses/>.

import logging

from flask import abort, jsonify, request

from newhackers import app, auth, items, exceptions, votes


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
        resp = items.get_stories(page)
    except exceptions.NotFound:
        abort(404)

    return app.response_class(resp, mimetype='application/json')


@app.route("/comments/<int:item_id>")
def get_comments(item_id):
    """Return story with its comments"""
    try:
        resp = items.get_comments(item_id)
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
    except KeyError:
        abort(401)
    except exceptions.ClientError as e:
        resp = jsonify(error=e.message)
        resp.status_code = 403
        return resp
    except exceptions.ServerError as e:
        resp = jsonify(error=e.message)
        resp.status_code = 500
        return resp

    return jsonify(token=token)


@app.route("/vote", methods=["POST"])
def vote():
    """Vote on an HN item"""
    try:
        success = votes.vote(request.form['token'], request.form['direction'],
                             request.form['item'])
    except KeyError:
        abort(401)
    except exceptions.ClientError as e:
        resp = jsonify(error=e.message)
        resp.status_code = 403
        return resp
    except exceptions.ServerError as e:
        resp = jsonify(error=e.message)
        resp.status_code = 500
        return resp

    return jsonify(vote='Success' if success else 'Fail')
