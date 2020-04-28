from flask import Flask, render_template, request
import search
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html') # just the static HTML

@app.route('/handle_form', methods=['POST'])
def handle_the_form():

    name = request.form["name"]
    order = request.form["order"]
    way = request.form["way"]
    test(name)
    return render_template('response.html', 
        name=name)


def test(name):
    CACHE_DICT = search.open_cache()
    baseurl = "https://store.steampowered.com/search/?term="
    game_dict = search.get_search_results(baseurl, name)
    details_dict = search.get_detail_results(game_dict)
    search.creat_db()
    search.load_games(game_dict)
    search.load_details(details_dict)

if __name__ == "__main__":
    app.run(debug=True)