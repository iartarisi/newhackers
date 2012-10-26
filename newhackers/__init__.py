from newhackers.utils import make_json_app

app = make_json_app(__name__)

if __name__ == "__main__":
    app.run(debug=True)
