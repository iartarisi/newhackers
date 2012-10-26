from flask import abort, jsonify

from newhackers import backend
from newhackers.utils import make_json_app


app = make_json_app(__name__)

@app.route("/stories")
@app.route("/stories/")
@app.route("/stories/<page>")
def stories(page=None):
    """Return a page of HN stories"""
    stories = backend.get_stories(page)

    if not stories:
        abort(404)
    return jsonify(stories=stories)

if __name__ == "__main__":
    app.run(debug=True)
