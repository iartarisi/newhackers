import re

from flask import Flask, jsonify
from werkzeug.exceptions import default_exceptions, HTTPException


def make_json_app(*args, **kwargs):
    """JSONify all error responses"""
    def make_json_error(ex):
        response = jsonify(error=str(ex))
        response.status_code = (ex.code if isinstance(ex, HTTPException)
                                else 500)
        return response

    app = Flask(*args, **kwargs)
    for code in default_exceptions:
        app.error_handler_spec[None][code] = make_json_error

    return app
