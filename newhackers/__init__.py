import logging

from newhackers.utils import make_json_app


logging.basicConfig(filename="/tmp/newhackers.log", level=logging.INFO)

app = make_json_app(__name__)

import newhackers.views


if __name__ == "__main__":
    app.run(debug=True)
